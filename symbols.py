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


CONF_TEMPLATE = """<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <include ignore_missing="yes">%s</include>
  <selectfont>
    <rejectfont><pattern><patelt name="color"><bool>true</bool></patelt></pattern></rejectfont>
  </selectfont>
</fontconfig>
"""


def reject_color_fonts():
    """Tell fontconfig to ignore colour fonts. A system with *Noto Color Emoji* (Debian, Ubuntu desktop...) otherwise draws the
    emoji as huge coloured pictures instead of the white pictograms of the bundled *Noto Emoji* font. FONTCONFIG_FILE must be
    set before fontconfig is first used by this process."""
    try:
        import tempfile
        base = os.environ.get("FONTCONFIG_FILE") or "/etc/fonts/fonts.conf"
        conf = CONF_TEMPLATE % base
        folder = os.path.join(os.path.expanduser("~"), ".cache", "ra-companion")
        try:
            os.makedirs(folder, exist_ok=True)
        except OSError:
            folder = tempfile.gettempdir()
        path = os.path.join(folder, "fonts.conf")
        with open(path, "w", encoding="utf-8") as f:
            f.write(conf)
        os.environ["FONTCONFIG_FILE"] = path
    except Exception:
        pass


def register_font():
    """Make the bundled Noto Emoji font known to this process (fontconfig). Returns True when it worked."""
    if os.name == "nt" or os.environ.get("RA_NO_EMOJI_FONT"):       # (the variable is a switch to find out a crash)
        return False
    path = _font_path()
    if not os.path.exists(path):
        return False
    reject_color_fonts()
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
