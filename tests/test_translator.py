"""Tests of translator.py (the network is replaced by fake answers). Run: python -m unittest discover -s tests"""

import os
import sys
import tempfile
import unittest
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import translator  # noqa: E402


def http_error(code):
    return urllib.error.HTTPError("http://x", code, "err", {}, None)


class TranslatorTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.answers = {}
        self.old_get, self.old_backends = translator.get_json, translator.BACKENDS
        translator.get_json = self.fake_get
        translator.time.sleep = lambda s: None

    def tearDown(self):
        translator.get_json = self.old_get

    def fake_get(self, url, timeout=15):
        self.calls.append(url)
        for prefix, answer in self.answers.items():
            if url.startswith(prefix):
                if isinstance(answer, Exception):
                    raise answer
                return answer
        raise AssertionError("unexpected url " + url)

    def test_google_answer_is_joined_and_cached(self):
        self.answers["https://translate.googleapis.com"] = [[["Bonjour ", "Hello ", None], ["le monde", "world", None]], None, "en"]
        t = translator.Translator()
        self.assertEqual(t.translate("Hello world", "fr"), "Bonjour le monde")
        self.assertEqual(t.translate("Hello world", "fr"), "Bonjour le monde")
        self.assertEqual(len(self.calls), 1)                               # second call comes from the cache

    def test_falls_back_to_the_next_endpoint(self):
        self.answers["https://translate.googleapis.com"] = http_error(429)
        self.answers["https://clients5.google.com"] = {"sentences": [{"trans": "Hola", "orig": "Hello"}], "src": "en"}
        t = translator.Translator()
        self.assertEqual(t.translate("Hello", "es"), "Hola")
        self.assertEqual(t._good, 1)                                       # the working endpoint is tried first next time
        t.translate("Another text", "es")
        self.assertTrue(self.calls[-1].startswith("https://clients5.google.com"))

    def test_mymemory_and_list_answers(self):
        self.answers["https://translate.googleapis.com"] = urllib.error.URLError("offline")
        self.answers["https://clients5.google.com"] = [["Ciao", "en"]]
        self.assertEqual(translator.Translator().translate("Hello", "it"), "Ciao")
        self.answers["https://clients5.google.com"] = http_error(403)
        self.answers["https://api.mymemory.translated.net"] = {"responseData": {"translatedText": "Hallo"}, "responseStatus": 200}
        self.assertEqual(translator.Translator().translate("Hello", "de"), "Hallo")

    def test_all_endpoints_fail_with_a_readable_error_and_a_pause(self):
        for prefix in ("https://translate.googleapis.com", "https://clients5.google.com", "https://api.mymemory.translated.net"):
            self.answers[prefix] = http_error(429)
        t = translator.Translator()
        with self.assertRaises(translator.TranslateError) as cm:
            t.translate("Hello", "fr")
        self.assertIn("HTTP 429", str(cm.exception))
        self.assertFalse(t.pending("fr", "Hello"))                          # not retried at once...
        t.reset_failures()
        self.assertTrue(t.pending("fr", "Hello"))                           # ...but the button gives it another chance

    def test_translate_many_sets_last_error_only_when_nothing_worked(self):
        self.answers["https://translate.googleapis.com"] = [[["X", "x", None]], None, "en"]
        t = translator.Translator()
        self.assertEqual(t.translate_many(["a", "b", "a", ""], "fr"), (2, 0))
        self.assertEqual(t.last_error, "")
        for prefix in ("https://translate.googleapis.com", "https://clients5.google.com", "https://api.mymemory.translated.net"):
            self.answers[prefix] = http_error(500)
        done, failed = t.translate_many(["c", "d"], "fr")
        self.assertEqual((done, failed), (0, 2))
        self.assertIn("HTTP 500", t.last_error)

    def test_cache_file(self):
        path = os.path.join(tempfile.mkdtemp(), "tr.json")
        self.answers["https://translate.googleapis.com"] = [[["Salut", "Hi", None]], None, "en"]
        t = translator.Translator(path)
        t.translate_many(["Hi"], "fr")
        again = translator.Translator(path)
        self.assertEqual(again.cached("fr", "Hi"), "Salut")
        self.assertEqual(again.cached("fr", "unknown"), "unknown")
        self.assertFalse(again.pending("fr", "Hi"))


if __name__ == "__main__":
    unittest.main()
