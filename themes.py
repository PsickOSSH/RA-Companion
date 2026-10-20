"""Skins for the mobile app. The skin files are the SAME files as the ones of the Windows version
(skins/default.py, dark.py, light.py...: UPPER_CASE variables with "#rrggbb" colors), so a skin can be copied from the PC to the phone.

Skins are loaded by file path (works with .py and with the .pyc files that python-for-android may package),
and a built-in copy of the default skin is used when the skins/ folder is missing or a variable is absent."""

import importlib.machinery
import importlib.util
import os
import re

BUILTIN = {
    "NAME": "Default (Midnight Gold)",
    "BACKGROUND": "#0f1420", "CARD": "#1a2133", "CARD_ALT": "#222c43", "CARD_LOCKED": "#141a29", "CARD_LOCKED_HOVER": "#1c2438",
    "TEXT": "#e8ecf5", "TEXT_MUTED": "#8a94ab", "TEXT_ON_ACCENT": "#1a1300",
    "ACCENT": "#f5b942", "SUCCESS": "#3ddc97", "INFO": "#6ab0ff", "WARNING": "#ff9f43", "DANGER": "#ff6b6b",
    "CONTROL_HOVER": "#34426a", "HOVER_TINT": "#ffffff", "HOVER_STRENGTH": 0.16,
}
DEFAULT_ID = "default"
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def hex_to_rgba(value, alpha=1.0):
    """'#rrggbb' -> (r, g, b, a) with floats between 0 and 1."""
    v = str(value).lstrip("#")
    return (int(v[0:2], 16) / 255.0, int(v[2:4], 16) / 255.0, int(v[4:6], 16) / 255.0, alpha)


def blend(c1, c2, t):
    """Mix two rgba colors: t = 0 gives c1, t = 1 gives c2."""
    return tuple(a + (b - a) * t for a, b in zip(c1, c2))


def read_skin(path):
    """Return the UPPER_CASE variables of a skin file (.py or .pyc), or None when the file cannot be read."""
    try:
        name = "ra_skin_" + re.sub(r"\W", "_", os.path.basename(path))
        loader = (importlib.machinery.SourcelessFileLoader if path.endswith(".pyc") else importlib.machinery.SourceFileLoader)(name, path)
        spec = importlib.util.spec_from_loader(name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        return {k: getattr(module, k) for k in dir(module) if k.isupper()}
    except Exception:
        return None


def discover(folder):
    """List the skins of `folder`: [{'id', 'name', 'path'}], the default skin first. A built-in default is always present."""
    files = {}
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        names = []
    for fname in names:
        base, ext = os.path.splitext(fname)
        if base.startswith("_") or ext not in (".py", ".pyc"):
            continue
        if base in files and ext == ".pyc":
            continue                      # the source file is preferred
        files[base] = os.path.join(folder, fname)
    skins = []
    for base, path in files.items():
        data = read_skin(path)
        if data is not None:
            skins.append({"id": base, "name": str(data.get("NAME") or base), "path": path})
    if not any(s["id"] == DEFAULT_ID for s in skins):
        skins.append({"id": DEFAULT_ID, "name": BUILTIN["NAME"], "path": None})
    skins.sort(key=lambda s: (s["id"] != DEFAULT_ID, s["name"].lower()))
    return skins


def palette(skin_vars):
    """Colors used by the interface, as rgba tuples, from the variables of a skin (missing or invalid ones use the default skin)."""
    s = dict(BUILTIN)
    for key, value in (skin_vars or {}).items():
        if key in BUILTIN and (key == "NAME" or (key == "HOVER_STRENGTH" and isinstance(value, (int, float)))
                               or (isinstance(value, str) and _HEX.match(value))):
            s[key] = value
    c = lambda key: hex_to_rgba(s[key])
    strength = max(0.0, min(0.6, float(s["HOVER_STRENGTH"]) * 1.8))
    return {
        "bg": c("BACKGROUND"), "card": c("CARD"), "alt": c("CARD_ALT"), "locked": c("CARD_LOCKED"),
        "press": blend(c("CARD_ALT"), c("HOVER_TINT"), strength),
        "text": c("TEXT"), "muted": c("TEXT_MUTED"), "accent": c("ACCENT"), "on_accent": c("TEXT_ON_ACCENT"),
        "success": c("SUCCESS"), "info": c("INFO"), "warning": c("WARNING"), "danger": c("DANGER"),
        "info_hex": s["INFO"].lstrip("#"), "muted_hex": s["TEXT_MUTED"].lstrip("#"),
    }
