"""Paths, constants and persistent settings (JSON files stored in the user's home directory)."""

import json
import os


# --- RetroAchievements endpoints ---
API = "https://retroachievements.org/API/"
MEDIA = "https://media.retroachievements.org"
# --- Files (all stored in the user's home directory) ---
HOME = os.path.expanduser("~")
CONFIG_FILE = os.path.join(HOME, ".ra_companion.json")
NOTES_FILE = os.path.join(HOME, ".ra_companion_notes.json")
GAMES_FILE = os.path.join(HOME, ".ra_companion_games.json")
GAMES_TTL = 30 * 86400
# --- Links shown in the settings window ---
API_KEY_URL = "https://retroachievements.org/settings?tab=applications"
SITE_URL = "https://retroachievements.org"
REPO_URL = "https://github.com/PsickOSSH/RA-Companion"


LOGO_URLS = {"github": "https://github.githubassets.com/favicons/favicon-dark.png",
             "ra": "https://commons.wikimedia.org/wiki/Special:FilePath/RetroAchievements_logo_square_color.png?width=64"}


def read_json(path, default):
    """Return the JSON content of `path`, or `default` if the file is missing or invalid."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def write_json(path, data):
    """Write `data` as UTF-8 JSON to `path`; failures are silently ignored (non-critical files)."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass


def load_cfg():
    """Load the user settings, filling in defaults for every missing key."""
    d = {"key": "", "user": "", "interval": 30, "alpha": 100, "ontop": False, "auto": True, "game_id": "",
        "translate": False, "ui_lang": "auto", "lang": "auto", "hc_only": False, "friend": "", "group": [],
        "skin": "default"}
    d.update(read_json(CONFIG_FILE, {}))
    return d


def save_cfg(d):
    """Persist the settings dictionary to the configuration file."""
    write_json(CONFIG_FILE, d)
