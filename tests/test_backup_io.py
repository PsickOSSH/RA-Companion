import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backup_io
import features
import notes_io
import settings_io
import userskins

CFG = {"user": "u", "key": "SECRET", "interval": 60, "skin": "user_ocean", "win_geo": "1x1+0+0"}
SKIN = {"NAME": "Ocean", "ACCENT": "#112233", "RADIUS_CARD": 4}


class BackupTests(unittest.TestCase):
    def test_export_and_import(self):
        text = backup_io.export_text(CFG, {"5": " note ", "6": "  ", "format": "x"}, [SKIN])
        data = backup_io.parse("﻿" + text)
        self.assertEqual(data, {"settings": {"user": "u", "key": "SECRET", "interval": 60}, "skin": "user_ocean",
                                "skins": [SKIN], "notes": {"5": "note"}})
        folder = tempfile.mkdtemp()
        self.assertEqual(backup_io.install_skins(data["skins"], folder, "x"), ["user_ocean"])
        self.assertEqual(userskins.load(folder, "user_ocean"), SKIN)
        backup_io.install_skins([dict(SKIN, ACCENT="#000000")], folder, "x")          # same name: replaced
        self.assertEqual([v["ACCENT"] for _i, v, _p in userskins.listing(folder)], ["#000000"])

    def test_wrong_parts_are_left_out(self):
        data = backup_io.parse(json.dumps({"format": backup_io.FORMAT, "settings": [1], "skin": "../x",
                                           "skins": [{"NAME": "no color"}, 3, {"ACCENT": "red"}], "notes": ["a"]}))
        self.assertEqual(data, {"settings": {}, "skin": None, "skins": [], "notes": {}})

    def test_the_other_files_are_not_mixed_up(self):
        backup = backup_io.export_text(CFG, {"5": "note"}, [SKIN])
        for parse in (settings_io.parse, notes_io.parse_notes, features.parse_notes, userskins.parse):
            with self.assertRaises(ValueError):
                parse(backup)
        for text in ("", "{", "[]", settings_io.export_text(CFG), notes_io.export_text({"5": "n"}),
                     "[" * 100000, " " * (backup_io.MAX_FILE + 1)):
            with self.assertRaises(ValueError):
                backup_io.parse(text)


if __name__ == "__main__":
    unittest.main()
