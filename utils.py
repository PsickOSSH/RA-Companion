"""Small pure helpers: number/date formatting, achievement predicates and sorting."""

import re
import time
import unicodedata
from datetime import datetime, timezone
from urllib.parse import quote

import i18n
from config import SITE_URL


def fmt_int(n):
    """Format an integer with spaces as thousands separators (falls back to str())."""
    try:
        return f"{int(n):,}".replace(",", " ")
    except Exception:
        return str(n)


_LINK = re.compile(r"(?:https?://|www\.)[^\s<>\"\[\]]+", re.I)


def split_links(text):
    """Cut `text` into [(piece, url)]: url is None for normal text, the address to open for a web link (comments)."""
    out, pos = [], 0
    for m in _LINK.finditer(text or ""):
        link = m.group(0)
        while link and link[-1] in ".,;:!?'\"]}" or (link.endswith(")") and link.count(")") > link.count("(")):
            link = link[:-1]                                   # punctuation that follows the link in the sentence
        if len(link) < 5:
            continue
        if m.start() > pos:
            out.append((text[pos:m.start()], None))
        out.append((link, link if link.lower().startswith("http") else "https://" + link))
        pos = m.start() + len(link)
    if pos < len(text or ""):
        out.append((text[pos:], None))
    return out


def markup_links(text, color):
    """`text` as Kivy markup: the web links are coloured, underlined and clickable ([ref=url]); the rest is escaped."""
    def esc(s):
        return s.replace("&", "&amp;").replace("[", "&bl;").replace("]", "&br;")
    parts = []
    for piece, url in split_links(text):
        if url:
            ref = url.replace("[", "%5B").replace("]", "%5D")
            parts.append(f"[ref={ref}][color={color}][u]{esc(piece)}[/u][/color][/ref]")
        else:
            parts.append(esc(piece))
    return "".join(parts)


def game_url(game_id):
    """Page of a game on RetroAchievements."""
    return f"{SITE_URL}/game/{game_id}"


def achievement_url(ach_id):
    """Page of an achievement on RetroAchievements."""
    return f"{SITE_URL}/achievement/{ach_id}"


def user_url(name):
    """Profile page of a player on RetroAchievements."""
    return f"{SITE_URL}/user/{quote(str(name), safe='')}"


def norm(s):
    """Lower-case a string and strip its accents, for accent-insensitive searching."""
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join((c for c in s if unicodedata.category(c) != "Mn"))


def is_hc(a):
    """True if the achievement was unlocked in hardcore mode."""
    return bool(a.get("DateEarnedHardcore"))


def is_any(a):
    """True if the achievement was unlocked in either hardcore or softcore mode."""
    return bool(a.get("DateEarnedHardcore") or a.get("DateEarned"))


def is_missable(a):
    """True for achievements flagged as missable (API `type` field, or the legacy '[m]' title suffix)."""
    t = str(a.get("type") or a.get("Type") or "").lower()
    return t == "missable" or str(a.get("Title", "")).rstrip().lower().endswith("[m]")


def is_counted(a, hc_only):
    """True if the achievement counts as unlocked given the 'hardcore only' option."""
    return is_hc(a) if hc_only else is_any(a)


# The API returns UTC dates: True shows them in the local time zone of the computer.
DATES_TO_LOCAL = True


DATE_FMT = {"en": "%m/%d/%Y %I:%M %p", "fr": "%d/%m/%Y %H:%M", "es": "%d/%m/%Y %H:%M",
            "de": "%d.%m.%Y %H:%M", "it": "%d/%m/%Y %H:%M", "pt": "%d/%m/%Y %H:%M"}


DAY_FMT = {"en": "%m/%d/%Y", "fr": "%d/%m/%Y", "es": "%d/%m/%Y", "de": "%d.%m.%Y", "it": "%d/%m/%Y", "pt": "%d/%m/%Y"}


def fmt_date(txt, with_time=True):
    """Format an API date (YYYY-MM-DD HH:MM:SS, UTC) according to the current UI language."""
    if not txt:
        return ""
    try:
        dt = datetime.strptime(str(txt).replace("T", " ")[:19], "%Y-%m-%d %H:%M:%S")
        if DATES_TO_LOCAL:
            dt = dt.replace(tzinfo=timezone.utc).astimezone()
        return dt.strftime((DATE_FMT if with_time else DAY_FMT).get(i18n.CUR, DATE_FMT["en"]))
    except Exception:
        return str(txt)[:16] if with_time else str(txt)[:10]


def date_of(a):
    """Return the unlock date of an achievement (hardcore date first), or an empty string."""
    return a.get("DateEarnedHardcore") or a.get("DateEarned") or ""


def sort_achievements(ach, mode, hc_only=False):
    """Sort a list of achievements according to one of the sort modes of the sort menu."""
    if mode == "unlocked_first":
        return sorted(ach, key=lambda a: (not is_counted(a, hc_only), int(a.get("DisplayOrder", 0) or 0)))
    key, _, direction = mode.rpartition("_")
    if key == "med":
        sign = -1 if direction == "desc" else 1
        return sorted(ach, key=lambda a: (median_unlock_hc(a) is None, sign * (median_unlock_hc(a) or 0)))
    if key == "disp":
        k = lambda a: int(a.get("DisplayOrder", 0) or 0)
    elif key == "awd":
        k = lambda a: int(a.get("NumAwarded", 0) or 0)
    elif key == "pts":
        k = lambda a: int(a.get("Points", 0) or 0)
    elif key == "title":
        k = lambda a: norm(a.get("Title", ""))
    else:
        k = lambda a: (not (a.get("type") or a.get("Type")), str(a.get("type") or a.get("Type") or ""))
    return sorted(ach, key=k, reverse=direction == "desc")

# ---------------------------------------------------------------------------
# Median times from API_GetGameProgression.php (hardcore only)
# ---------------------------------------------------------------------------
# The API also returns "standard" medians (MedianTimeToUnlock, MedianTimeToBeat, MedianTimeToComplete). They are ignored on
# purpose: softcore allows save states and other shortcuts, so only the hardcore values describe the real effort.


def _seconds(value):
    """Positive number of seconds from an API value, or None when it is missing, zero or not a number."""
    try:
        s = float(value)
    except (TypeError, ValueError):
        return None
    return s if s > 0 else None


def median_unlock_hc(a):
    """Median time (seconds) the hardcore players needed to unlock this achievement, or None if the API has no value."""
    return _seconds(a.get("MedianTimeToUnlockHardcore"))


def median_beat_hc(game):
    """Median time (seconds) the hardcore players needed to beat the game, or None."""
    return _seconds(game.get("MedianTimeToBeatHardcore"))


def median_master(game):
    """Median time (seconds) to master the game. A mastery is earned in hardcore, so this value is a hardcore one."""
    return _seconds(game.get("MedianTimeToMaster"))


def fmt_duration(seconds):
    """Format seconds as '45 s', '4 min 34 s', '5 h 12 min' or '134 h'. Empty string when the value is unknown."""
    s = _seconds(seconds)
    if s is None:
        return ""
    s = int(round(s))
    if s < 60:
        return f"{s} s"
    minutes, sec = divmod(s, 60)
    if minutes < 60:
        return f"{minutes} min {sec:02d} s"
    hours, minutes = divmod(minutes, 60)
    if hours >= 100:
        return f"{hours} h"
    return f"{hours} h {minutes:02d} min" if minutes else f"{hours} h"


# ---------------------------------------------------------------------------
# Recently played games and "Want to Play" list (search page)
# ---------------------------------------------------------------------------
def _count(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def recent_games(reply, hc_only=False):
    """Games of API_GetUserRecentlyPlayedGames.php: [{game_id, title, console, done, total}], the last played first."""
    out = []
    for g in reply if isinstance(reply, list) else []:
        if not isinstance(g, dict) or not g.get("GameID"):
            continue
        hc = _count(g.get("NumAchievedHardcore"))
        out.append({"game_id": _count(g.get("GameID")), "title": str(g.get("Title") or "?"),
                    "console": str(g.get("ConsoleName") or ""), "done": hc if hc_only else max(hc, _count(g.get("NumAchieved"))),
                    "total": _count(g.get("NumPossibleAchievements") or g.get("AchievementsTotal"))})
    return out


def want_games(reply):
    """Games of API_GetUserWantToPlayList.php: [{game_id, title, console, total}], sorted by title."""
    items = reply.get("Results") if isinstance(reply, dict) else None
    out = [{"game_id": _count(g.get("ID")), "title": str(g.get("Title") or "?"), "console": str(g.get("ConsoleName") or ""),
            "total": _count(g.get("AchievementsPublished"))} for g in items or [] if isinstance(g, dict) and g.get("ID")]
    return sorted(out, key=lambda g: norm(g["title"]))


def filter_games(games, query):
    """Games of a list whose title or console contains every word of `query` (case and accents ignored)."""
    words = norm(query).split()
    return [g for g in games if all(w in norm(f"{g['title']} {g['console']}") for w in words)]


# ---------------------------------------------------------------------------
# Session summary: the achievements unlocked since the program was started
# ---------------------------------------------------------------------------
SESSION_MARGIN = 60        # seconds: tolerated difference between the clock of the device and the one of the server


def api_time(text):
    """Time stamp (seconds since 1970) of an API date ('YYYY-MM-DD HH:MM:SS', UTC), or None."""
    try:
        dt = datetime.strptime(str(text).replace("T", " ")[:19], "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return None
    return dt.replace(tzinfo=timezone.utc).timestamp()


def short_time(seconds):
    """'12 min' or '1 h 05' (whole minutes)."""
    minutes = max(0, int(seconds // 60))
    return f"{minutes} min" if minutes < 60 else f"{minutes // 60} h {minutes % 60:02d}"


class Session:
    """Remembers the achievements unlocked since `start`. The games given to `add` can change from one call to the next."""

    def __init__(self, start=None):
        self.start = time.time() if start is None else start
        self.items = {}                      # achievement ID -> description of the unlock

    def add(self, game):
        """Look for new unlocks in a game (answer of API_GetGameInfoAndUserProgress). Returns the new ones, oldest first."""
        achievements = (game or {}).get("Achievements") or {}
        new = []
        for a in achievements.values() if isinstance(achievements, dict) else achievements:
            hc, sc = api_time(a.get("DateEarnedHardcore")), api_time(a.get("DateEarned"))
            when = max(hc or 0, sc or 0)
            if when < self.start - SESSION_MARGIN:
                continue
            key = str(a.get("ID"))
            is_new_hc = bool(hc) and hc >= self.start - SESSION_MARGIN
            old = self.items.get(key)
            if old and (old["hc"] or not is_new_hc):
                continue                     # already known (an achievement won again in hardcore is updated)
            item = {"id": key, "title": str(a.get("Title") or ""), "description": str(a.get("Description") or ""),
                    "points": _count(a.get("Points")), "badge": str(a.get("BadgeName") or ""),
                    "game": str(game.get("Title") or ""), "hc": is_new_hc, "when": when}
            self.items[key] = item
            if not old:
                new.append(item)
        return sorted(new, key=lambda i: i["when"])

    def unlocks(self, hc_only=False):
        """The unlocks of the session, the newest first."""
        items = list(self.items.values())      # copy: the phone app adds unlocks from its background thread
        return sorted((i for i in items if i["hc"] or not hc_only), key=lambda i: i["when"], reverse=True)

    def summary(self, hc_only=False, now=None):
        """(number of achievements, points, duration as text)."""
        items = self.unlocks(hc_only)
        now = time.time() if now is None else now
        return len(items), sum(i["points"] for i in items), short_time(now - self.start)


# --- Keyboard shortcut of the Refresh button (Windows) -----------------------------------------------------------
DEFAULT_REFRESH_KEY = "Control-Alt-r"      # not F1: emulators such as Dolphin use the F-keys
_MODIFIER_KEYSYMS = {"Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Meta_L", "Meta_R", "Super_L",
                     "Super_R", "Caps_Lock", "Num_Lock", "ISO_Level3_Shift"}


def shortcut_from_key(keysym, state):
    """Tk sequence (without the < >) for a key press, or None when it is not allowed as a shortcut.

    Allowed: F1 to F12 (alone or with Ctrl / Alt / Shift), or a letter / digit together with Ctrl or Alt. A plain letter
    is refused because it would also fire while typing in the text fields. `state` is the Tk event state (Windows)."""
    if keysym in _MODIFIER_KEYSYMS:
        return None
    shift, ctrl, alt = bool(state & 0x1), bool(state & 0x4), bool(state & 0x20000)
    is_fkey = len(keysym) > 1 and keysym[0] == "F" and keysym[1:].isdigit() and 1 <= int(keysym[1:]) <= 12
    if is_fkey:
        key = keysym
    elif len(keysym) == 1 and keysym.isalnum() and keysym.isascii() and (ctrl or alt) and not shift:
        key = keysym.lower()
    else:
        return None
    mods = (["Control"] if ctrl else []) + (["Alt"] if alt else []) + (["Shift"] if shift else [])
    return "-".join(mods + [key])


def shortcut_label(seq):
    """Readable form of a shortcut sequence: 'Control-r' -> 'Ctrl+R'."""
    parts = str(seq or DEFAULT_REFRESH_KEY).split("-")
    return "+".join("Ctrl" if p == "Control" else p.upper() if len(p) == 1 else p for p in parts)
