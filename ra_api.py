"""Network helpers: RetroAchievements Web API, plain HTTP downloads and content translation."""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from appinfo import __version__
from config import API

try:
    import certifi
    import ssl
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CONTEXT = None


TRANSLATION_CACHE = {}


def http_get(url, binary=False):
    """GET `url` and return the decoded JSON, or the raw bytes when `binary` is true."""
    req = urllib.request.Request(url, headers={"User-Agent": "RACompanion/" + __version__})
    kwargs = {"timeout": 25}
    if SSL_CONTEXT:
        kwargs["context"] = SSL_CONTEXT
    with urllib.request.urlopen(req, **kwargs) as r:
        b = r.read()
    return b if binary else json.loads(b.decode("utf-8"))


RETRY_DELAYS = (1.0, 3.0)                 # pauses (seconds) before the 1st and 2nd retry
RETRY_MAX_WAIT = 10.0                     # longest pause accepted from a Retry-After header
RETRY_CODES = (429, 500, 502, 503, 504)   # temporary server answers worth a retry


def _retry_wait(error, default):
    """Seconds to wait before retrying after `error`, or None when the error is final (bad key, 404, bad JSON...)."""
    if isinstance(error, urllib.error.HTTPError):
        if error.code not in RETRY_CODES:
            return None
        try:
            asked = float(error.headers.get("Retry-After", ""))
            return min(max(asked, 0.0), RETRY_MAX_WAIT)
        except (TypeError, ValueError, AttributeError):
            return default
    if isinstance(error, (urllib.error.URLError, TimeoutError, ConnectionError)):
        return default                    # temporary network hiccup
    return None


def call_api(endpoint, key, **p):
    """Call a RetroAchievements Web API endpoint; empty parameters are dropped and the API key is added as `y`.

    Temporary failures (HTTP 429 / 5xx, timeouts, network errors) are retried twice with a short pause. This blocks,
    so call it from a background thread (as the whole app does). The last error is raised if every attempt fails."""
    p = {k: v for k, v in p.items() if v != ""}
    p["y"] = key
    url = API + endpoint + "?" + urllib.parse.urlencode(p)
    for default in RETRY_DELAYS:
        try:
            return http_get(url)
        except Exception as e:
            wait = _retry_wait(e, default)
            if wait is None:
                raise
            time.sleep(wait)
    return http_get(url)


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
