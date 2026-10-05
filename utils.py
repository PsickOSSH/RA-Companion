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
