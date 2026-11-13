"""Translation of descriptions and comments (no Kivy import: testable on a PC).

Several services are tried one after the other: DeepL and LibreTranslate when the user gave a key / server address in the
settings, then the free endpoints (Google, MyMemory). The setting `tr_service` puts one of them first. The answers are
cached in memory and in a JSON file, and a text that failed is retried only after a pause (or when the user presses the
translation button again). Errors are kept in `last_error` so that the interface can show them instead of failing silently."""

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
SERVICES = ["auto", "deepl", "libretranslate", "google", "mymemory"]     # values of the setting `tr_service`
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


def post_json(url, payload, headers=None, timeout=15, insecure=False):
    """POST `payload` as JSON and return the decoded JSON answer.

    `insecure=True` accepts a certificate that is not valid for the address (own server with a self-signed certificate or
    reached through another name); it is only used for the LibreTranslate server chosen by the user."""
    h = {"User-Agent": USER_AGENT, "Accept": "application/json", "Content-Type": "application/json"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=h, method="POST")
    kw = {"timeout": timeout}
    if insecure:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kw["context"] = ctx
    elif _CTX is not None:
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


DEEPL_TARGETS = {"en": "EN-US", "pt": "PT-PT", "zh-CN": "ZH"}         # DeepL wants EN-US / PT-PT; others: the code in capitals
LIBRE_TARGETS = {"zh-CN": "zh-Hans"}


def _deepl(text, lang, key):
    """DeepL API (the free keys end with ':fx' and use another server than the paid ones)."""
    host = "api-free.deepl.com" if key.endswith(":fx") else "api.deepl.com"
    data = post_json(f"https://{host}/v2/translate", {"text": [text[:4500]], "target_lang": DEEPL_TARGETS.get(lang, lang.upper())},
                     {"Authorization": "DeepL-Auth-Key " + key})
    return "".join(t.get("text", "") for t in data.get("translations", []))


def _libretranslate(text, lang, url, key, insecure=False):
    """LibreTranslate server (own server, or a hosted one with an API key)."""
    url = url.strip().rstrip("/")
    if "://" not in url:
        url = "https://" + url
    payload = {"q": text[:4500], "source": "auto", "target": LIBRE_TARGETS.get(lang, lang), "format": "text"}
    if key:
        payload["api_key"] = key
    data = post_json(url + "/translate", payload, **({"insecure": True} if insecure else {}))
    if "translatedText" not in data:
        raise TranslateError(str(data.get("error") or "no translation"))
    return data["translatedText"]


# Free endpoints, always available (the order is the order of the tries)
BACKENDS = [("google", _google_gtx), ("google-chrome", _google_chrome), ("mymemory", _mymemory)]


def _describe(e):
    if isinstance(e, urllib.error.HTTPError):
        if e.code in (301, 302, 307, 308):
            return f"HTTP {e.code} (redirection: try the address with https://)"
        return f"HTTP {e.code}"
    if isinstance(e, urllib.error.URLError):
        if isinstance(e.reason, ssl.SSLCertVerificationError):
            return "invalid certificate: " + str(getattr(e.reason, "verify_message", "") or e.reason)[:90]
        return f"network ({e.reason})"
    return f"{e.__class__.__name__}: {e}"[:80]


class Translator:
    def __init__(self, path=None):
        self.cache = {}                 # (lang, text) -> translation
        self.failed = {}                # (lang, text) -> time of the last failure
        self.last_error = ""
        self.path = None
        self._lock = threading.Lock()
        self._good = 0                  # index of the endpoint that worked last (automatic mode)
        self.last_used = ""             # name of the service that gave the last translation
        self.configure()
        if path:
            self.set_cache_file(path)

    # ---- settings --------------------------------------------------------
    def configure(self, service="auto", deepl_key="", libre_url="", libre_key="", libre_insecure=False):
        """Choose the preferred service and give the keys. A service without key / address is simply skipped.
        `libre_insecure` accepts an invalid certificate for the LibreTranslate server."""
        self.service = service if service in SERVICES else "auto"
        self.deepl_key = str(deepl_key or "").strip()
        self.libre_url = str(libre_url or "").strip()
        self.libre_key = str(libre_key or "").strip()
        self.libre_insecure = bool(libre_insecure)
        self._good = 0

    def configure_from(self, cfg):
        """Same as configure(), reading the settings dictionary of the app."""
        self.configure(cfg.get("tr_service", "auto"), cfg.get("deepl_key", ""), cfg.get("libre_url", ""),
                       cfg.get("libre_key", ""), cfg.get("libre_insecure", False))

    def chain(self):
        """The services to try, in order: [(name, function(text, lang))]."""
        items = []
        if self.deepl_key:
            items.append(("deepl", lambda t, l, k=self.deepl_key: _deepl(t, l, k)))
        if self.libre_url:
            items.append(("libretranslate", lambda t, l, u=self.libre_url, k=self.libre_key, i=self.libre_insecure:
                          _libretranslate(t, l, u, k, i)))
        items += BACKENDS
        if self.service != "auto":                                   # the preferred service goes first
            first = [it for it in items if it[0].split("-")[0] == self.service]
            items = first + [it for it in items if it not in first]
        return items

    def test(self, text="Hello world", lang="fr"):
        """Try every service of the chain on its own (the cache is not used): [(name, ok, translation or error)]."""
        def one(item):
            name, fn = item
            try:
                out = (fn(text, lang) or "").strip()
                if not out:
                    raise TranslateError("empty answer")
                return name, True, out
            except Exception as e:
                return name, False, _describe(e)
        chain = self.chain()
        with ThreadPoolExecutor(len(chain)) as ex:
            return list(ex.map(one, chain))

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
        chain = self.chain()
        n = len(chain)
        start = self._good % n if self.service == "auto" else 0       # automatic mode starts with the last good one
        for k in range(n):
            idx = (start + k) % n
            name, fn = chain[idx]
            try:
                out = (fn(text, lang) or "").strip()
                if not out:
                    raise TranslateError("empty answer")
                if self.service == "auto":
                    self._good = idx
                self.last_used = name
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
