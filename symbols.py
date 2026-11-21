"""Symbols and emoji on Linux.

Tk cannot draw the colour emoji of a Linux system (empty squares). The desktop version therefore carries the monochrome
font *Noto Emoji* (fonts/NotoEmoji.ttf, SIL Open Font License): it looks like the emoji of Windows (white pictograms) and is
registered in fontconfig when this module is imported, before the first window exists, so that Tk finds it. If the font
cannot be registered, every emoji is replaced by a plain symbol that the DejaVu Sans font contains (`LINUX_SYMBOLS`).
On Windows nothing is done.
"""

import os
import sys

FONT_FILE = "NotoEmoji.ttf"
SYMBOL_FAMILY = "Noto Emoji"


def _font_path():
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "fonts", FONT_FILE)


def register_font():
    """Make the bundled Noto Emoji font known to this process (fontconfig). Returns True when it worked."""
    if os.name == "nt":
        return False
    path = _font_path()
    if not os.path.exists(path):
        return False
    try:
        import ctypes
        fc = ctypes.CDLL("libfontconfig.so.1")
        fc.FcConfigAppFontAddFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        fc.FcConfigAppFontAddFile.restype = ctypes.c_int
        return bool(fc.FcConfigAppFontAddFile(None, path.encode()))
    except Exception:
        return False


FONT_OK = register_font()                   # True: the emoji are drawn with Noto Emoji; False: plain symbols are used

# Used only when Noto Emoji is not available
LINUX_SYMBOLS = {
    "🏆": "♛", "👥": "☻", "👤": "☺", "💬": "✉", "🌐": "⊕", "📝": "✎", "🔒": "⊗", "🔓": "⊙", "🏅": "✪", "🏷": "◈",
    "⏱": "◷", "📌": "⚑", "🔍": "⚲",
}


def sym(text):
    """`text` adapted to the system: on Linux the full-width plus (missing from the fonts) becomes "+", and the emoji become
    plain symbols when the Noto Emoji font could not be loaded. Unchanged on Windows."""
    if os.name == "nt" or not isinstance(text, str):
        return text
    text = text.replace("＋", "+").replace("️", "")   # U+FE0F asks for the coloured look of a symbol: useless here
    if not FONT_OK:
        for emoji, plain in LINUX_SYMBOLS.items():
            if emoji in text:
                text = text.replace(emoji, plain)
    return text
