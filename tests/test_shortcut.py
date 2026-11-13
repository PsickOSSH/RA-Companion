import unittest

import hotkey
import utils

SHIFT, CTRL, ALT = 0x1, 0x4, 0x20000


class ShortcutTest(unittest.TestCase):
    def test_function_keys_are_allowed(self):
        self.assertEqual(utils.shortcut_from_key("F1", 0), "F1")
        self.assertEqual(utils.shortcut_from_key("F12", 0), "F12")
        self.assertEqual(utils.shortcut_from_key("F5", CTRL), "Control-F5")
        self.assertEqual(utils.shortcut_from_key("F2", SHIFT | ALT), "Alt-Shift-F2")

    def test_function_keys_out_of_range_are_refused(self):
        self.assertIsNone(utils.shortcut_from_key("F13", 0))
        self.assertIsNone(utils.shortcut_from_key("F0", 0))
        self.assertIsNone(utils.shortcut_from_key("Fx", 0))

    def test_letter_needs_ctrl_or_alt(self):
        self.assertIsNone(utils.shortcut_from_key("r", 0))
        self.assertIsNone(utils.shortcut_from_key("r", SHIFT))
        self.assertEqual(utils.shortcut_from_key("r", CTRL), "Control-r")
        self.assertEqual(utils.shortcut_from_key("R", CTRL), "Control-r")
        self.assertEqual(utils.shortcut_from_key("4", ALT), "Alt-4")
        self.assertEqual(utils.shortcut_from_key("r", CTRL | ALT), "Control-Alt-r")

    def test_ctrl_shift_letter_and_other_keys_are_refused(self):
        self.assertIsNone(utils.shortcut_from_key("r", CTRL | SHIFT))
        for key in ("Tab", "Escape", "Return", "space", "Left", "é"):
            self.assertIsNone(utils.shortcut_from_key(key, CTRL), key)

    def test_modifier_alone_is_ignored(self):
        for key in ("Control_L", "Shift_R", "Alt_L"):
            self.assertIsNone(utils.shortcut_from_key(key, CTRL))

    def test_label(self):
        self.assertEqual(utils.shortcut_label("F1"), "F1")
        self.assertEqual(utils.shortcut_label("Control-r"), "Ctrl+R")
        self.assertEqual(utils.shortcut_label("Control-Alt-Shift-F5"), "Ctrl+Alt+Shift+F5")
        self.assertEqual(utils.shortcut_label(""), utils.shortcut_label(utils.DEFAULT_REFRESH_KEY))

    def test_default_is_not_a_function_key(self):
        self.assertFalse(utils.DEFAULT_REFRESH_KEY.split("-")[-1].startswith("F"))
        self.assertIsNotNone(hotkey.parse(utils.DEFAULT_REFRESH_KEY))


class HotkeyParseTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(hotkey.parse("F1"), (0, 0x70))
        self.assertEqual(hotkey.parse("F12"), (0, 0x7B))
        self.assertEqual(hotkey.parse("Control-Alt-r"), (0x2 | 0x1, ord("R")))
        self.assertEqual(hotkey.parse("Alt-Shift-4"), (0x1 | 0x4, ord("4")))

    def test_parse_refuses_unsupported(self):
        for seq in ("Space", "F13", "Foo-r", "Control-", "", "Control-é"):
            self.assertIsNone(hotkey.parse(seq), seq)

    def test_every_allowed_shortcut_can_be_registered(self):
        for keysym, state in (("F1", 0), ("F12", 0x4), ("a", 0x4), ("9", 0x20000), ("z", 0x4 | 0x20000)):
            self.assertIsNotNone(hotkey.parse(utils.shortcut_from_key(keysym, state)), keysym)


if __name__ == "__main__":
    unittest.main()
