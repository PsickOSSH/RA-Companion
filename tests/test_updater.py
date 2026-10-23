"""Tests of updater.py (the network is replaced by fake answers). Run: python -m unittest discover -s tests"""

import os
import sys
import unittest
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import updater  # noqa: E402


def release(tag, assets=(), draft=False):
    return {"tag_name": tag, "draft": draft, "assets": [{"name": n, "browser_download_url": "https://dl/" + tag + "/" + n, "size": 1000} for n in assets]}


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
