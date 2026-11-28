"""Export and import of everything in one file: settings, theme, imported skins and personal notes (Windows, Linux, Android
and iOS read each other's files). It is built from the other formats (settings_io.py, userskins.py, notes_io.py) and is
checked the same way when it is imported. It holds the account key and the translation keys in plain text."""

import json
import re

import notes_io
import settings_io
import userskins

FORMAT = "ra-companion-backup"
MAX_FILE = 5_000_000        # characters


def export_text(cfg, notes, skins):
    """The text of a backup file: configuration `cfg`, personal `notes` {ID: text} and imported `skins` (their variables)."""
    kept = {ident: str(text).strip() for ident, text in notes_io.clean(notes).items() if str(text).strip()}
    return json.dumps({"format": FORMAT, "version": 1, "settings": settings_io.valid(cfg),
                       "skin": str(cfg.get("skin", "default")), "skins": [userskins.check(v) for v in skins], "notes": kept},
                      ensure_ascii=False, indent=2) + "\n"


def parse(text):
    """The content of a backup file: {"settings", "skin" (identifier or None), "skins" [variables], "notes" {ID: text}}.
    Only what is valid is kept. ValueError when the text is not a backup file."""
    text = str(text).lstrip("﻿")
    if len(text) > MAX_FILE:
        raise ValueError("file too big")
    try:
        data = json.loads(text)
    except RecursionError as e:
        raise ValueError("not a backup file") from e
    if not isinstance(data, dict) or data.get("format") != FORMAT:
        raise ValueError("not a backup file")
    settings = data.get("settings")
    skins = data.get("skins")
    skin = data.get("skin")
    checked = [userskins.check(v) for v in skins if isinstance(v, dict)] if isinstance(skins, list) else []
    return {
        "settings": settings_io.valid(settings) if isinstance(settings, dict) else {},
        "skin": skin if isinstance(skin, str) and re.fullmatch(r"[a-z0-9_]{1,80}", skin) else None,
        "skins": [v for v in checked if any(key in v for key in userskins.COLOR_KEYS)],
        "notes": {ident: note.strip() for ident, note in notes_io.clean(data.get("notes")).items()
                  if isinstance(note, str) and note.strip()},
    }


def install_skins(skins, folder, default_name):
    """Save the skins of a backup into `folder` (a skin with the same name is replaced). Returns their identifiers.
    OSError when one cannot be saved."""
    return [userskins.install(userskins.export_text(values), folder, values.get("NAME") or default_name)[0]
            for values in skins]
