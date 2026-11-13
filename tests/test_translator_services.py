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
        self.insecure_flags = []
        self.gets = []
        self.post_answer = {"translations": [{"text": "Salut"}]}
        self.get_answer = GOOGLE_OK
        patches = [mock.patch.object(translator, "post_json", side_effect=self.fake_post),
                   mock.patch.object(translator, "get_json", side_effect=self.fake_get),
                   mock.patch.object(translator.time, "sleep")]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def fake_post(self, url, payload, headers=None, timeout=15, insecure=False):
        self.posts.append((url, payload, headers or {}))
        self.insecure_flags.append(insecure)
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

    def test_invalid_certificate_option_is_passed_to_libretranslate_only(self):
        self.post_answer = {"translatedText": "Bonjour monde"}
        t = translator.Translator()
        t.configure(libre_url="https://trad.local", libre_insecure=True, deepl_key="abc:fx")
        t.test()
        self.assertEqual(self.insecure_flags, [False, True])         # DeepL (strict) then LibreTranslate (insecure)
        t.configure(libre_url="https://trad.local")
        self.insecure_flags.clear()
        t.translate("Hello again", "fr")
        self.assertEqual(self.insecure_flags, [False])

    def test_configure_from_reads_the_certificate_option(self):
        t = translator.Translator()
        t.configure_from({"libre_url": "x", "libre_insecure": True})
        self.assertTrue(t.libre_insecure)
        t.configure_from({})
        self.assertFalse(t.libre_insecure)

    def test_test_reports_every_service_without_the_cache(self):
        self.post_answer = {"translatedText": "Bonjour monde"}
        self.get_answer = http_error(429)
        t = translator.Translator()
        t.configure(libre_url="https://trad.local")
        t.cache[("fr", "Hello world")] = "from cache"
        results = t.test()
        self.assertEqual([r[0] for r in results], ["libretranslate", "google", "google-chrome", "mymemory"])
        self.assertEqual(results[0], ("libretranslate", True, "Bonjour monde"))
        self.assertEqual(results[1], ("google", False, "HTTP 429"))

    def test_error_descriptions_help_to_fix_the_address(self):
        self.assertIn("https://", translator._describe(http_error(308)))
        import ssl
        err = ssl.SSLCertVerificationError(1, "certificate verify failed")
        err.verify_message = "Hostname mismatch, certificate is not valid for 'trad.local'."
        text = translator._describe(urllib.error.URLError(err))
        self.assertIn("invalid certificate", text)
        self.assertIn("trad.local", text)


class InsecureContextTest(unittest.TestCase):
    def test_post_json_builds_an_unverified_context_only_when_asked(self):
        import ssl

        class Answer:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return b"{}"
        with mock.patch.object(translator.urllib.request, "urlopen", return_value=Answer()) as urlopen:
            translator.post_json("https://x/translate", {}, insecure=True)
            ctx = urlopen.call_args.kwargs["context"]
            self.assertEqual(ctx.verify_mode, ssl.CERT_NONE)
            self.assertFalse(ctx.check_hostname)
            translator.post_json("https://x/translate", {})
            strict = urlopen.call_args.kwargs.get("context")
            self.assertTrue(strict is None or strict.verify_mode != ssl.CERT_NONE)


if __name__ == "__main__":
    unittest.main()
