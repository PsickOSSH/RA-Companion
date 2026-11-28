import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import skins
import themes
import userskins

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIN = '''"""My skin."""
NAME = "Océan  bleu"
ACCENT = "#112233"
CARD = "#223344"
HOVER_STRENGTH = 0.2
RADIUS_CARD = 8
'''


class UserSkinTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()

    def test_nothing_of_the_file_is_run(self):
        witness = os.path.join(self.folder, "run.txt")
        code = ('import os\nopen(%r, "w").write("x")\nACCENT = "#112233"\n'
                'CARD = open(%r, "w") and "#000000"\nTEXT = __import__("os").getcwd()\n') % (witness, witness)
        self.assertEqual(userskins.parse(code), {"ACCENT": "#112233"})
        userskins.install(code, self.folder, "x")
        self.assertFalse(os.path.exists(witness))

    def test_wrong_values_are_left_out(self):
        values = userskins.parse('ACCENT = "red"\nCARD = "#223344"\nRADIUS_CARD = 900\nRADIUS_PANEL = True\n'
                                 'HOVER_STRENGTH = "a"\nFONT = 3\nOTHER = "#000000"\nTEXT = ["#000000"]\n')
        self.assertEqual(values, {"CARD": "#223344"})

    def test_files_that_are_not_skins(self):
        for text in ("", "NAME = 'x'", "{not python", "\x00", "ACCENT = '#112233'\n" + "#" * userskins.MAX_SIZE):
            with self.assertRaises(ValueError):
                userskins.parse(text)

    def test_install_list_load_and_replace(self):
        ident, values = userskins.install("﻿" + SKIN, self.folder, "file name")
        self.assertEqual((ident, values["NAME"]), ("user_ocean_bleu", "Océan bleu"))
        userskins.install(SKIN.replace("#112233", "#445566"), self.folder, "file name")
        self.assertEqual([(i, v["ACCENT"]) for i, v, _p in userskins.listing(self.folder)], [(ident, "#445566")])
        self.assertEqual(userskins.load(self.folder, ident)["RADIUS_CARD"], 8)
        for bad in ("user_../x", "default", "user_missing", ""):
            self.assertEqual(userskins.load(self.folder, bad), {})
        self.assertEqual(userskins.install('ACCENT = "#112233"', self.folder, "  My   file ")[1]["NAME"], "My file")
        self.assertTrue(userskins.skin_id("日本").startswith("user_"))

    def test_remove_only_deletes_an_imported_skin(self):
        ident, _v = userskins.install(SKIN, self.folder, "x")
        outside = os.path.join(os.path.dirname(self.folder), "outside_%s.json" % os.path.basename(self.folder))
        with open(outside, "w") as f:
            f.write("{}")
        self.addCleanup(os.remove, outside)
        for bad in ("default", "user_../" + os.path.basename(outside)[:-5], "../x", "", None):
            self.assertFalse(userskins.remove(self.folder, bad))
        self.assertTrue(os.path.exists(outside))
        self.assertTrue(userskins.remove(self.folder, ident))
        self.assertEqual(userskins.listing(self.folder), [])
        self.assertFalse(userskins.remove(self.folder, ident))

    def test_an_exported_skin_is_imported_back_unchanged(self):
        ident, values = userskins.install(SKIN + 'AUTHOR = "L\'auteur \\"x\\""\nFONT = "Arial"\n', self.folder, "x")
        text = userskins.export_text(userskins.load(self.folder, ident))
        self.assertEqual(userskins.parse(text), values)
        other = tempfile.mkdtemp()
        self.assertEqual(userskins.install(text, other, "y"), (ident, values))
        self.assertEqual(userskins.file_name(ident), "ocean_bleu.py")

    def test_several_skins_in_one_file(self):
        a = userskins.install(SKIN, self.folder, "x")[1]
        b = userskins.install('NAME = "Deux"\nACCENT = "#000001"\n', self.folder, "x")[1]
        text = userskins.bundle_text([a, b])
        other = tempfile.mkdtemp()
        done = userskins.install_all("\ufeff" + text + "\n" + userskins.MARKER + "\nprint(1)\n", other, "z")
        self.assertEqual([v for _i, v in done], [a, b])
        self.assertEqual(len(userskins.listing(other)), 2)
        self.assertEqual(userskins.install_all(SKIN, tempfile.mkdtemp(), "z")[0][1], a)            # a plain file: one skin
        unnamed = userskins.MARKER + '\nACCENT = "#000001"\n' + userskins.MARKER + '\nACCENT = "#000002"\n'
        self.assertEqual([v["NAME"] for _i, v in userskins.install_all(unnamed, other, "z")], ["z 1", "z 2"])
        for bad in ("", userskins.MARKER, "print(1)", "#" * (userskins.MAX_FILE + 1)):
            with self.assertRaises(ValueError):
                userskins.install_all(bad, other, "z")

    def test_export_files_never_replaces_a_file(self):
        a = userskins.install(SKIN, self.folder, "x")[0]
        b = userskins.install('NAME = "Deux"\nACCENT = "#000001"\n', self.folder, "x")[0]
        target = tempfile.mkdtemp()
        with open(os.path.join(target, "deux.py"), "w") as f:
            f.write("keep")
        written = userskins.export_files(self.folder, [a, b, "user_missing"], target)
        self.assertEqual([os.path.basename(p) for p in written], ["ocean_bleu.py", "deux_2.py"])
        with open(os.path.join(target, "deux.py")) as f:
            self.assertEqual(f.read(), "keep")

    def test_unique_names(self):
        self.assertEqual(userskins.unique_name("A", {"B"}), "A")
        self.assertEqual(userskins.unique_name("A", {"A", "A (2)"}), "A (3)")

    def test_desktop_and_mobile_see_the_imported_skin(self):
        ident, _v = userskins.install(SKIN.replace("Océan  bleu", "Dark (Graphite)"), self.folder, "x")
        old, skins.USER_DIR = skins.USER_DIR, self.folder
        try:
            self.assertEqual(skins.available()["Dark (Graphite) (2)"], ident)
            skin = skins.load(ident)
            self.assertEqual((skin.ACCENT, skin.TEXT), ("#112233", skins.load("default").TEXT))
        finally:
            skins.USER_DIR = old
        found = themes.discover(os.path.join(ROOT, "skins"), self.folder)
        entry = next(s for s in found if s["id"] == ident)
        self.assertEqual((entry["name"], found[0]["id"]), ("Dark (Graphite) (2)", "default"))
        self.assertAlmostEqual(themes.palette(themes.read_skin(entry["path"]))["accent"][0], 0x11 / 255)

    def test_the_default_skin_file_can_be_imported(self):
        with open(os.path.join(ROOT, "skins", "default.py"), encoding="utf-8") as f:
            values = userskins.parse(f.read())
        self.assertEqual(sorted(k for k in values if k in userskins.COLOR_KEYS), sorted(userskins.COLOR_KEYS))
        self.assertTrue(set(userskins.NUMBER_KEYS) <= set(values))


if __name__ == "__main__":
    unittest.main()
