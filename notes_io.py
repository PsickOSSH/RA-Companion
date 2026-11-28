"""Personal notes: export, import and merge (no Tk import: testable anywhere). Notes are a dict {achievement ID (text): note}.
The file format is a plain JSON object, the same as the Android app."""

import json
import re

_ID = re.compile(r"[0-9]+")            # an achievement ID: anything else is not a note


def clean(notes):
    """The notes of the dictionary `notes` (empty when it is not one), without the entries that are not about an achievement
    (added by an import of another kind of file in older versions)."""
    if not isinstance(notes, dict):
        return {}
    return {str(k): v for k, v in notes.items() if _ID.fullmatch(str(k))}


def entries(notes, titles=None, length=60):
    """The notes as a list to choose from: [(ID, "title: beginning of the note")]. `titles` ({ID: achievement title}) holds
    the achievements known now (they come first); the others are shown with their ID."""
    titles = titles or {}
    out = []
    for ident, text in clean(notes).items():
        text = " ".join(str(text).split())
        if not text:
            continue
        short = text if len(text) <= length else text[:length].rstrip() + "…"
        known = titles.get(ident)
        out.append(((not known, (known or "").lower(), int(ident)), (ident, f"{known or '#' + ident} : {short}")))
    return [entry for _order, entry in sorted(out)]


def export_text(notes):
    """JSON text of the non-empty notes, sorted by achievement ID."""
    kept = {k: str(v).strip() for k, v in clean(notes).items() if str(v).strip()}
    return json.dumps(dict(sorted(kept.items(), key=lambda kv: int(kv[0]))), ensure_ascii=False, indent=2)


def parse_notes(text):
    """Read an exported file. Raises ValueError when it is not a notes file."""
    data = json.loads(text)
    if isinstance(data, dict) and "format" in data:                 # another file of the app (settings, backup...)
        raise ValueError("not a notes file")
    if isinstance(data, dict) and isinstance(data.get("notes"), dict):
        data = data["notes"]
    if not isinstance(data, dict):
        raise ValueError("not a notes file")
    notes = {k: str(v).strip() for k, v in clean(data).items() if isinstance(v, (str, int, float)) and str(v).strip()}
    if data and not notes:
        raise ValueError("no note found")
    return notes


def merge(current, imported):
    """Add the imported notes to `current` (modified in place). Returns (added, merged, unchanged).
    A note that already exists with another text is kept and the imported text is appended below it."""
    added = merged = unchanged = 0
    for key, text in imported.items():
        mine = current.get(key, "").strip()
        if not mine:
            current[key] = text
            added += 1
        elif text in mine:
            unchanged += 1
        else:
            current[key] = mine + "\n\n" + text
            merged += 1
    return added, merged, unchanged
