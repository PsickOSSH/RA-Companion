"""Export and import of the settings (Windows, Linux, Android and iOS read each other's files).

The file holds every setting except the skin (the skins have their own export) and the position of the window, which only
makes sense on one computer. The personal notes have their own export too. The account key and the translation keys are in
it, in plain text. Only known settings with a valid value are imported."""

import copy
import json
import re

from i18n import SORT_IDS

FORMAT = "ra-companion-settings"
MAX_FILE = 200_000          # characters
EXCLUDED = ("skin", "win_geo")
ACCOUNT = ("user", "key")      # kept when the settings are reset "keeping the account": everything else goes back to default


def _bool(value):
    return value if isinstance(value, bool) else None


def _text(value):
    return value if isinstance(value, str) and len(value) <= 500 else None


def _number(low, high):
    def rule(value):
        return value if isinstance(value, int) and not isinstance(value, bool) and low <= value <= high else None
    return rule


def _choice(*choices):
    return lambda value: value if isinstance(value, str) and value in choices else None


def _pattern(regex):
    return lambda value: value if isinstance(value, str) and re.fullmatch(regex, value) else None


def _game_id(value):
    text = str(value) if isinstance(value, int) and not isinstance(value, bool) else value
    return text if isinstance(text, str) and re.fullmatch(r"\d{0,12}", text) else None


def _texts(value):
    if isinstance(value, list) and len(value) <= 100 and all(_text(v) is not None for v in value):
        return list(value)
    return None


def _services(value):
    """AI translation services: [{"url", "model", "key"}]."""
    if not isinstance(value, list) or len(value) > 20 or not all(isinstance(e, dict) for e in value):
        return None
    out = [{k: e.get(k, "") for k in ("url", "model", "key")} for e in value]
    return out if all(_text(v) is not None for e in out for v in e.values()) else None


_LANG = _pattern(r"auto|[a-z]{2}(-[A-Za-z]{2,4})?")

# setting -> rule: gives the value to keep, or None when it is not valid. Every new setting of the app must be added here
# (or to EXCLUDED); tests/test_settings_io.py checks it.
RULES = {
    # account
    "user": _text, "key": _text,
    # what is followed
    "auto": _bool, "game_id": _game_id, "friend": _text, "group": _texts, "hc_only": _bool, "interval": _number(5, 3600),
    "auto_refresh": _bool, "notify": _bool,
    # display
    "ui_lang": _LANG, "lang": _LANG, "translate": _bool, "sort": _choice(*SORT_IDS), "miss_only": _bool,
    "filter": _choice("all", "locked", "unlocked"), "tab": _choice("success", "duel", "group"),
    # Windows / Linux
    "ontop": _bool, "alpha": _number(30, 100), "note_height": _number(20, 4000), "overlay": _bool,
    "overlay_port": _number(1, 65535), "refresh_key": _pattern(r"(Control-)?(Alt-)?(Shift-)?(F([1-9]|1[0-2])|[a-z0-9])"),
    # translation
    "tr_service": _text, "tr_order": _texts, "deepl_key": _text, "libre_url": _text, "libre_key": _text,
    "libre_insecure": _bool, "ai_url": _text, "ai_key": _text, "ai_model": _text, "ai_services": _services,
}


def valid(settings):
    """The settings of the dictionary `settings` that are known and valid."""
    out = {}
    for name, rule in RULES.items():
        if name in settings:
            value = rule(settings[name])
            if value is not None:
                out[name] = value
    return out


def reset(cfg, defaults, keep_account):
    """Put the settings of the configuration `cfg` (changed in place) back to their values of a first start (`defaults`).
    The skin and the window position stay; with `keep_account` the settings of ACCOUNT stay too."""
    for name in RULES:
        if keep_account and name in ACCOUNT:
            continue
        if name in defaults:
            cfg[name] = copy.deepcopy(defaults[name])
        else:
            cfg.pop(name, None)                # a setting without a stored default: the app uses its own one


def export_text(cfg):
    """The text of a settings file for the configuration `cfg`."""
    return json.dumps({"format": FORMAT, "version": 1, "settings": valid(cfg)}, ensure_ascii=False, indent=2) + "\n"


def parse(text):
    """The settings of the text of a settings file. ValueError when it is not one."""
    text = str(text).lstrip("﻿")
    if len(text) > MAX_FILE:
        raise ValueError("file too big")
    try:
        data = json.loads(text)
    except RecursionError as e:
        raise ValueError("not a settings file") from e
    if not isinstance(data, dict) or data.get("format") != FORMAT or not isinstance(data.get("settings"), dict):
        raise ValueError("not a settings file")
    settings = valid(data["settings"])
    if not settings:
        raise ValueError("no setting in this file")
    return settings
