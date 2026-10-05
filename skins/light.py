"""Light skin: soft grey-blue background, white cards, amber accent.

Hover darkens the controls instead of lightening them (HOVER_TINT is black).
Any variable left out falls back to the default skin (see `default.py` for the documented list).
"""

NAME = "Light (Daylight)"
AUTHOR = "RA Companion"

# ---- Typography -------------------------------------------------------------
FONT = "Segoe UI"
SYMBOL_FONT = "Segoe UI Symbol"

# ---- Surfaces ---------------------------------------------------------------
BACKGROUND = "#eef1f6"
CARD = "#ffffff"
CARD_ALT = "#e2e7f0"
CARD_LOCKED = "#e6eaf2"
CARD_LOCKED_HOVER = "#dde3ee"

# ---- Text -------------------------------------------------------------------
TEXT = "#1b2233"
TEXT_MUTED = "#5d6778"
TEXT_ON_ACCENT = "#ffffff"

# ---- Accent and status colors -----------------------------------------------
ACCENT = "#ad6600"
SUCCESS = "#13845a"
INFO = "#1d5fd1"
WARNING = "#c2540a"
DANGER = "#c9283a"

# ---- Controls ---------------------------------------------------------------
CONTROL_HOVER = "#c8d0df"
SCROLL_THUMB = "#b4bdcf"
BAR_TRACK_ALT = "#d3d9e5"
HOVER_TINT = "#000000"             # buttons get darker on hover (light backgrounds)
HOVER_STRENGTH = 0.07
TOOLTIP_BG = "#ffffff"
TOOLTIP_TEXT = "#1b2233"
TOOLTIP_BORDER = "#ad6600"

# ---- Shapes (corner radius in pixels) ---------------------------------------
RADIUS_PANEL = 16
RADIUS_CARD = 12
RADIUS_BUTTON = 10
RADIUS_BUTTON_LARGE = 12
RADIUS_TOAST = 18
