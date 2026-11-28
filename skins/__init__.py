"""Skin system.

A skin is a Python file in this folder that defines UPPER_CASE variables (colors, fonts, corner
radii). See `default.py` for the full, documented list and for instructions on creating a skin.

The skin chosen in the settings (saved as "skin" in the configuration file) is loaded once, when
this package is imported, and exposed as `skins.active`. Other modules simply do:

    from skins import active as skin
    ... skin.CARD, skin.ACCENT, skin.RADIUS_CARD ...

Changing the skin therefore requires a restart, which the settings window does automatically.
The skins imported by the user are data files in `USER_DIR` (see userskins.py).
"""

import importlib
import os
import pkgutil
from types import SimpleNamespace

import userskins
from config import CONFIG_FILE, HOME, read_json

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DIR = os.path.join(HOME, ".ra_companion_skins")          # skins imported in the settings


def _values(module):
    """Return the UPPER_CASE variables of a skin module as a dictionary."""
    return {name: value for name, value in vars(module).items() if name.isupper()}


def _import(name):
    return importlib.import_module(f"{__name__}.{name}")


def available():
    """Return {display name: skin identifier} for every skin of this folder and every imported one."""
    found = {}
    for info in pkgutil.iter_modules([_PACKAGE_DIR]):
        if info.name.startswith("_"):          # files starting with "_" are ignored (templates, helpers)
            continue
        try:
            module = _import(info.name)
        except Exception:                      # a broken skin must never prevent the app from starting
            continue
        found[getattr(module, "NAME", info.name)] = info.name
    for ident, values, _path in userskins.listing(USER_DIR):
        found[userskins.unique_name(values["NAME"], found)] = ident
    return found


def load(name):
    """Build a skin: the default values, overridden by the variables of skin `name`."""
    values = _values(_import("default"))
    if str(name).startswith(userskins.PREFIX):
        values.update(userskins.load(USER_DIR, name))
    elif name != "default":
        try:
            values.update(_values(_import(name)))
        except Exception:                      # unknown / broken skin -> fall back to the default one
            pass
    if os.name != "nt":                        # the Windows fonts do not exist on Linux / macOS
        from symbols import FONT_OK, SYMBOL_FAMILY
        if str(values.get("FONT", "")).startswith("Segoe UI"):
            values["FONT"] = "DejaVu Sans"
        if str(values.get("SYMBOL_FONT", "")).startswith("Segoe UI"):
            values["SYMBOL_FONT"] = SYMBOL_FAMILY if FONT_OK else "DejaVu Sans"   # monochrome emoji like the ones of Windows
    return SimpleNamespace(**values)


# The skin used by the whole application.
active = load(read_json(CONFIG_FILE, {}).get("skin", "default"))
