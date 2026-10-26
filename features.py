"""Pure logic for the achievement list, detail page, notes, Duel, Group and game search (no Kivy import: testable on a PC)."""

import json
import os
import threading
import time

import storage
from utils import date_of, fmt_date, fmt_int, is_any, is_counted, is_hc, is_missable, norm, sort_achievements

GAMES_TTL = 30 * 86400   # a console game list is kept 30 days
MAX_RESULTS = 200
COMMA_LANGS = ("fr", "es", "de", "it", "pt")      # languages that write 15,5% instead of 15.5%

DEFAULT_LABELS = {
    "locked": "À débloquer",
    "sc_only": "Softcore uniquement (non compté)",
    "hc": "HARDCORE",
    "sc": "softcore",
}


def _labels(labels):
    out = dict(DEFAULT_LABELS)
    out.update(labels or {})
    return out


def _int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def achievements_of(game):
    """Return the list of achievement dicts of an API game object (empty list if the game is missing or invalid)."""
    if not isinstance(game, dict):
        return []
    ach = game.get("Achievements") or {}
    return list(ach.values()) if isinstance(ach, dict) else []


def _badge_url(media, a, shown):
    name = a.get("BadgeName", "")
    if not name:
        return ""
    return f"{media}/Badge/{name}{'' if shown else '_lock'}.png"


def _tag(a, lb):
    return lb["hc"] if is_hc(a) else lb["sc"]


def fmt_rank(rank, total, lang="en"):
    """'26 236 (15,5%)': rank, then the percentage of ranked players (decimal comma in fr / es / de / it / pt)."""
    r = _int(rank)
    if r <= 0:
        return ""
    text = fmt_int(r)
    try:
        pct = f"{100 * r / int(total):.1f}%"
        text += " (" + (pct.replace(".", ",") if lang in COMMA_LANGS else pct) + ")"
    except (TypeError, ValueError, ZeroDivisionError):
        pass
    return text


# ---------------------------------------------------------------------------
# Personal notes (one text per achievement). Same JSON format as the Windows version (.ra_companion_notes.json):
# {"achievement ID": "text"}, so the file can be exported / imported between the PC and the phone.
# ---------------------------------------------------------------------------
def parse_notes(text):
    """Notes from the text of a notes file ({ID: text}). Raises ValueError when the text is not a notes file."""
    try:
        data = json.loads(text)
    except (TypeError, ValueError):
        raise ValueError("not JSON")
    if not isinstance(data, dict):
        raise ValueError("not an object")
    notes = {str(k): v.strip() for k, v in data.items() if isinstance(v, str) and v.strip()}
    if data and not notes:
        raise ValueError("no text values")
    return notes


class NotesStore:
    """Notes of the user, saved in a JSON file. An empty note removes the entry."""

    def __init__(self, path):
        self.path = path
        self.data = {}
        self.last_error = ""
        self._lock = threading.Lock()
        loaded = storage.load_json(path, {})
        if isinstance(loaded, dict):
            self.data = {str(k): str(v) for k, v in loaded.items() if str(v).strip()}

    def get(self, ach_id):
        return self.data.get(str(ach_id), "")

    def ids(self):
        return set(self.data)

    def set(self, ach_id, text):
        """Store the note; returns True when something changed."""
        key, text = str(ach_id), (text or "").strip()
        with self._lock:
            if text == self.data.get(key, ""):
                return False
            if text:
                self.data[key] = text
            else:
                self.data.pop(key, None)
            self.save()
        return True

    def save(self):
        ok, err = storage.save_json(self.path, self.data)
        self.last_error = "" if ok else err
        return ok

    def export_text(self):
        """The notes as the text of a notes file (readable by the Windows version)."""
        return json.dumps(self.data, ensure_ascii=False, indent=2, sort_keys=True)

    def merge(self, notes):
        """Add imported notes. Returns (added, merged, unchanged): when both sides have a different text for the same
        achievement the two texts are kept, separated by '---' (nothing is lost)."""
        added = merged = unchanged = 0
        with self._lock:
            for key, text in notes.items():
                cur = self.data.get(key, "")
                if not cur:
                    self.data[key] = text
                    added += 1
                elif text == cur or text in cur:
                    unchanged += 1
                elif cur in text:
                    self.data[key] = text
                    merged += 1
                else:
                    self.data[key] = cur + "\n\n---\n" + text
                    merged += 1
            if added or merged:
                self.save()
        return added, merged, unchanged


# ---------------------------------------------------------------------------
# Achievement list
# ---------------------------------------------------------------------------
def progress_summary(game, hc_only=False):
    """Counters of the game card: unlocked / total achievements and points, and how many were won in hardcore / softcore."""
    ach = achievements_of(game)
    done = [a for a in ach if is_counted(a, hc_only)]
    total = len(ach)
    return {
        "done": len(done),
        "total": total,
        "got_pts": sum(_int(a.get("Points")) for a in done),
        "tot_pts": sum(_int(a.get("Points")) for a in ach),
        "pct": round(100 * len(done) / total) if total else 0,
        "ratio": len(done) / total if total else 0.0,
        "n_hc": sum(1 for a in ach if is_hc(a)),
        "n_sc": sum(1 for a in ach if is_any(a) and not is_hc(a)),
    }


def achievement_rows(game, media, hc_only=False, sort_mode="disp_asc", labels=None, desc_fn=None, noted=None):
    """Rows (dicts) for the achievement RecycleView, sorted with the same modes as the desktop version.
    `desc_fn` (optional) maps a description to its translation; `noted` is the set of achievement IDs that have a note."""
    lb = _labels(labels)
    desc_fn = desc_fn or (lambda t: t)
    noted = noted or set()
    rows = []
    for a in sort_achievements(achievements_of(game), sort_mode, hc_only):
        done = is_counted(a, hc_only)
        if done:
            date = f"✓ {fmt_date(date_of(a))} • {_tag(a, lb)}"
        elif is_any(a):
            date = lb["sc_only"]
        else:
            date = lb["locked"]
        rows.append({
            "ach_id": str(a.get("ID", "")),
            "title": a.get("Title", ""),
            "description": desc_fn(a.get("Description", "")),
            "points": str(a.get("Points", 0)),
            "date": date,
            "status": "unlocked" if done else "locked",
            "badge_url": _badge_url(media, a, done),
            "missable": bool(is_missable(a)),
            "has_note": str(a.get("ID", "")) in noted,
        })
    return rows


def filter_rows(rows, name, missable_only=False):
    """Status filter (all / locked / unlocked) that can be combined with the 'missable only' option."""
    if name == "unlocked":
        rows = [r for r in rows if r["status"] == "unlocked"]
    elif name == "locked":
        rows = [r for r in rows if r["status"] == "locked"]
    elif name == "missable":          # old name of the filter, kept for compatibility
        missable_only = True
    if missable_only:
        rows = [r for r in rows if r.get("missable")]
    return list(rows)


# ---------------------------------------------------------------------------
# Achievement detail page and unlock detection
# ---------------------------------------------------------------------------
def load_comments(call_api, key, ach_id, limit=100):
    """Return (total, comments) with the `limit` newest comments, newest first. `call_api` is ra_api.call_api."""
    first = call_api("API_GetComments.php", key, t=2, i=ach_id, c=limit, o=0)
    first = first if isinstance(first, dict) else {}
    total = _int(first.get("Total"))
    results = first.get("Results") or []
    if total > limit:
        second = call_api("API_GetComments.php", key, t=2, i=ach_id, c=limit, o=total - limit)
        results = (second.get("Results") if isinstance(second, dict) else None) or []
    comments = [{"user": r.get("User", ""), "date": r.get("Submitted", ""), "text": (r.get("CommentText") or "").strip()}
                for r in results]
    comments.reverse()
    return total, comments


class UnlockTracker:
    """Detects newly unlocked achievements between two refreshes (yours and a friend's). Thread-safe."""

    def __init__(self):
        self._lock = threading.Lock()
        self.reset()

    def reset(self):
        with self._lock:
            self._gid = None
            self._known = None
            self._fkey = None
            self._fknown = None

    def check(self, gid, game, friend, friend_game):
        """Return (my_new, friend_new): achievements unlocked since the previous call on the same game."""
        with self._lock:
            mine, theirs = [], []
            ach = achievements_of(game)
            if ach:   # an empty answer (network hiccup) must not reset the baseline
                ids = {str(a.get("ID")) for a in ach if is_any(a)}
                if self._known is not None and gid == self._gid:
                    mine = [a for a in ach if is_any(a) and str(a.get("ID")) not in self._known]
                self._known, self._gid = ids, gid
            if friend and isinstance(friend_game, dict) and not friend_game.get("error") and achievements_of(friend_game):
                fach = achievements_of(friend_game)
                fids = {str(a.get("ID")) for a in fach if is_any(a)}
                fkey = (gid, friend.lower())
                if self._fknown is not None and self._fkey == fkey:
                    theirs = [a for a in fach if is_any(a) and str(a.get("ID")) not in self._fknown]
                self._fknown, self._fkey = fids, fkey
            elif not friend:
                self._fknown, self._fkey = None, None
            return mine, theirs


# ---------------------------------------------------------------------------
# Duel
# ---------------------------------------------------------------------------
def compute_duel(me_game, friend_game, user, friend, media, hc_only=False, labels=None, desc_fn=None, noted=None):
    """Compare two players on the same game. Returns the counters and the rows of the duel list."""
    lb = _labels(labels)
    desc_fn = desc_fn or (lambda t: t)
    noted = noted or set()
    theirs = {str(a.get("ID")): a for a in achievements_of(friend_game)}
    data = []
    for a in achievements_of(me_game):
        b = theirs.get(str(a.get("ID")))
        data.append((a, b, is_counted(a, hc_only), b is not None and is_counted(b, hc_only)))

    def order(d):
        a, _b, mee, fre = d
        if fre and not mee:
            grp = 0
        elif mee and not fre:
            grp = 1
        elif not (mee or fre):
            grp = 2
        else:
            grp = 3
        return grp, _int(a.get("DisplayOrder"))

    rows = []
    for a, b, mee, fre in sorted(data, key=order):
        if mee and fre:
            state = "both"
        elif mee:
            state = "me"
        elif fre:
            state = "friend"
        else:
            state = "none"
        rows.append({
            "ach_id": str(a.get("ID", "")),
            "title": a.get("Title", ""),
            "description": desc_fn(a.get("Description", "")),
            "points": str(a.get("Points", 0)),
            "badge_url": _badge_url(media, a, mee or fre),
            "me_line": f"{user} • {fmt_date(date_of(a))} • {_tag(a, lb)}" if mee else "",
            "fr_line": f"{friend} • {fmt_date(date_of(b))} • {_tag(b, lb)}" if fre else "",
            "state": state,
            "missable": bool(is_missable(a)),
            "has_note": str(a.get("ID", "")) in noted,
        })
    return {
        "x": sum(1 for d in data if d[2]),
        "y": sum(1 for d in data if d[3]),
        "tot": len(data),
        "pa": sum(_int(d[0].get("Points")) for d in data if d[2]),
        "pb": sum(_int(d[0].get("Points")) for d in data if d[3]),
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Group
# ---------------------------------------------------------------------------
def build_entry(name, summary, game, pic, me=False, hc_only=False):
    """One player of the group dashboard."""
    summary = summary or {}
    ach = achievements_of(game)
    last = summary.get("LastGame") or {}
    return {
        "name": name,
        "pic": pic or "",
        "pts": summary.get("TotalPoints", 0) or 0,
        "play": summary.get("RichPresenceMsg") or last.get("Title") or "",
        "cnt": sum(1 for a in ach if is_counted(a, hc_only)),
        "tot": len(ach),
        "err": "",
        "me": me,
        "wait": False,
    }


def group_entries(user, my_summary, my_game, my_pic, members, data, hc_only=False):
    """Entries of the dashboard (you + the members), best progress first. `data` maps member.lower() to the API data."""
    entries = []
    if my_summary:
        entries.append(build_entry(user, my_summary, my_game, my_pic, True, hc_only))
    for m in members:
        d = (data or {}).get(m.lower())
        if d is None:
            entries.append({"name": m, "pic": "", "pts": 0, "play": "", "cnt": 0, "tot": 0, "err": "", "me": False, "wait": True})
        elif d.get("error"):
            entries.append({"name": m, "pic": "", "pts": 0, "play": "", "cnt": 0, "tot": 0, "err": str(d["error"]), "me": False, "wait": False})
        else:
            entries.append(build_entry(m, d.get("s"), d.get("game"), d.get("pic"), False, hc_only))
    entries.sort(key=lambda e: (-(e["cnt"] / e["tot"] if e["tot"] else 0), -e["cnt"], e["name"].lower()))
    return entries


def entry_rows(entries, media):
    """Rows for the group RecycleView."""
    rows = []
    for e in entries:
        rows.append({
            "member": e["name"],
            "points_line": f"{fmt_int(e['pts'])} pts",
            "play": "…" if e["wait"] else e["play"],
            "err": e["err"],
            "progress": (e["cnt"] / e["tot"]) if e["tot"] else 0,
            "progress_text": f"{e['cnt']} / {e['tot']}" if e["tot"] else "",
            "pic_url": f"{media}{e['pic']}" if e["pic"] else "",
            "me": e["me"],
            "removable": not e["me"],
        })
    return rows


# ---------------------------------------------------------------------------
# Game search (local index of the game lists, like the desktop version)
# ---------------------------------------------------------------------------
class GameIndex:
    """Console list + game list of every console, cached in a JSON file."""

    def __init__(self, path):
        self.path = path
        self.data = {"consoles": [], "ct": 0, "games": {}}
        self._lock = threading.RLock()
        self.load()

    def load(self):
        d = storage.load_json(self.path, None)
        if isinstance(d, dict) and isinstance(d.get("consoles"), list) and isinstance(d.get("games"), dict):
            self.data = {"consoles": d["consoles"], "ct": d.get("ct", 0), "games": d["games"]}

    def save(self):
        with self._lock:
            storage.save_json(self.path, self.data)

    def console_list(self):
        return [(c[0], c[1]) for c in self.data["consoles"] if isinstance(c, (list, tuple)) and len(c) >= 2]

    def consoles_fresh(self):
        return bool(self.data["consoles"]) and time.time() - self.data.get("ct", 0) < GAMES_TTL

    def set_consoles(self, raw):
        with self._lock:
            self.data["consoles"] = sorted(([c["ID"], c["Name"]] for c in raw if "ID" in c and "Name" in c), key=lambda c: c[1])
            self.data["ct"] = time.time()
        self.save()

    def is_fresh(self, cid):
        g = self.data["games"].get(str(cid))
        return bool(g) and time.time() - g.get("t", 0) < GAMES_TTL

    def set_games(self, cid, games):
        rows = [[g.get("ID"), g.get("Title", ""), g.get("ConsoleName", ""), g.get("NumAchievements", 0)] for g in games]
        with self._lock:
            self.data["games"][str(cid)] = {"t": time.time(), "g": rows}

    def search(self, query, cids):
        """Return up to MAX_RESULTS dicts {game_id, title, console, count}. A number is also offered as a game ID."""
        q = norm(query.strip())
        res = []
        if q.isdigit():
            res.append({"game_id": int(q), "title": f"ID {q}", "console": "", "count": 0})
        if len(q) >= 2:
            words = q.split()
            found = []
            for cid in cids:
                g = self.data["games"].get(str(cid))
                if not g:
                    continue
                for item in g.get("g", []):
                    if len(item) < 4:
                        continue
                    gid, title, cname, n = item[:4]
                    nt = norm(title)
                    if all(w in nt for w in words):
                        found.append((not nt.startswith(words[0]), nt, gid, title, cname, n))
            found.sort(key=lambda f: (f[0], f[1], str(f[2])))
            for _a, _b, gid, title, cname, n in found[:MAX_RESULTS]:
                res.append({"game_id": gid, "title": title, "console": cname, "count": n})
        return res
