import json
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import config
import settings_io


def desktop_defaults():
    old = config.CONFIG_FILE
    config.CONFIG_FILE = os.path.join(ROOT, "no_such_configuration.json")
    try:
        return config.load_cfg()
    finally:
        config.CONFIG_FILE = old


class SettingsFileTests(unittest.TestCase):
    def test_every_setting_of_both_apps_is_covered(self):
        with open(os.path.join(ROOT, "main.py"), encoding="utf-8") as f:
            block = re.search(r"CFG_DEFAULTS = \{(.*?)\}\n", f.read(), re.S).group(1)
        names = set(desktop_defaults()) | set(re.findall(r'"(\w+)":', block))
        self.assertEqual(sorted(names - set(settings_io.RULES) - set(settings_io.EXCLUDED)), [])

    def test_the_defaults_are_valid(self):
        defaults = desktop_defaults()
        kept = settings_io.valid(defaults)
        self.assertEqual(sorted(set(defaults) - set(kept)), sorted(settings_io.EXCLUDED))

    def test_export_and_import(self):
        cfg = dict(desktop_defaults(), user="Nom é", key="SECRET", interval=45, group=["A", "B"], skin="user_x",
                   win_geo="1x1+0+0", refresh_key="F5", ai_services=[{"url": "u", "model": "m", "key": "k"}], other=1)
        text = settings_io.export_text(cfg)
        settings = settings_io.parse("﻿" + text)
        for name in ("user", "key", "interval", "group", "refresh_key", "ai_services"):
            self.assertEqual(settings[name], cfg[name], name)
        for name in ("skin", "win_geo", "other"):
            self.assertNotIn(name, settings)
        self.assertNotIn("user_x", text)

    def test_wrong_values_are_left_out(self):
        wrong = {"user": 3, "interval": 1, "alpha": 0, "hc_only": "yes", "game_id": "../x", "ui_lang": "<x>", "sort": "zzz",
                 "overlay_port": True, "refresh_key": "a", "group": ["ok", 2], "ai_services": [1], "skin": "default",
                 "deepl_key": "x" * 600, "friend": "Bob"}
        self.assertEqual(settings_io.valid(wrong), {"friend": "Bob", "refresh_key": "a"})
        self.assertEqual(settings_io.valid({"refresh_key": "<Delete>"}), {})

    def test_reset(self):
        defaults = desktop_defaults()
        cfg = dict(defaults, user="u", key="k", deepl_key="d", interval=90, sort="pts_desc", skin="dark", win_geo="g",
                   group=["a"], unknown=1)
        settings_io.reset(cfg, defaults, keep_account=True)
        self.assertEqual((cfg["user"], cfg["key"], cfg["deepl_key"], cfg["interval"], cfg["group"]), ("u", "k", "", 30, []))
        self.assertNotIn("sort", cfg)
        self.assertEqual((cfg["skin"], cfg["win_geo"], cfg["unknown"]), ("dark", "g", 1))
        cfg["group"].append("x")
        self.assertEqual(defaults["group"], [])                # the defaults are copied
        settings_io.reset(cfg, defaults, keep_account=False)
        self.assertEqual((cfg["user"], cfg["key"], cfg["deepl_key"], cfg["group"], cfg["skin"]), ("", "", "", [], "dark"))

    def test_files_that_are_not_settings(self):
        notes = json.dumps({"12": "a note"})
        empty = json.dumps({"format": settings_io.FORMAT, "settings": {"zzz": 1}})
        for text in ("", "{", "[]", notes, empty, "[" * 100000, " " * (settings_io.MAX_FILE + 1)):
            with self.assertRaises(ValueError):
                settings_io.parse(text)


if __name__ == "__main__":
    unittest.main()
