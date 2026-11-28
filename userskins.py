"""Skins imported by the user (Settings -> Import a skin), for every version of the app.

A skin file is a Python file, but an imported one is only READ, never executed: it could otherwise run any program and read
the account key. The `NAME = value` lines whose value is a plain text or number are kept, checked one by one, and saved as
a data file (JSON) in a folder of the user. Everything else of the file is ignored."""

import ast
import hashlib
import json
import os
import re
import unicodedata

PREFIX = "user_"                    # identifier of an imported skin: "user_<file name>"
MAX_SIZE = 100_000                  # characters of one skin: a skin file is a few thousand
MAX_FILE = 1_000_000                # characters of a file that holds several skins
MARKER = "# === RA Companion skin ==="           # line before each skin of such a file
COLOR_KEYS = ("BACKGROUND", "CARD", "CARD_ALT", "CARD_LOCKED", "CARD_LOCKED_HOVER", "TEXT", "TEXT_MUTED", "TEXT_ON_ACCENT",
              "ACCENT", "SUCCESS", "INFO", "WARNING", "DANGER", "CONTROL_HOVER", "SCROLL_THUMB", "BAR_TRACK_ALT", "HOVER_TINT",
              "TOOLTIP_BG", "TOOLTIP_TEXT", "TOOLTIP_BORDER")
TEXT_KEYS = ("NAME", "AUTHOR", "FONT", "SYMBOL_FONT")
NUMBER_KEYS = {"HOVER_STRENGTH": (0, 1), "RADIUS_PANEL": (0, 40), "RADIUS_CARD": (0, 40), "RADIUS_BUTTON": (0, 40),
               "RADIUS_BUTTON_LARGE": (0, 40), "RADIUS_TOAST": (0, 40)}
_COLOR = re.compile(r"#[0-9a-fA-F]{6}")
_ID = re.compile(PREFIX + r"[a-z0-9_]{1,60}")


def check(values):
    """The valid variables of `values` ({name: value}); unknown names and wrong values are left out."""
    out = {}
    for key, value in values.items():
        if key in COLOR_KEYS:
            if isinstance(value, str) and _COLOR.fullmatch(value):
                out[key] = value
        elif key in TEXT_KEYS:
            if isinstance(value, str) and value.strip():
                out[key] = " ".join(value.split())[:60]
        elif key in NUMBER_KEYS:
            low, high = NUMBER_KEYS[key]
            if isinstance(value, (int, float)) and not isinstance(value, bool) and low <= value <= high:
                out[key] = value if key == "HOVER_STRENGTH" else int(value)
    return out


def parse(text):
    """Variables of the text of a skin file. ValueError when it is not one (too big, not Python, or no color at all)."""
    text = str(text).lstrip("﻿")
    if len(text) > MAX_SIZE:
        raise ValueError("file too big")
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError, MemoryError) as e:
        raise ValueError("not a skin file") from e
    values = {}
    for node in tree.body:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)):
            continue
        try:
            values[node.targets[0].id] = ast.literal_eval(node.value)      # plain values only: nothing is run
        except (ValueError, TypeError, SyntaxError, RecursionError, MemoryError):
            continue
    values = check(values)
    if not any(key in values for key in COLOR_KEYS):
        raise ValueError("no color in this file")
    return values


def skin_id(name):
    """Identifier of the imported skin called `name` (importing the same name again replaces it)."""
    plain = unicodedata.normalize("NFKD", name.lower()).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "_", plain).strip("_")[:40]
    return PREFIX + (slug or hashlib.sha1(name.encode("utf-8")).hexdigest()[:10])


def install(text, folder, default_name):
    """Save the skin written in `text` into `folder`. `default_name` is used when the file has no NAME.
    Returns (identifier, variables). ValueError: not a skin file; OSError: it cannot be saved."""
    values = parse(text)
    values.setdefault("NAME", " ".join(str(default_name).split())[:60] or "Skin")
    ident = skin_id(values["NAME"])
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, ident + ".json")
    with open(path + ".part", "w", encoding="utf-8") as f:
        json.dump(values, f, ensure_ascii=False, indent=1)
    os.replace(path + ".part", path)
    return ident, values


def split(text):
    """The skins of a file: one, or several when each of them follows a MARKER line (export of the phone app)."""
    parts, current = [], []
    for line in str(text).lstrip("\ufeff").split("\n"):
        if line.strip() == MARKER:
            parts.append(current)
            current = []
        else:
            current.append(line)
    parts.append(current)
    return [joined for joined in ("\n".join(p) for p in parts) if joined.strip()]


def install_all(text, folder, default_name):
    """Save every skin of the text of a file. Returns [(identifier, variables)]; the parts that are not skins are left out.
    ValueError when there is no skin at all; OSError when one cannot be saved."""
    if len(text) > MAX_FILE:
        raise ValueError("file too big")
    parts = split(text)
    done = []
    for n, part in enumerate(parts, 1):
        try:
            done.append(install(part, folder, default_name if len(parts) == 1 else f"{default_name} {n}"))
        except ValueError:
            continue
    if not done:
        raise ValueError("no skin in this file")
    return done


def read(path):
    """Variables of a saved skin (checked again, the file may have been edited), or None when it cannot be read."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.loads(f.read(MAX_SIZE))
        return check(data) or None
    except (OSError, ValueError, AttributeError, RecursionError):
        return None


def listing(folder):
    """The imported skins of `folder`: [(identifier, variables, path)], sorted by file name."""
    try:
        names = sorted(os.listdir(folder))
    except (OSError, TypeError):
        return []
    out = []
    for name in names:
        ident, ext = os.path.splitext(name)
        if ext != ".json" or not _ID.fullmatch(ident):
            continue
        path = os.path.join(folder, name)
        values = read(path)
        if values:
            values.setdefault("NAME", ident[len(PREFIX):])
            out.append((ident, values, path))
    return out


def load(folder, ident):
    """Variables of the imported skin `ident`, or {} when it does not exist."""
    if not _ID.fullmatch(str(ident)):
        return {}
    return read(os.path.join(folder, ident + ".json")) or {}


def export_text(values):
    """The text of a skin file with the variables `values`, which `parse` (and so "Import a skin") reads back."""
    lines = ["# RA Companion skin: import it in the settings of the app (it can also be placed in the skins/ folder of the",
             "# sources). Variables that are not here come from the default skin.", ""]
    values = check(values)
    for key in TEXT_KEYS + COLOR_KEYS + tuple(NUMBER_KEYS):
        if key in values:
            lines.append(f"{key} = {values[key]!r}")
    return "\n".join(lines) + "\n"


def file_name(ident):
    """Name proposed for the exported file of the imported skin `ident`."""
    return str(ident)[len(PREFIX):] + ".py"


def bundle_text(skins):
    """One file with several skins (list of their variables), for the phones: "Import a skin" reads them all back."""
    return "\n".join(f"{MARKER}\n{export_text(values)}" for values in skins)


def export_files(folder, idents, target):
    """Write each imported skin of `idents` as a file of the directory `target`; an existing file is never replaced
    (a number is added to the name). Returns the paths written. OSError when a file cannot be written."""
    written = []
    for ident in idents:
        values = load(folder, ident)
        if not values:
            continue
        base = file_name(ident)[:-3]
        path, n = os.path.join(target, base + ".py"), 1
        while os.path.exists(path):
            n += 1
            path = os.path.join(target, f"{base}_{n}.py")
        with open(path, "x", encoding="utf-8") as f:
            f.write(export_text(values))
        written.append(path)
    return written


def remove(folder, ident):
    """Delete the imported skin `ident`. False when there is no such skin; OSError when its file cannot be deleted."""
    if not _ID.fullmatch(str(ident)):                  # only a file of `folder` can ever be deleted
        return False
    try:
        os.remove(os.path.join(folder, ident + ".json"))
    except FileNotFoundError:
        return False
    return True


def unique_name(name, taken):
    """`name`, or "name (2)", "name (3)"... when it is already in `taken` (the skins are chosen by name)."""
    result, n = name, 1
    while result in taken:
        n += 1
        result = f"{name} ({n})"
    return result
