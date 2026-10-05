"""Network helpers: RetroAchievements Web API, plain HTTP downloads and content translation."""

import json
import urllib.parse
import urllib.request

from config import API


TRANSLATION_CACHE = {}


def http_get(url, binary=False):
    """GET `url` and return the decoded JSON, or the raw bytes when `binary` is true."""
    req = urllib.request.Request(url, headers={"User-Agent": "RACompanion/2.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        b = r.read()
    return b if binary else json.loads(b.decode("utf-8"))


def call_api(endpoint, key, **p):
    """Call a RetroAchievements Web API endpoint; empty parameters are dropped and the API key is added as `y`."""
    p = {k: v for k, v in p.items() if v != ""}
    p["y"] = key
    return http_get(API + endpoint + "?" + urllib.parse.urlencode(p))


def translate(text, lang):
    """Translate `text` into `lang` through the public Google Translate endpoint (results are cached in memory)."""
    k = (lang, text)
    if k in TRANSLATION_CACHE:
        return TRANSLATION_CACHE[k]
    if not text or not text.strip():
        return text
    url = "https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode({"client": "gtx", "sl": "auto",
            "tl": lang, "dt": "t", "q": text[:4500]})
    d = http_get(url)
    out = "".join((part[0] for part in d[0] if part and part[0]))
    TRANSLATION_CACHE[k] = out
    return out
