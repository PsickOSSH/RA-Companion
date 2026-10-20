import unittest

import desktop_texts
import i18n


class DesktopTextsTests(unittest.TestCase):
    def test_every_language_has_every_english_text(self):
        english = set(i18n.I18N["en"])
        for lang, texts in i18n.I18N.items():
            self.assertEqual(sorted(english - set(texts)), [], lang)