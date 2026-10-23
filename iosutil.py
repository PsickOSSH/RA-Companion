"""iOS helpers: safe-area margins and device language."""

from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import platform


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

