"""iOS helpers: safe-area margins, device language, clipboard, web links and the document window ("Files")."""

import os
import shutil
import tempfile

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import platform

MAX_FILE = 5_000_000          # bytes: a larger file is refused (the limit of the Android reader)
# UIDocumentPickerMode: "import" gives the app its own copy of the chosen file, "export" copies a file of the app to the
# place chosen by the user
_MODE_IMPORT, _MODE_EXPORT = 0, 2
_delegate = None              # receives the answers of the document window; kept here, iOS does not keep it alive


def safe_area():
    """Return (left, top, right, bottom) margins in Kivy pixels."""
    if platform != "ios":
        return 0, 0, 0, 0
    if Window.width > Window.height:
        return dp(48), 0, dp(48), dp(21)
    return 0, dp(48), 0, dp(34)


def device_language():
    """Two-letter language of the device ('fr', 'en', ...), or '' when unknown."""
    if platform != "ios":
        return ""
    try:
        from pyobjus import autoclass
        langs = autoclass("NSLocale").preferredLanguages()
        first = langs.objectAtIndex_(0).UTF8String()
        if isinstance(first, bytes):
            first = first.decode("utf-8")
        return str(first).replace("_", "-").split("-")[0].lower()
    except Exception as exc:
        print(f"[iosutil] language lookup failed: {exc!r}", flush=True)
        return ""


def clipboard_copy(text):
    """Put `text` in the iOS system pasteboard (falls back to Kivy's clipboard)."""
    text = str(text or "")
    if platform == "ios":
        try:
            from pyobjus import autoclass, objc_str
            board = autoclass("UIPasteboard").generalPasteboard()
            board.setString_(objc_str(text))
            return True
        except Exception as exc:
            print(f"[iosutil] pasteboard copy failed: {exc!r}", flush=True)
    try:
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(text)
        return True
    except Exception as exc:
        print(f"[iosutil] kivy copy failed: {exc!r}", flush=True)
        return False


def clipboard_paste():
    """Text of the iOS system pasteboard ('' when empty)."""
    if platform == "ios":
        try:
            from pyobjus import autoclass
            board = autoclass("UIPasteboard").generalPasteboard()
            value = board.string()
            if value is not None:
                text = value.UTF8String()
                if isinstance(text, bytes):
                    text = text.decode("utf-8", "replace")
                return str(text or "")
            return ""
        except Exception as exc:
            print(f"[iosutil] pasteboard paste failed: {exc!r}", flush=True)
    try:
        from kivy.core.clipboard import Clipboard
        return Clipboard.paste() or ""
    except Exception as exc:
        print(f"[iosutil] kivy paste failed: {exc!r}", flush=True)
        return ""


# ---- document window -------------------------------------------------------------------------------
# UIDocumentPickerViewController, with the calls that exist since iOS 8 (iOS 14 added others, but the app supports
# iOS 12): nothing to add to the Xcode project, the window is part of UIKit.

def _value(obj, name):
    """A property of an iOS object. pyobjus gives either its value or a method to call, according to the real class of
    the object."""
    value = getattr(obj, name)
    return value() if callable(value) else value


def _text(string):
    value = _value(string, "UTF8String")
    if isinstance(value, bytes):
        value = value.decode("utf-8", "replace")
    return str(value or "")


def _failure(exc):
    return f"{exc.__class__.__name__}: {exc}"


def _answer(callback, status, text):
    """Give the answer on the next Kivy frame, once the system window has returned."""
    Clock.schedule_once(lambda dt: callback(status, text))


def _document_delegate():
    """The object told by iOS that a document was chosen or that the window was cancelled."""
    global _delegate
    if _delegate is None:
        from pyobjus import protocol
        from pyobjus.protocols import protocols
        # the types of the two methods, used by pyobjus when iOS does not describe this protocol itself
        protocols.setdefault("UIDocumentPickerDelegate", {
            "documentPicker:didPickDocumentsAtURLs:": ("v16@0:4@8@12", "v32@0:8@16@24"),
            "documentPickerWasCancelled:": ("v12@0:4@8", "v24@0:8@16")})

        class DocumentDelegate:
            done = None                    # done(url or None) of the window now open
            picker = None

            def finish(self, url):
                done, self.done, self.picker = self.done, None, None
                if done:
                    done(url)

            @protocol("UIDocumentPickerDelegate")
            def documentPicker_didPickDocumentsAtURLs_(self, picker, urls):
                try:
                    url = _value(urls, "firstObject")
                except Exception as exc:
                    print(f"[iosutil] no chosen document: {exc!r}", flush=True)
                    url = None
                self.finish(url)

            @protocol("UIDocumentPickerDelegate")
            def documentPickerWasCancelled_(self, picker):
                self.finish(None)

        _delegate = DocumentDelegate()
    return _delegate


def _top_controller():
    """The view controller on screen, from which a system window can be shown."""
    from pyobjus import autoclass
    application = autoclass("UIApplication").sharedApplication()
    window = _value(application, "keyWindow")
    if window is None:
        window = _value(_value(application, "windows"), "firstObject")
    controller = _value(window, "rootViewController")
    while True:
        above = _value(controller, "presentedViewController")
        if above is None:
            return controller
        controller = above


def _show_picker(make, done):
    """Show the document window built by `make(new picker)`; `done(url)` is called when it closes (None: cancelled)."""
    from pyobjus import autoclass
    delegate = _document_delegate()
    picker = make(autoclass("UIDocumentPickerViewController").alloc())
    picker.setDelegate_(delegate)
    delegate.done, delegate.picker = done, picker
    _top_controller().presentViewController_animated_completion_(picker, True, None)


def _read_document(url):
    """(status, text) of the chosen document."""
    try:
        # needed for a document that stays outside the app; True means that the access must be given back
        scoped = url.startAccessingSecurityScopedResource()
        try:
            path = _text(_value(url, "path"))
            with open(path, "rb") as f:
                data = f.read(MAX_FILE + 1)
            _remove_copy(path)
        finally:
            if scoped:
                url.stopAccessingSecurityScopedResource()
        if len(data) > MAX_FILE:
            return "error", f"file larger than {MAX_FILE // 1_000_000} MB"
        return "ok", data.decode("utf-8-sig", "replace")
    except Exception as exc:
        return "error", _failure(exc)


def _remove_copy(path):
    """Delete the copy iOS made for the app (it may hold keys). Only a file of the temporary folder of the app is
    deleted, never a document of the user."""
    temporary = os.path.realpath(tempfile.gettempdir()) + os.sep
    if os.path.realpath(path).startswith(temporary):
        try:
            os.remove(path)
        except OSError as exc:
            print(f"[iosutil] copy not removed: {exc!r}", flush=True)


def open_file(extension, callback):
    """Let the user choose a ".json" or ".py" file; callback(status, text), status 'ok', 'cancel' or 'error'."""
    try:
        from pyobjus import autoclass, objc_str
        kind = "public.json"
        if extension == ".py":
            # iOS knows the type of the Python files for sure since version 14; before, any file can be chosen
            version = _text(_value(autoclass("UIDevice").currentDevice(), "systemVersion"))
            kind = "public.python-script" if int(version.split(".")[0]) >= 14 else "public.data"
        types = autoclass("NSArray").arrayWithObject_(objc_str(kind))

        def done(url):
            _answer(callback, *(("cancel", "") if url is None else _read_document(url)))
        _show_picker(lambda new: new.initWithDocumentTypes_inMode_(types, _MODE_IMPORT), done)
    except Exception as exc:
        callback("error", _failure(exc))


def save_file(filename, text, callback):
    """Let the user choose where to save `text`, under the proposed name; callback(status, info) like open_file."""
    folder = os.path.join(tempfile.gettempdir(), "ra_companion_export")

    def clean():
        shutil.rmtree(folder, ignore_errors=True)        # the file may hold keys: it does not stay in the app

    try:
        from pyobjus import autoclass, objc_str
        clean()                                          # of an export whose window gave no answer
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        source = autoclass("NSURL").fileURLWithPath_(objc_str(path))

        def done(url):
            clean()                                      # iOS has made its copy
            _answer(callback, "cancel" if url is None else "ok", "")
        _show_picker(lambda new: new.initWithURL_inMode_(source, _MODE_EXPORT), done)
    except Exception as exc:
        clean()
        callback("error", _failure(exc))


def open_url(url):
    """Open a web address in Safari (iOS). Returns True when the request was handed to the system."""
    if platform != "ios":
        return False
    try:
        from pyobjus import autoclass, objc_str
        nsurl = autoclass("NSURL").URLWithString_(objc_str(str(url)))
        app = autoclass("UIApplication").sharedApplication()
        options = autoclass("NSDictionary").dictionary()
        app.openURL_options_completionHandler_(nsurl, options, None)
        return True
    except Exception as exc:
        print(f"[iosutil] open_url failed: {exc!r}", flush=True)
        return False