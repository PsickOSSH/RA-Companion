import http.client
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import overlay


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.overlay = overlay.Overlay()
        self.assertTrue(self.overlay.start(0))           # any free port
        self.addCleanup(self.overlay.stop)

    def get(self, path, host=None):
        c = http.client.HTTPConnection("127.0.0.1", self.overlay.port, timeout=5)
        self.addCleanup(c.close)
        c.request("GET", path, headers={"Host": host} if host else {})
        r = c.getresponse()
        return r.status, r.read().decode("utf-8")

    def test_page_and_state(self):
        status, html = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn('id="banner"', html)
        self.assertNotIn("__ACCENT__", html)
        self.overlay.set_game({"Title": "Game", "ImageIcon": "/Images/1.png", "Achievements": {
            "1": {"DateEarned": "2026-11-27 12:00:00"}, "2": {}}}, progress="1/2")
        self.overlay.push({"title": "<b>A</b>", "points": 5, "badge": "123", "hc": True}, "\U0001F3C6 Achievement unlocked!")
        status, body = self.get("/state?x=1")
        state = json.loads(body)
        self.assertEqual((status, state["game"]["percent"], state["seq"]), (200, 50, 1))
        self.assertEqual(state["events"][0]["points"], "+5 pts • HARDCORE")
        self.assertEqual(state["events"][0]["head"], "Achievement unlocked!")        # the emoji is not sent as text
        self.assertNotIn("\U0001F3C6", body)
        self.assertTrue(state["events"][0]["icon"] == "" or state["events"][0]["icon"].startswith("data:image/png;base64,"))
        self.assertEqual(overlay.split_icon("\U0001F3C6 Unlocked!"), ("\U0001F3C6", "Unlocked!"))
        self.assertEqual(overlay.split_icon("Latest achievement"), ("", "Latest achievement"))
        self.assertTrue(state["events"][0]["badge"].endswith("/Badge/123.png"))

    def test_last_unlocked_achievement(self):
        game = {"Title": "Game", "Achievements": {
            "1": {"Title": "old", "Points": 5, "BadgeName": "1", "DateEarned": "2026-11-20 10:00:00",
                  "DateEarnedHardcore": "2026-11-20 10:00:00"},
            "2": {"Title": "newest", "Points": 10, "BadgeName": "2", "DateEarned": "2026-11-27 12:00:00"},
            "3": {"Title": "locked"}}}
        self.overlay.set_game(game, last_head="Latest")
        last = self.overlay.state()["game"]["last"]
        self.assertEqual((last["head"], last["title"], last["points"]), ("Latest", "newest", "+10 pts"))
        self.overlay.set_game(game, hc_only=True)
        self.assertEqual(self.overlay.state()["game"]["last"]["points"], "+5 pts • HARDCORE")
        self.overlay.set_game({"Title": "New", "Achievements": {"3": {"Title": "locked"}}})
        self.assertIsNone(self.overlay.state()["game"]["last"])

    def test_other_host_names_and_paths_are_refused(self):
        self.assertEqual(self.get("/state", host="evil.example:%d" % self.overlay.port)[0], 403)
        self.assertEqual(self.get("/state", host="localhost:%d" % self.overlay.port)[0], 200)
        self.assertEqual(self.get("/../app.py")[0], 404)

    def test_a_busy_port_is_reported_and_stop_frees_it(self):
        port = self.overlay.port
        other = overlay.Overlay()
        self.addCleanup(other.stop)
        self.assertFalse(other.start(port))
        self.assertFalse(other.running)
        self.overlay.stop()
        self.assertTrue(other.start(port))


if __name__ == "__main__":
    unittest.main()
