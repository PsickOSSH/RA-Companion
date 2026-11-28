"""Tests of notes_io.py. Run: python -m unittest discover -s tests"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import features  # noqa: E402
import notes_io  # noqa: E402
import settings_io  # noqa: E402


class NotesIoTests(unittest.TestCase):
    def test_export_is_sorted_json_and_skips_empty_notes(self):
        text = notes_io.export_text({"10": "b", "2": "a\nline 2", "7": "  "})
        self.assertEqual(list(json.loads(text)), ["2", "10"])
        self.assertEqual(json.loads(text)["2"], "a\nline 2")

    def test_parse(self):
        self.assertEqual(notes_io.parse_notes('{"1": " x ", "2": ""}'), {"1": "x"})
        self.assertEqual(notes_io.parse_notes('{"notes": {"3": "y"}}'), {"3": "y"})
        for bad in ("[1, 2]", "not json", '{"1": ["list"]}'):
            with self.assertRaises(ValueError):
                notes_io.parse_notes(bad)

    def test_another_kind_of_file_is_not_a_notes_file(self):
        settings = settings_io.export_text({"user": "u", "key": "k", "interval": 30})
        skin = json.dumps({"NAME": "x", "ACCENT": "#112233"})
        for text in (settings, skin, '{"format": "x", "version": 1}', '{"-1": "a", "1.5": "b"}'):
            for parse in (notes_io.parse_notes, features.parse_notes):
                with self.assertRaises(ValueError):
                    parse(text)

    def test_entries_imported_by_mistake_are_dropped(self):
        stored = {"format": "ra-companion-settings", "version": "1", "42": "mine"}
        self.assertEqual(notes_io.clean(stored), {"42": "mine"})
        self.assertEqual(json.loads(notes_io.export_text(stored)), {"42": "mine"})
        self.assertEqual(notes_io.clean(["x"]), {})
        path = os.path.join(tempfile.mkdtemp(), "notes.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(stored, f)
        self.assertEqual(features.NotesStore(path).ids(), {"42"})

    def test_entries_to_choose_from(self):
        notes = {"30": "z" * 100, "2": "two\nlines", "7": "  ", "5": "five", "format": "x"}
        found = notes_io.entries(notes, {"5": "Beta", "30": "alpha"}, length=10)
        self.assertEqual(found, [("30", "alpha : " + "z" * 10 + "…"), ("5", "Beta : five"), ("2", "#2 : two lines")])
        self.assertEqual(notes_io.entries({}), [])

    def test_merge(self):
        mine = {"1": "same", "2": "mine", "4": ""}
        counts = notes_io.merge(mine, {"1": "same", "2": "theirs", "3": "new", "4": "filled"})
        self.assertEqual(counts, (2, 1, 1))                       # added 3 and 4, merged 2, unchanged 1
        self.assertEqual(mine["2"], "mine\n\ntheirs")
        self.assertEqual(notes_io.merge(mine, {"2": "theirs"}), (0, 0, 1))   # importing twice changes nothing


if __name__ == "__main__":
    unittest.main()
