"""Personal notes: export, import and merge (no Tk import: testable anywhere). Notes are a dict {achievement ID (text): note}.
The file format is a plain JSON object, the same as the Android app."""

import json


def export_text(notes):
    """JSON text of the non-empty notes, sorted by achievement ID."""
    clean = {str(k): str(v).strip() for k, v in notes.items() if str(v).strip()}
    return json.dumps(dict(sorted(clean.items(), key=lambda kv: (not kv[0].isdigit(), int(kv[0]) if kv[0].isdigit() else 0, kv[0]))),
                      ensure_ascii=False, indent=2)


def parse_notes(text):
    """Read an exported file. Raises ValueError when it is not a notes file."""
    data = json.loads(text)
    if isinstance(data, dict) and isinstance(data.get("notes"), dict):
        data = data["notes"]
    if not isinstance(data, dict):
        raise ValueError("not a notes file")
    notes = {str(k): str(v).strip() for k, v in data.items() if isinstance(v, (str, int, float)) and str(v).strip()}
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
