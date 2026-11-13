"""DeepL / LibreTranslate and the preferred service of translator.py (the network is replaced by fake answers)."""

import os
import sys
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import translator  # noqa: E402


def http_error(code):
    return urllib.error.HTTPError("http://x", code, "err", {}, None)


GOOGLE_OK = [[["Bonjour", "Hello", None]], None, "en"]


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.posts = []
        self.gets = []
        self.post_answer = {"translations": [{"text": "Salut"}]}
        self.get_answer = GOOGLE_OK
        patches = [mock.patch.object(translator, "post_json", side_effect=self.fake_post),
                   mock.patch.object(translator, "get_json", side_effect=self.fake_get),
                   mock.patch.object(translator.time, "sleep")]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def fake_post(self, url, payload, headers=None, timeout=15):
        self.posts.append((url, payload, headers or {}))
        if isinstance(self.post_answer, Exception):
            raise self.post_answer
        return self.post_answer

    def fake_get(self, url, timeout=15):
        self.gets.append(url)
        if isinstance(self.get_answer, Exception):
            raise self.get_answer
        return self.get_answer

    def names(self, t):
        return [name for name, _fn in t.chain()]

    def test_default_chain_is_unchanged_without_keys(self):
        self.assertEqual(self.names(translator.Translator()), ["google", "google-chrome", "mymemory"])

    def test_deepl_is_first_when_a_key_is_given(self):
        t = translator.Translator()
        t.configure(deepl_key="abc:fx")
        self.assertEqual(self.names(t)[0], "deepl")
        self.assertEqual(t.translate("Hello", "fr"), "Salut")
        url, payload, headers = self.posts[0]
        self.assertEqual(url, "https://api-free.deepl.com/v2/translate")
        self.assertEqual(payload, {"text": ["Hello"], "target_lang": "FR"})
        self.assertEqual(headers["Authorization"], "DeepL-Auth-Key abc:fx")
        self.assertEqual(t.last_used, "deepl")
        self.assertEqual(self.gets, [])

    def test_deepl_paid_server_and_language_codes(self):
        t = translator.Translator()
        t.configure(deepl_key="paidkey")
        for lang, expected in (("en", "EN-US"), ("pt", "PT-PT"), ("zh-CN", "ZH"), ("de", "DE")):
            t.translate("Hello " + lang, lang)
            self.assertEqual(self.posts[-1][1]["target_lang"], expected)
        self.assertEqual(self.posts[0][0], "https://api.deepl.com/v2/translate")

    def test_falls_back_when_deepl_fails(self):
        self.post_answer = http_error(456)                       # quota exceeded
        t = translator.Translator()
        t.configure(deepl_key="abc:fx")
        self.assertEqual(t.translate("Hello", "fr"), "Bonjour")
        self.assertEqual(t.last_used, "google")
        self.assertEqual(t._good, 1)                             # automatic mode remembers that Google works
        t.translate("Another", "fr")
        self.assertEqual(len(self.posts), 1)                     # DeepL is not tried again for every text

    def test_libretranslate(self):
        self.post_answer = {"translatedText": "Hola"}
        t = translator.Translator()
        t.configure(libre_url="libre.example.org/", libre_key="K")
        self.assertEqual(self.names(t)[0], "libretranslate")
        self.assertEqual(t.translate("Hello", "es"), "Hola")
        url, payload, _headers = self.posts[0]
        self.assertEqual(url, "https://libre.example.org/translate")
        self.assertEqual(payload["api_key"], "K")
        self.assertEqual(payload["target"], "es")
        t.translate("Hello 2", "zh-CN")
        self.assertEqual(self.posts[-1][1]["target"], "zh-Hans")

    def test_libretranslate_without_key_and_error_answer(self):
        t = translator.Translator()
        t.configure(libre_url="http://192.168.1.5:5000")
        self.post_answer = {"error": "Too many requests"}
        self.assertEqual(t.translate("Hello", "fr"), "Bonjour")      # falls back to Google
        url, payload, _headers = self.posts[0]
        self.assertEqual(url, "http://192.168.1.5:5000/translate")
        self.assertNotIn("api_key", payload)

    def test_preferred_service_goes_first_and_is_always_tried_first(self):
        t = translator.Translator()
        t.configure(service="google", deepl_key="abc:fx")
        self.assertEqual(self.names(t), ["google", "google-chrome", "deepl", "mymemory"])
        t.translate("Hello", "fr")
        t.translate("Hello again", "fr")
        self.assertEqual(self.posts, [])
        t.configure(service="mymemory")
        self.assertEqual(self.names(t)[0], "mymemory")

    def test_preferred_service_without_key_is_ignored(self):
        t = translator.Translator()
        t.configure(service="deepl")
        self.assertEqual(self.names(t), ["google", "google-chrome", "mymemory"])

    def test_unknown_service_means_auto(self):
        t = translator.Translator()
        t.configure(service="bing", deepl_key="k")
        self.assertEqual(t.service, "auto")

    def test_configure_from_settings_dictionary(self):
        t = translator.Translator()
        t.configure_from({"tr_service": "deepl", "deepl_key": " k:fx ", "libre_url": "", "libre_key": None})
        self.assertEqual((t.service, t.deepl_key, t.libre_url, t.libre_key), ("deepl", "k:fx", "", ""))
        t.configure_from({})
        self.assertEqual((t.service, t.deepl_key), ("auto", ""))

    def test_all_services_fail_lists_every_cause(self):
        self.post_answer = http_error(403)
        self.get_answer = urllib.error.URLError("offline")
        t = translator.Translator()
        t.configure(deepl_key="bad:fx")
        with self.assertRaises(translator.TranslateError) as ctx:
            t.translate("Hello", "fr")
        self.assertIn("deepl: HTTP 403", str(ctx.exception))
        self.assertIn("mymemory", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
