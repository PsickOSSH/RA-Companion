"""Tests of updater.py (the network is replaced by fake answers). Run: python -m unittest discover -s tests"""

import os
import sys
import unittest
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import updater  # noqa: E402


def release(tag, assets=(), draft=False):
    return {"tag_name": tag, "draft": draft, "assets": [{"name": n, "browser_download_url": "https://dl/" + tag + "/" + n, "size": 1000} for n in assets]}


class PatchNotesTests(unittest.TestCase):
    BODY = ("## New\r\n\r\n- **Your own skins**: press `F1` or see [the guide](https://example.org/a)\r\n"
            "* second *item*\r\n<!-- hidden -->\r\n> Keys are in plain text.\r\n\r\n---\r\n"
            "**Full Changelog**: https://github.com/a/b/compare/v1...v2\r\n")

    def test_markdown_becomes_plain_blocks(self):
        self.assertEqual(updater.note_blocks(self.BODY), [
            ("title", "New"), ("bullet", "Your own skins: press F1 or see the guide"), ("bullet", "second item"),
            ("text", "Keys are in plain text.")])

    def test_a_body_with_only_the_changelog_link_has_no_note(self):
        for body in ("Full Changelog: https://github.com/a/b/compare/v1...v2",
                     "Full Changelog:\nhttps://github.com/a/b/compare/v1...v2", "", None):
            self.assertEqual(updater.note_blocks(body), [], repr(body))

    def test_names_with_stars_or_underscores_stay(self):
        self.assertEqual(updater.note_blocks("set overlay_port in *.json files, 2 * 3"),
                         [("text", "set overlay_port in *.json files, 2 * 3")])

    def test_releases_are_sorted_by_version_and_drafts_are_left_out(self):
        data = [{"tag_name": "v1.9", "published_at": "2026-11-14T10:00:00Z", "body": "- a"},
                {"tag_name": "v1.10", "published_at": "2026-11-15T10:00:00Z", "body": "- b"},
                {"tag_name": "v3.0", "draft": True, "body": "- not yet"}, "noise"]
        notes = updater.release_notes("a/b", fetch=lambda url: data)
        self.assertEqual([(n["version"], n["date"]) for n in notes], [("1.10", "2026-11-15"), ("1.9", "2026-11-14")])
        self.assertEqual(notes[0]["blocks"], [("bullet", "b")])

    def test_an_unexpected_answer_is_an_error(self):
        with self.assertRaises(ValueError):
            updater.release_notes("a/b", fetch=lambda url: {"message": "Not Found"})


class UpdaterTests(unittest.TestCase):
    def test_version_parsing(self):
        self.assertEqual(updater.parse_version("v1.2.3"), (1, 2, 3))
        self.assertGreater(updater.parse_version("1.10.0"), updater.parse_version("1.9.9"))   # not a text comparison
        self.assertEqual(updater.parse_version("v2.0.0-beta1"), (2, 0, 0))
        self.assertEqual(updater.parse_version("nightly"), (0,))

    def test_repo_from_url(self):
        self.assertEqual(updater.repo_from_url("https://github.com/PsickOSSH/RA-Companion"), "PsickOSSH/RA-Companion")
        self.assertEqual(updater.repo_from_url("https://github.com/a/b.git"), "a/b")
        self.assertIsNone(updater.repo_from_url("https://example.org"))

    def test_newer_release_with_an_apk(self):
        data = [release("v1.1.0", ["RACompanion.exe"]), release("v1.0.5", ["app.apk"]), release("v1.0.9", ["RACompanion.exe", "app-1.0.9.apk"])]
        res = updater.check("a/b", "1.0.0", fetch=lambda url: data)
        self.assertEqual((res["status"], res["version"]), ("newer", "1.0.9"))        # v1.1.0 has no apk: ignored
        self.assertEqual(res["url"], "https://dl/v1.0.9/app-1.0.9.apk")

    def test_up_to_date_and_drafts(self):
        data = [release("v2.0.0", ["x.apk"], draft=True), release("v1.0.0", ["x.apk"])]
        self.assertEqual(updater.check("a/b", "1.0.0", fetch=lambda url: data)["status"], "uptodate")
        self.assertEqual(updater.check("a/b", "v1.0.1", fetch=lambda url: data)["status"], "uptodate")

    def test_no_apk_and_bad_answers(self):
        self.assertEqual(updater.check("a/b", "1.0.0", fetch=lambda url: [release("v1.0.0", ["a.exe"])]), {"status": "noapk"})
        with self.assertRaises(ValueError):
            updater.check("a/b", "1.0.0", fetch=lambda url: {"message": "Not Found"})

    def test_error_texts(self):
        err = lambda code: urllib.error.HTTPError("u", code, "x", {}, None)
        self.assertIn("limit", updater.describe(err(403)))
        self.assertIn("not found", updater.describe(err(404)))
        self.assertEqual(updater.describe(urllib.error.URLError("offline")), "no connection")


if __name__ == "__main__":
    unittest.main()
