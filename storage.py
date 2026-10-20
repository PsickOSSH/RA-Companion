"""JSON files in the private folder of the app: atomic writes, a .bak copy, and errors that are reported instead of swallowed."""

import json
import os
import shutil


def load_json(path, default=None):
    """Read a JSON file. A damaged file falls back to its .bak copy, then to `default`."""
    for candidate in (path, path + ".bak"):
        try:
            with open(candidate, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            continue
        except Exception:
            continue
    return default


def save_json(path, data):
    """Write `data` atomically (temporary file, flush, fsync, rename). Returns (ok, error_text)."""
    tmp = path + ".tmp"
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.flush()
            os.fsync(f.fileno())
        if os.path.exists(path):
            try:
                shutil.copyfile(path, path + ".bak")
            except OSError:
                pass
        os.replace(tmp, path)
        return True, ""
    except Exception as e:
        return False, f"{e.__class__.__name__}: {e}"
