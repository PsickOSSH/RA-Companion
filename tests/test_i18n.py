"""Checks that every text used by main.py / main.kv exists in the 6 languages, with the same placeholders.
    python -m unittest discover -s tests
"""

import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from uitext import MOBILE  # noqa: E402  (mobile_i18n.MOBILE + the texts added in uitext.py)

LANGS = ["en", "fr", "es", "de", "it", "pt"]


def placeholders(text):
    return sorted(re.findall(r"\{(\w+)\}", text))


class TranslationTests(unittest.TestCase):
    def test_all_languages_have_the_same_keys_and_placeholders(self):
        for lang in LANGS:
            self.assertEqual(set(MOBILE[lang]), set(MOBILE["en"]), lang)
            for key, text in MOBILE[lang].items():
                self.assertEqual(placeholders(text), placeholders(MOBILE["en"][key]), f"{lang}.{key}")

    def test_every_key_used_in_the_code_exists(self):
        src = ""
        for name in ("main.py", "main.kv", "uitext.py"):
            with open(os.path.join(ROOT, name), encoding="utf-8") as f:
                src += f.read()
        used = set(re.findall(r"\btr\(\s*['\"](\w+)['\"]", src))
        used |= {"sort_" + sid for sid in ("unlocked_first", "disp_asc", "disp_desc", "awd_desc", "awd_asc", "pts_desc", "pts_asc", "title_asc", "title_desc", "type_asc", "type_desc")}
        used = {k for k in used if not k.endswith("_")}
        self.assertEqual(sorted(used - set(MOBILE["en"])), [])


if __name__ == "__main__":
    unittest.main()
