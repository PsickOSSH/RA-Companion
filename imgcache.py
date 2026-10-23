"""Disk cache for the pictures of the RetroAchievements media server (badges, game icons, avatars) and the small logos.

Badges and game icons never change, so they are kept for good: each one is downloaded only once, even after the app is
closed and reopened. Anything else (avatars, logos) is downloaded again after a week. A picture that cannot be
downloaded is not requested again for two minutes, so a missing badge does not hit the server at every scroll.
"""

import hashlib
import logging
import os
import re
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from ra_api import http_get

Logger = logging.getLogger("imgcache")

FOREVER = ("/Badge/", "/Images/")
MAX_AGE = 7 * 24 * 3600
RETRY_AFTER = 120

_POOL = ThreadPoolExecutor(max_workers=4)
_LOCK = threading.Lock()
_WAITING = {}
_FAILED = {}


def path_for(folder, url):
    """Local file of `url` in `folder` (the name is a hash of the address, the extension is kept)."""
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
    if not re.fullmatch(r"\.[a-z0-9]{2,5}", ext):
        ext = ".png"
    return os.path.join(folder, hashlib.sha1(url.encode("utf-8")).hexdigest()[:20] + ext)


def _fresh(path, url):
    try:
        if os.path.getsize(path) == 0:
            return False
        age = time.time() - os.path.getmtime(path)
    except OSError:
        return False
    return age < MAX_AGE or any(part in url for part in FOREVER)


def cached_path(folder, url):
    """Path of the saved picture, or None when it is missing or too old."""
    path = path_for(folder, url)
    return path if _fresh(path, url) else None


def download(folder, url):
    """Download `url` into the cache and return the file path. Raises an exception when the download fails."""
    data = http_get(url, binary=True)
    if not data:
        raise ValueError("empty picture")
    os.makedirs(folder, exist_ok=True)
    path = path_for(folder, url)
    tmp = f"{path}.{threading.get_ident()}.part"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)
    return path


def get_bytes(folder, url):
    """Content of the picture (from the disk if possible, else downloaded and saved), or None. Blocking call."""
    path = cached_path(folder, url)
    try:
        if path is None:
            path = download(folder, url)
    except Exception as exc:
        Logger.warning("imgcache: download failed for %s in %s: %r", url, folder, exc)
        path = path_for(folder, url)
    try:
        with open(path, "rb") as f:
            return f.read() or None
    except OSError as exc:
        Logger.warning("imgcache: cannot read %s: %r", path, exc)
        return None


def fetch_async(folder, url, done):
    """Download in the background, then call `done(path)` from the worker thread. The same address is downloaded once."""
    if time.time() - _FAILED.get(url, 0) < RETRY_AFTER:
        return
    with _LOCK:
        if url in _WAITING:
            _WAITING[url].append(done)
            return
        _WAITING[url] = [done]

    def job():
        path = None
        try:
            path = download(folder, url)
        except Exception as exc:
            Logger.warning("imgcache: async download failed for %s in %s: %r", url, folder, exc)
            _FAILED[url] = time.time()
        with _LOCK:
            callbacks = _WAITING.pop(url, [])
        if path:
            for callback in callbacks:
                try:
                    callback(path)
                except Exception:
                    Logger.exception("imgcache: callback failed")

    _POOL.submit(job)