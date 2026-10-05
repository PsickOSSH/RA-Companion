"""RA Companion - live RetroAchievements progress tracker.

Run with:  python ra_companion.py

Requires Python 3.9+ and Tkinter (included in the official Windows installer of Python).
No third-party package is needed.

Project layout
--------------
ra_companion.py   entry point (this file)
app.py            main window and application logic
widgets.py        reusable widgets (rounded cards/buttons, tooltips, mixed-font labels)
ra_api.py         RetroAchievements Web API, HTTP downloads, translation
i18n.py           UI translations and language helpers
utils.py          formatting, achievement predicates and sorting
config.py         paths, constants and persistent settings
skins/            visual themes (one .py file per skin)
"""

from app import App


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
