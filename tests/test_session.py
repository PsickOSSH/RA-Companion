import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import medians
from utils import (Session, achievement_url, api_time, filter_games, game_url, median_master, recent_games, short_time,
                   user_url, want_games)


def game(*achievements, title="Game"):
    return {"Title": title, "Achievements": {str(a["ID"]): a for a in achievements}}


START = api_time("2026-11-27 12:00:00")


class SessionTests(unittest.TestCase):
    def test_only_the_unlocks_made_after_the_start_are_counted(self):
        s = Session(START)
        new = s.add(game({"ID": 1, "Points": 5, "DateEarned": "2026-11-27 11:00:00"},
                         {"ID": 2, "Points": 10, "DateEarned": "2026-11-27 12:05:00",
                          "DateEarnedHardcore": "2026-11-27 12:05:00"},
                         {"ID": 3, "Points": 25}))
        self.assertEqual([i["id"] for i in new], ["2"])
        self.assertEqual(s.summary(now=START + 3900), (1, 10, "1 h 05"))

    def test_an_unlock_is_new_only_once_and_games_add_up(self):
        s = Session(START)
        a = {"ID": 1, "Points": 5, "DateEarned": "2026-11-27 12:01:00"}
        self.assertEqual(len(s.add(game(a))), 1)
        self.assertEqual(s.add(game(a)), [])
        s.add(game({"ID": 9, "Points": 3, "DateEarned": "2026-11-27 12:09:00"}, title="Other"))
        self.assertEqual([i["game"] for i in s.unlocks()], ["Other", "Game"])
        self.assertEqual(s.summary(now=START)[:2], (2, 8))

    def test_hardcore_only_and_softcore_won_again_in_hardcore(self):
        s = Session(START)
        a = {"ID": 1, "Points": 5, "DateEarned": "2026-11-27 12:01:00"}
        s.add(game(a))
        self.assertEqual(s.summary(hc_only=True, now=START)[:2], (0, 0))
        self.assertEqual(s.add(game(dict(a, DateEarnedHardcore="2026-11-27 12:20:00"))), [])
        self.assertEqual(s.summary(hc_only=True, now=START)[:2], (1, 5))

    def test_empty_answers(self):
        s = Session(START)
        self.assertEqual(s.add(None), [])
        self.assertEqual(s.add({"Achievements": []}), [])
        self.assertEqual(short_time(59), "0 min")
        self.assertEqual(short_time(12 * 60), "12 min")


class GameListTests(unittest.TestCase):
    def test_recent_games(self):
        reply = [{"GameID": 11, "Title": "A", "ConsoleName": "SNES", "NumPossibleAchievements": 40, "NumAchieved": 12,
                  "NumAchievedHardcore": 10}, {"Title": "no id"}]
        self.assertEqual(recent_games(reply), [{"game_id": 11, "title": "A", "console": "SNES", "done": 12, "total": 40}])
        self.assertEqual(recent_games(reply, hc_only=True)[0]["done"], 10)
        self.assertEqual(recent_games({"error": 1}), [])

    def test_web_pages(self):
        self.assertEqual(user_url("Scott"), "https://retroachievements.org/user/Scott")
        self.assertEqual(user_url("a b/c"), "https://retroachievements.org/user/a%20b%2Fc")
        self.assertEqual(game_url(228), "https://retroachievements.org/game/228")
        self.assertEqual(achievement_url("342"), "https://retroachievements.org/achievement/342")

    def test_search_in_a_list(self):
        games = [{"title": "Pokémon Red", "console": "Game Boy"}, {"title": "Super Mario World", "console": "SNES"}]
        self.assertEqual(filter_games(games, "  "), games)
        self.assertEqual(filter_games(games, "POKEMON"), games[:1])
        self.assertEqual(filter_games(games, "mario snes"), games[1:])
        self.assertEqual(filter_games(games, "zelda"), [])

    def test_want_to_play(self):
        reply = {"Count": 2, "Total": 2, "Results": [
            {"ID": 2, "Title": "Zelda", "ConsoleName": "NES", "AchievementsPublished": 30},
            {"ID": 1, "Title": "Ápex", "ConsoleName": "GB", "AchievementsPublished": 5}]}
        self.assertEqual([g["title"] for g in want_games(reply)], ["Ápex", "Zelda"])
        self.assertEqual(want_games([]), [])


class TimeToMasterTests(unittest.TestCase):
    def test_the_time_to_master_is_cached_and_put_in_the_game(self):
        reply = {"MedianTimeToMaster": 79744, "Achievements": [{"ID": 5, "MedianTimeToUnlockHardcore": 60}]}
        folder = tempfile.mkdtemp()
        data = medians.fetch(lambda *a, **k: reply, "k", 987654, folder)
        medians._MEMORY.clear()
        again = medians.fetch(lambda *a, **k: self.fail("the disk cache must be used"), "k", 987654, folder)
        self.assertEqual(data, again)
        g = game({"ID": 5})
        medians.apply(g, again)
        self.assertEqual(median_master(g), 79744)
        self.assertEqual(g["Achievements"]["5"]["MedianTimeToUnlockHardcore"], 60)

    def test_no_time_to_master(self):
        g = game({"ID": 5})
        medians.apply(g, medians._parse({"MedianTimeToMaster": 0, "Achievements": []}))
        self.assertIsNone(median_master(g))


if __name__ == "__main__":
    unittest.main()
