"""Translation of descriptions and comments (no Kivy import: testable on a PC).

Several free endpoints are tried one after the other, the answers are cached in memory and in a JSON file, and a text that
failed is retried only after a pause (or when the user presses the translation button again). Errors are kept in
`last_error` so that the interface can show them instead of failing silently."""

import json
import os
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

try:
    import certifi
    _CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _CTX = None

USER_AGENT = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
RETRY_AFTER = 60          # seconds before a failed text is tried again
MAX_CACHED = 6000         # entries kept on disk


class TranslateError(Exception):
    """Every endpoint failed; the message says why."""


def get_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json,text/plain,*/*"})
    kw = {"timeout": timeout}
    if _CTX is not None:
        kw["context"] = _CTX
    with urllib.request.urlopen(req, **kw) as r:
        return json.loads(r.read().decode("utf-8"))


def _google_gtx(text, lang):
    data = get_json("https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode(
        {"client": "gtx", "sl": "auto", "tl": lang, "dt": "t", "q": text[:4500]}))
    return "".join(part[0] for part in data[0] if part and part[0])


def _google_chrome(text, lang):
    data = get_json("https://clients5.google.com/translate_a/t?" + urllib.parse.urlencode(
        {"client": "dict-chrome-ex", "sl": "auto", "tl": lang, "q": text[:4500]}))
    if isinstance(data, dict):                                   # {"sentences": [{"trans": ...}, ...]}
        return "".join(s.get("trans", "") for s in data.get("sentences", []))
    if isinstance(data, list) and data:                          # [["translation", "en"]] or ["translation"]
        first = data[0]
        return first[0] if isinstance(first, list) else str(first)
    return ""


def _mymemory(text, lang):
    data = get_json("https://api.mymemory.translated.net/get?" + urllib.parse.urlencode(
        {"q": text[:450], "langpair": f"Autodetect|{lang}"}))
    if str(data.get("responseStatus")) != "200":
        raise TranslateError(str(data.get("responseDetails") or data.get("responseStatus")))
    return (data.get("responseData") or {}).get("translatedText", "")


BACKENDS = [("google", _google_gtx), ("google-chrome", _google_chrome), ("mymemory", _mymemory)]


def _describe(e):
    if isinstance(e, urllib.error.HTTPError):
        return f"HTTP {e.code}"
    if isinstance(e, urllib.error.URLError):
        return f"network ({e.reason})"
    return f"{e.__class__.__name__}: {e}"[:80]


class Translator:
    def __init__(self, path=None):
        self.cache = {}                 # (lang, text) -> translation
        self.failed = {}                # (lang, text) -> time of the last failure
        self.last_error = ""
        self.path = None
        self._lock = threading.Lock()
        self._good = 0                  # index of the endpoint that worked last
        if path:
            self.set_cache_file(path)

    # ---- cache -----------------------------------------------------------
    def set_cache_file(self, path):
        self.path = path
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            for lang, items in data.items():
                for text, out in items.items():
                    self.cache[(lang, text)] = out
        except Exception:
            pass

    def save(self):
        if not self.path:
            return
        with self._lock:
            items = list(self.cache.items())[-MAX_CACHED:]
            data = {}
            for (lang, text), out in items:
                data.setdefault(lang, {})[text] = out
            try:
                tmp = self.path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
                os.replace(tmp, self.path)
            except Exception:
                pass

    def cached(self, lang, text):
        """The translation when it is known, the original text otherwise."""
        return self.cache.get((lang, text), text)

    def reset_failures(self):
        self.failed.clear()
        self.last_error = ""

    def pending(self, lang, text):
        """True when `text` still has to be translated (not cached and not failed recently)."""
        if not text or not text.strip() or (lang, text) in self.cache:
            return False
        return time.time() - self.failed.get((lang, text), 0) > RETRY_AFTER

    # ---- translation -----------------------------------------------------
    def translate(self, text, lang):
        if (lang, text) in self.cache:
            return self.cache[(lang, text)]
        errors = []
        n = len(BACKENDS)
        for k in range(n):
            idx = (self._good + k) % n
            name, fn = BACKENDS[idx]
            try:
                out = (fn(text, lang) or "").strip()
                if not out:
                    raise TranslateError("empty answer")
                self._good = idx
                self.cache[(lang, text)] = out
                return out
            except Exception as e:
                errors.append(f"{name}: {_describe(e)}")
                if isinstance(e, urllib.error.HTTPError) and e.code in (429, 503):
                    time.sleep(0.5)
        self.failed[(lang, text)] = time.time()
        raise TranslateError("; ".join(errors))

    def translate_many(self, texts, lang, workers=3):
        """Translate every pending text. Returns (done, failed); `last_error` holds the first error message."""
        todo = [t for t in dict.fromkeys(texts) if self.pending(lang, t)]
        results = {"done": 0, "failed": 0, "error": ""}

        def one(t):
            try:
                self.translate(t, lang)
                results["done"] += 1
            except Exception as e:
                results["failed"] += 1
                results["error"] = results["error"] or str(e)

        if todo:
            with ThreadPoolExecutor(workers) as ex:
                list(ex.map(one, todo))
            self.last_error = results["error"] if results["failed"] and not results["done"] else ""
            self.save()
        return results["done"], results["failed"]
