"""Tests of notes_io.py. Run: python -m unittest discover -s tests"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import notes_io  # noqa: E402


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

    def test_merge(self):
        mine = {"1": "same", "2": "mine", "4": ""}
        counts = notes_io.merge(mine, {"1": "same", "2": "theirs", "3": "new", "4": "filled"})
        self.assertEqual(counts, (2, 1, 1))                       # added 3 and 4, merged 2, unchanged 1
        self.assertEqual(mine["2"], "mine\n\ntheirs")
        self.assertEqual(notes_io.merge(mine, {"2": "theirs"}), (0, 0, 1))   # importing twice changes nothing


if __name__ == "__main__":
    unittest.main()
