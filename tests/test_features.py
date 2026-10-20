"""Unit tests for features.py (pure logic, no Kivy needed). Run from the project folder:
    python -m unittest discover -s tests
"""

import os
import sys
import tempfile
import unittest
import uitext

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import features  # noqa: E402

MEDIA = "https://media.example"


def ach(i, title, pts, hc=None, sc=None, typ=""):
    return {"ID": i, "Title": title, "Description": f"d{i}", "Points": pts, "BadgeName": f"B{i}", "DisplayOrder": i,
            "DateEarnedHardcore": hc, "DateEarned": hc or sc, "type": typ}


ME = {"Achievements": {"1": ach(1, "A1", 10, hc="2026-10-05 10:00:00"), "2": ach(2, "A2", 5, sc="2026-10-05 11:00:00"),
                       "3": ach(3, "A3", 25, typ="missable"), "4": ach(4, "A4", 15),
                       "5": ach(5, "A5", 50, hc="2026-10-05 12:00:00", typ="missable")}}
FRIEND = {"Achievements": {"1": ach(1, "A1", 10, hc="2026-10-06 10:00:00"), "2": ach(2, "A2", 5),
                           "3": ach(3, "A3", 25, hc="2026-10-06 12:00:00"), "4": ach(4, "A4", 15), "5": ach(5, "A5", 50)}}


class AchievementTests(unittest.TestCase):
    def test_progress_and_hc_sc_counters(self):
        p = features.progress_summary(ME)
        self.assertEqual((p["done"], p["total"], p["got_pts"], p["tot_pts"], p["pct"]), (3, 5, 65, 105, 60))
        self.assertEqual((p["n_hc"], p["n_sc"]), (2, 1))                      # "HC 2 • SC 1"
        self.assertEqual(features.progress_summary(ME, hc_only=True)["done"], 2)
        self.assertEqual(features.progress_summary(None)["total"], 0)

    def test_rows_flags(self):
        rows = features.achievement_rows(ME, MEDIA, noted={"3"})
        self.assertEqual([r["ach_id"] for r in rows], ["1", "2", "3", "4", "5"])
        self.assertEqual([r["missable"] for r in rows], [False, False, True, False, True])
        self.assertEqual([r["has_note"] for r in rows], [False, False, True, False, False])
        self.assertTrue(rows[2]["badge_url"].endswith("/Badge/B3_lock.png"))
        hc_rows = features.achievement_rows(ME, MEDIA, hc_only=True)
        self.assertEqual([r["status"] for r in hc_rows], ["unlocked", "locked", "locked", "locked", "unlocked"])

    def test_missable_option_combines_with_the_status_filters(self):
        rows = features.achievement_rows(ME, MEDIA)
        titles = lambda name, miss: [r["title"] for r in features.filter_rows(rows, name, miss)]
        self.assertEqual(titles("all", False), ["A1", "A2", "A3", "A4", "A5"])
        self.assertEqual(titles("all", True), ["A3", "A5"])
        self.assertEqual(titles("locked", False), ["A3", "A4"])
        self.assertEqual(titles("locked", True), ["A3"])
        self.assertEqual(titles("unlocked", True), ["A5"])
        self.assertEqual(titles("missable", False), ["A3", "A5"])          # old filter name still works

    def test_every_sort_mode_works(self):
        for mode in uitext.SORT_IDS:
            self.assertEqual(len(features.achievement_rows(ME, MEDIA, sort_mode=mode)), 5, mode)
        pts = [r["points"] for r in features.achievement_rows(ME, MEDIA, sort_mode="pts_desc")]
        self.assertEqual(pts, ["50", "25", "15", "10", "5"])

    def test_translated_descriptions(self):
        rows = features.achievement_rows(ME, MEDIA, desc_fn=lambda t: t.upper())
        self.assertEqual(rows[0]["description"], "D1")


class NotesTests(unittest.TestCase):
    def test_save_reload_and_delete(self):
        path = os.path.join(tempfile.mkdtemp(), "notes.json")
        store = features.NotesStore(path)
        self.assertTrue(store.set(3, "  boss: use fire\nsecond line "))
        self.assertFalse(store.set("3", "boss: use fire\nsecond line"))     # nothing changed
        self.assertEqual(store.ids(), {"3"})
        again = features.NotesStore(path)                                      # survives a restart
        self.assertEqual(again.get(3), "boss: use fire\nsecond line")
        self.assertTrue(again.set(3, "   "))                                   # empty text deletes the note
        self.assertEqual(features.NotesStore(path).ids(), set())

    def test_corrupt_file(self):
        path = os.path.join(tempfile.mkdtemp(), "notes.json")
        with open(path, "w") as f:
            f.write("{not json")
        self.assertEqual(features.NotesStore(path).ids(), set())


class CommentTests(unittest.TestCase):
    def test_newest_first_and_offset(self):
        calls = []

        def fake(endpoint, key, **p):
            calls.append(p["o"])
            return {"Total": 130, "Results": [{"User": f"u{p['o'] + k}", "Submitted": "2026-10-01 10:00:00", "CommentText": f" c{p['o'] + k} "}
                                              for k in range(100)]}

        total, comments = features.load_comments(fake, "K", 42)
        self.assertEqual((total, calls), (130, [0, 30]))      # more than 100 comments: the newest page is fetched
        self.assertEqual(comments[0]["user"], "u129")          # newest first
        self.assertEqual(comments[0]["text"], "c129")

    def test_invalid_answer(self):
        self.assertEqual(features.load_comments(lambda *a, **k: None, "K", 1), (0, []))


class UnlockTrackerTests(unittest.TestCase):
    def test_detects_new_unlocks_only_after_a_baseline(self):
        t = features.UnlockTracker()
        self.assertEqual(t.check(1, ME, "", None), ([], []))                 # baseline, no notification
        self.assertEqual(t.check(1, ME, "", None), ([], []))
        newer = {"Achievements": dict(ME["Achievements"], **{"3": ach(3, "A3", 25, hc="2026-10-07 09:00:00")})}
        mine, _ = t.check(1, newer, "", None)
        self.assertEqual([a["ID"] for a in mine], [3])
        self.assertEqual(t.check(1, newer, "", None), ([], []))              # not notified twice

    def test_friend_and_game_change(self):
        t = features.UnlockTracker()
        t.check(1, ME, "bob", FRIEND)
        newer_friend = {"Achievements": dict(FRIEND["Achievements"], **{"2": ach(2, "A2", 5, hc="2026-10-08 10:00:00")})}
        _, theirs = t.check(1, ME, "bob", newer_friend)
        self.assertEqual([a["ID"] for a in theirs], [2])
        self.assertEqual(t.check(2, newer_friend, "bob", newer_friend), ([], []))   # another game: new baseline

    def test_empty_answer_keeps_the_baseline(self):
        t = features.UnlockTracker()
        t.check(1, ME, "", None)
        t.check(1, {"Achievements": {}}, "", None)                             # network hiccup
        self.assertEqual(t.check(1, ME, "", None), ([], []))                   # no false "everything is new"


class DuelTests(unittest.TestCase):
    def test_duel(self):
        d = features.compute_duel(ME, FRIEND, "me", "bob", MEDIA, noted={"4"})
        self.assertEqual((d["x"], d["y"], d["tot"], d["pa"], d["pb"]), (3, 2, 5, 65, 35))
        self.assertEqual([r["state"] for r in d["rows"]], ["friend", "me", "me", "none", "both"])
        first = d["rows"][0]
        self.assertEqual((first["ach_id"], first["missable"]), ("3", True))
        self.assertTrue(next(r for r in d["rows"] if r["ach_id"] == "4")["has_note"])

    def test_missing_friend_game(self):
        self.assertEqual(features.compute_duel(ME, None, "me", "bob", MEDIA)["y"], 0)


class GroupTests(unittest.TestCase):
    def test_group_sorted_by_progress(self):
        data = {"carol": {"s": {"TotalPoints": 5}, "game": FRIEND, "pic": "/UserPic/carol.png"},
                "dave": {"error": "Pseudo ou clé API invalide"}}
        entries = features.group_entries("me", {"TotalPoints": 100}, ME, "/UserPic/me.png", ["carol", "dave", "erin"], data)
        self.assertEqual([e["name"] for e in entries], ["me", "carol", "dave", "erin"])
        rows = features.entry_rows(entries, MEDIA)
        self.assertFalse(rows[0]["removable"])
        self.assertEqual(rows[2]["err"], "Pseudo ou clé API invalide")
        self.assertEqual(rows[3]["play"], "…")


class GameIndexTests(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "idx.json")
        self.idx = features.GameIndex(self.path)
        self.idx.set_games(1, [{"ID": 1, "Title": "Sonic the Hedgehog", "ConsoleName": "Mega Drive", "NumAchievements": 12},
                               {"ID": 2, "Title": "Super Sonic Wings", "ConsoleName": "Mega Drive", "NumAchievements": 5},
                               {"ID": 3, "Title": "Pokémon Rouge", "ConsoleName": "Game Boy", "NumAchievements": 40}])

    def test_search(self):
        r = self.idx.search("sonic", [1])
        self.assertEqual([x["game_id"] for x in r], [1, 2])       # title starting with the word comes first
        self.assertEqual(self.idx.search("pokemon rouge", [1])[0]["game_id"], 3)   # accent-insensitive
        self.assertEqual(self.idx.search("1234", [1])[0]["game_id"], 1234)         # a number is a game ID
        self.assertEqual(self.idx.search("s", [1]), [])

    def test_save_and_reload(self):
        self.idx.set_consoles([{"ID": 2, "Name": "SNES"}, {"ID": 1, "Name": "Mega Drive"}])
        again = features.GameIndex(self.path)
        self.assertEqual(again.console_list(), [(1, "Mega Drive"), (2, "SNES")])
        self.assertTrue(again.consoles_fresh())


if __name__ == "__main__":
    unittest.main()
