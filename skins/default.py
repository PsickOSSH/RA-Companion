"""Default skin: dark navy surfaces with a gold accent.

HOW TO CREATE YOUR OWN SKIN
---------------------------
1. Copy this file to `skins/my_skin.py` (any name that does not start with an underscore).
2. Change NAME (it is the label shown in Settings -> Skin) and any value below.
   Colors are "#rrggbb" strings.
3. Start the program, open Settings and pick your skin. The application restarts to apply it.

Only UPPER_CASE variables are read. Any variable you leave out falls back to the value
defined here, so a skin can override just a few colors.
"""

NAME = "Default (Midnight Gold)"   # label shown in the settings window
AUTHOR = "RA Companion"            # informational only

# ---- Typography -------------------------------------------------------------
FONT = "Segoe UI"                  # main UI font
SYMBOL_FONT = "Segoe UI Symbol"    # font used for every emoji / symbol / icon

# ---- Surfaces ---------------------------------------------------------------
BACKGROUND = "#0f1420"             # window background
CARD = "#1a2133"                   # profile card, game card, unlocked achievements
CARD_ALT = "#222c43"               # buttons, inactive chips, hover color of cards
CARD_LOCKED = "#141a29"            # achievements that are not unlocked yet
CARD_LOCKED_HOVER = "#1c2438"      # same, while the mouse is over it

# ---- Text -------------------------------------------------------------------
TEXT = "#e8ecf5"                   # main text
TEXT_MUTED = "#8a94ab"             # secondary text (descriptions, hints)
TEXT_ON_ACCENT = "#1a1300"         # text drawn on top of an ACCENT-colored button

# ---- Accent and status colors -----------------------------------------------
ACCENT = "#f5b942"                 # active buttons / chips, points, progress bar
SUCCESS = "#3ddc97"                # unlocked, softcore mode, completed progress
INFO = "#6ab0ff"                   # hardcore mode, links, friend in the duel view
WARNING = "#ff9f43"                # "missable" markers
DANGER = "#ff6b6b"                 # errors, delete actions

# ---- Controls ---------------------------------------------------------------
CONTROL_HOVER = "#34426a"          # combobox arrow while hovered
SCROLL_THUMB = "#3a4766"           # scrollbar handle and dropdown borders
BAR_TRACK_ALT = "#2a3550"          # empty part of progress bars drawn on non-CARD backgrounds
HOVER_TINT = "#ffffff"             # buttons are blended towards this color on hover...
HOVER_STRENGTH = 0.16              # ...by this amount (0 = no effect, 1 = fully tinted)
TOOLTIP_BG = "#222c43"             # tooltip background (same family as the buttons)
TOOLTIP_TEXT = "#e8ecf5"           # tooltip text
TOOLTIP_BORDER = "#f5b942"         # thin outline around the tooltip

# ---- Shapes (corner radius in pixels) ---------------------------------------
RADIUS_PANEL = 16                  # profile card, game card, achievement header
RADIUS_CARD = 12                   # achievement rows and player rows
RADIUS_BUTTON = 10                 # buttons and filter chips
RADIUS_BUTTON_LARGE = 12           # tabs and the big "Save" / "Track this game" buttons
RADIUS_TOAST = 18                  # unlock notification
