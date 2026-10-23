"""Median time to unlock (hardcore players only) of each achievement of a game.

Source: API_GetGameProgression.php, field MedianTimeToUnlockHardcore, in seconds. The standard median is ignored on purpose:
softcore allows save states and other shortcuts, so only the hardcore values describe the real effort. The answer is kept in
memory and on disk for one day, so the app does not ask for it at every refresh.
"""

import json
import os
import time

TTL = 24 * 3600
RETRY_AFTER = 600

_MEMORY = {}
_FAILED = {}


def _parse(reply):
    """{achievement id: seconds} from the answer of the API (only the positive hardcore medians)."""
    items = reply.get("Achievements") if isinstance(reply, dict) else None
    if isinstance(items, dict):
        items = list(items.values())
    out = {}
    for a in items or []:
        try:
            seconds = float(a.get("MedianTimeToUnlockHardcore"))
            if seconds > 0:
                out[int(a["ID"])] = seconds
        except (TypeError, ValueError, KeyError, AttributeError):
            continue
    return out


def _file(folder, game_id):
    return os.path.join(folder, f"{game_id}.json") if folder else None


def _read(folder, game_id, now):
    path = _file(folder, game_id)
    try:
        if path and now - os.path.getmtime(path) < TTL:
            with open(path, encoding="utf-8") as f:
                return {int(k): float(v) for k, v in json.load(f).items()}
    except (OSError, ValueError, TypeError):
        pass
    return None


def _write(folder, game_id, data):
    path = _file(folder, game_id)
    if not path:
        return
    try:
        os.makedirs(folder, exist_ok=True)
        tmp = path + ".part"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, path)
    except OSError:
        pass


def fetch(call_api, key, game_id, folder=None):
    """Hardcore median unlock times {achievement id: seconds} of a game; {} when the API has nothing or fails."""
    gid = str(game_id)
    now = time.time()
    known = _MEMORY.get(gid)
    if known and now - known[0] < TTL:
        return known[1]
    data = _read(folder, gid, now)
    if data is None:
        if now - _FAILED.get(gid, 0) < RETRY_AFTER:
            return known[1] if known else {}
        try:
            data = _parse(call_api("API_GetGameProgression.php", key, i=gid, h=1))
        except Exception:
            _FAILED[gid] = now
            return known[1] if known else {}
        _write(folder, gid, data)
    _MEMORY[gid] = (now, data)
    return data


def apply(game, medians):
    """Put the median of each achievement of `game` (the answer of API_GetGameInfoAndUserProgress) in its dictionary."""
    items = game.get("Achievements") if isinstance(game, dict) else None
    if isinstance(items, dict):
        items = list(items.values())
    for a in items or []:
        try:
            value = medians.get(int(a["ID"]))
        except (TypeError, ValueError, KeyError, AttributeError):
            continue
        if value:
            a["MedianTimeToUnlockHardcore"] = value
