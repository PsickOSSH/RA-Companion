"""Light skin (Paper Indigo): warm paper background, white cards, indigo accent.

Hover darkens the controls instead of lightening them (HOVER_TINT is black).
Any variable left out falls back to the default skin (see `default.py` for the documented list).
"""

NAME = "Light (Paper Indigo)"
AUTHOR = "RA Companion"

# ---- Typography -------------------------------------------------------------
FONT = "Segoe UI"
SYMBOL_FONT = "Segoe UI Symbol"

# ---- Surfaces ---------------------------------------------------------------
BACKGROUND = "#f6f3ee"
CARD = "#fffdfa"
CARD_ALT = "#ebe6dd"
CARD_LOCKED = "#ece8e1"
CARD_LOCKED_HOVER = "#e3ded5"

# ---- Text -------------------------------------------------------------------
TEXT = "#241f2e"
TEXT_MUTED = "#6b6475"
TEXT_ON_ACCENT = "#ffffff"

# ---- Accent and status colors -----------------------------------------------
ACCENT = "#5b4bdb"
SUCCESS = "#12806a"
INFO = "#1f6fd1"
WARNING = "#c2540a"
DANGER = "#c9283a"

# ---- Controls ---------------------------------------------------------------
CONTROL_HOVER = "#d6cfc2"
SCROLL_THUMB = "#c4bcad"
BAR_TRACK_ALT = "#ddd6c9"
HOVER_TINT = "#000000"  # buttons get darker on hover (light backgrounds)
HOVER_STRENGTH = 0.07
TOOLTIP_BG = "#fffdfa"
TOOLTIP_TEXT = "#241f2e"
TOOLTIP_BORDER = "#5b4bdb"

# ---- Shapes (corner radius in pixels) ---------------------------------------
RADIUS_PANEL = 16
RADIUS_CARD = 12
RADIUS_BUTTON = 10
RADIUS_BUTTON_LARGE = 12
RADIUS_TOAST = 18
