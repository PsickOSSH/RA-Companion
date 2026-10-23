"""Small pure helpers: number/date formatting, achievement predicates and sorting."""

import unicodedata
from datetime import datetime, timezone

import i18n


def fmt_int(n):
    """Format an integer with spaces as thousands separators (falls back to str())."""
    try:
        return f"{int(n):,}".replace(",", " ")
    except Exception:
        return str(n)


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
