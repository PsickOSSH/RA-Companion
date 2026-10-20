"""Update check: looks for the newest .apk attached to the GitHub releases of the project (no Kivy import: testable on a PC)."""

import json
import re
import ssl
import urllib.error
import urllib.request

try:
    import certifi
    _CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _CTX = None

API = "https://api.github.com/repos/{repo}/releases?per_page=30"


def parse_version(text):
    """'v1.2.3' -> (1, 2, 3); '1.10' -> (1, 10); anything without digits -> (0,). Tuples compare correctly (1.10 > 1.9)."""
    numbers = re.findall(r"\d+", str(text or "").split("-")[0])
    return tuple(int(n) for n in numbers[:4]) or (0,)


def repo_from_url(url):
    """'https://github.com/owner/name(.git)' -> 'owner/name' (None when it is not a GitHub address)."""
    m = re.search(r"github\.com/([^/\s]+)/([^/\s#?]+)", str(url or ""))
    return f"{m.group(1)}/{re.sub(r'[.]git$', '', m.group(2))}" if m else None


def get_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "RACompanion-Android"})
    kw = {"timeout": timeout}
    if _CTX is not None:
        kw["context"] = _CTX
    with urllib.request.urlopen(req, **kw) as r:
        return json.loads(r.read().decode("utf-8"))


def pick_apk(release, ext=".apk"):
    """The first .apk asset of a release, or None."""
    for asset in release.get("assets") or []:
        if str(asset.get("name", "")).lower().endswith(ext) and asset.get("browser_download_url"):
            return asset
    return None


def check(repo, current, fetch=None, ext=".apk"):
    """Compare the installed version with the newest release that has an .apk.
    Returns {'status': 'newer' | 'uptodate' | 'noapk', 'version', 'url', 'size'}."""
    releases = (fetch or get_json)(API.format(repo=repo))
    if not isinstance(releases, list):
        raise ValueError("unexpected answer from GitHub")
    best = None
    for rel in releases:
        if not isinstance(rel, dict) or rel.get("draft"):
            continue
        apk = pick_apk(rel, ext)
        if apk is None:
            continue
        number = parse_version(rel.get("tag_name") or rel.get("name"))
        if best is None or number > best[0]:
            best = (number, rel, apk)
    if best is None:
        return {"status": "noapk"}
    number, rel, apk = best
    label = str(rel.get("tag_name") or rel.get("name") or "").lstrip("vV")
    return {"status": "newer" if number > parse_version(current) else "uptodate",
            "version": label, "url": apk["browser_download_url"], "size": apk.get("size")}


def describe(e):
    """Short readable text for a network error."""
    if isinstance(e, urllib.error.HTTPError):
        if e.code == 403:
            return "GitHub limit reached, try again later"
        if e.code == 404:
            return "repository not found (is it private?)"
        return f"HTTP {e.code}"
    if isinstance(e, (urllib.error.URLError, TimeoutError, OSError)):
        return "no connection"
    return (str(e) or e.__class__.__name__)[:80]
