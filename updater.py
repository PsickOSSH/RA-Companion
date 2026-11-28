"""Update check and patch notes: reads the GitHub releases of the project (no GUI import: testable on a PC)."""

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


# ---- patch notes: the descriptions of the releases, as plain text --------------------------------------------------
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_TAG = re.compile(r"</?(?:a|b|br|details|div|em|i|img|p|strong|sub|summary|sup)\b[^>]*>", re.I)
_CHANGELOG = re.compile(r"(?:\*\*|__)?\s*full changelog\s*(?:\*\*|__)?\s*:", re.I)
_COMPARE = re.compile(r"https://github\.com/\S+/(?:compare|commits)/\S+")
_INLINE = ((re.compile(r"!\[[^\]]*\]\([^)]*\)"), ""),                          # picture: removed
           (re.compile(r"\[([^\]]*)\]\([^)]*\)"), r"\1"),                      # [text](address): the text
           (re.compile(r"(\*\*|__)(?=\S)(.+?)(?<=\S)\1"), r"\2"),              # bold
           (re.compile(r"(?<![\w*])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![\w*])"), r"\1"),    # italic
           (re.compile(r"`([^`]*)`"), r"\1"))                                  # code


def note_blocks(body):
    """The description of a release (Markdown) as a list of (kind, text) with kind 'title', 'bullet' or 'text'. The marks
    of Markdown are removed, and so is the "Full Changelog" link (it is of no use in the app)."""
    blocks = []
    for line in _TAG.sub("", _COMMENT.sub("", str(body or ""))).splitlines():
        line = line.strip()
        if not line or line.startswith("```") or re.fullmatch(r"[-*_=]{3,}", line):
            continue
        if _CHANGELOG.match(line) or _COMPARE.fullmatch(line):
            continue
        kind = "text"
        heading = re.match(r"#{1,6}\s+", line)
        item = re.match(r"(?:[-*+]|\d{1,2}\.)\s+", line)
        if heading:
            kind, line = "title", line[heading.end():]
        elif item:
            kind, line = "bullet", line[item.end():]
        else:
            line = re.sub(r"^(?:>\s*)+", "", line)                       # quote
        for pattern, replacement in _INLINE:
            line = pattern.sub(replacement, line)
        if line.strip():
            blocks.append((kind, line.strip()))
    return blocks


def release_notes(repo, fetch=None):
    """The patch notes of the published releases, the newest version first:
    [{'version': '2.6', 'date': '2026-12-01', 'blocks': [(kind, text)]}] (see note_blocks)."""
    releases = (fetch or get_json)(API.format(repo=repo))
    if not isinstance(releases, list):
        raise ValueError("unexpected answer from GitHub")
    notes = []
    for rel in releases:
        if not isinstance(rel, dict) or rel.get("draft"):
            continue
        label = str(rel.get("tag_name") or rel.get("name") or "").lstrip("vV")
        if label:
            notes.append({"version": label, "date": str(rel.get("published_at") or "")[:10],
                          "blocks": note_blocks(rel.get("body"))})
    return sorted(notes, key=lambda note: parse_version(note["version"]), reverse=True)


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
