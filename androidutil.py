"""Android helpers (through pyjnius): open a web link, save / read a text file with the system file picker.
On a PC the file functions use ~/ra_companion_notes.json so that the app can be tested without a phone."""

import os

from kivy.clock import Clock
from kivy.utils import platform

_REQ_SAVE, _REQ_OPEN = 7101, 7102
_pending = {}
_bound = False


def open_url(url):
    if platform == "android":
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            intent = Intent(Intent.ACTION_VIEW)
            intent.setData(Uri.parse(url))
            PythonActivity.mActivity.startActivity(intent)
            return True
        except Exception as e:
            print("open_url: Android intent failed:", e)
    try:
        import webbrowser
        return webbrowser.open(url)
    except Exception:
        return False


def _activity():
    from jnius import autoclass
    return autoclass("org.kivy.android.PythonActivity").mActivity


def _bind_once():
    global _bound
    if not _bound:
        from android import activity
        activity.bind(on_activity_result=_on_result)
        _bound = True


def _on_result(request_code, result_code, intent):
    """Called by Android when the file picker closes. `status` given to the callback: 'ok', 'cancel' or 'error'."""
    job = _pending.pop(request_code, None)
    if job is None:
        return
    kind, text, callback = job
    status, data = "cancel", ""
    try:
        if result_code == -1 and intent is not None and intent.getData() is not None:     # -1 = RESULT_OK
            from jnius import autoclass
            uri = intent.getData()
            resolver = _activity().getContentResolver()
            if kind == "save":
                writer = autoclass("java.io.OutputStreamWriter")(resolver.openOutputStream(uri, "wt"), "UTF-8")
                writer.write(text)
                writer.flush()
                writer.close()
                status, data = "ok", str(uri.getLastPathSegment() or "")
            else:
                reader = autoclass("java.io.BufferedReader")(autoclass("java.io.InputStreamReader")(resolver.openInputStream(uri), "UTF-8"))
                lines, size, line = [], 0, reader.readLine()
                while line is not None and size < 5_000_000:
                    lines.append(line)
                    size += len(line)
                    line = reader.readLine()
                reader.close()
                status, data = "ok", "\n".join(lines)
    except Exception as e:
        status, data = "error", f"{e.__class__.__name__}: {e}"
    Clock.schedule_once(lambda dt: callback(status, data))


def save_text(filename, text, callback):
    """Ask the user where to save `text` (system 'save as' dialog). callback(status, info) runs on the Kivy thread."""
    if platform == "android":
        try:
            from jnius import autoclass
            _bind_once()
            Intent = autoclass("android.content.Intent")
            intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("application/json")
            intent.putExtra(Intent.EXTRA_TITLE, filename)
            _pending[_REQ_SAVE] = ("save", text, callback)
            _activity().startActivityForResult(intent, _REQ_SAVE)
        except Exception as e:
            _pending.pop(_REQ_SAVE, None)
            callback("error", f"{e.__class__.__name__}: {e}")
        return
    path = os.path.join(os.path.expanduser("~"), filename)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        callback("ok", path)
    except Exception as e:
        callback("error", str(e))


def read_text(callback):
    """Ask the user to choose a file (system picker) and give its text to callback(status, text)."""
    if platform == "android":
        try:
            from jnius import autoclass
            _bind_once()
            Intent = autoclass("android.content.Intent")
            intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("*/*")
            _pending[_REQ_OPEN] = ("open", "", callback)
            _activity().startActivityForResult(intent, _REQ_OPEN)
        except Exception as e:
            _pending.pop(_REQ_OPEN, None)
            callback("error", f"{e.__class__.__name__}: {e}")
        return
    path = os.path.join(os.path.expanduser("~"), "ra_companion_notes.json")
    try:
        with open(path, encoding="utf-8") as f:
            callback("ok", f.read())
    except FileNotFoundError:
        callback("cancel", "")
    except Exception as e:
        callback("error", str(e))
