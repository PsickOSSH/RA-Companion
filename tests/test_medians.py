import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import fmt_duration, median_beat_hc, median_master, median_unlock_hc


class HardcoreMedianTests(unittest.TestCase):
    def test_only_the_hardcore_median_is_used(self):
        a = {"MedianTimeToUnlock": 274, "MedianTimeToUnlockHardcore": 323}
        self.assertEqual(median_unlock_hc(a), 323)
        self.assertIsNone(median_unlock_hc({"MedianTimeToUnlock": 274}))

    def test_missing_zero_or_invalid_values(self):
        for value in (None, 0, "", "abc", -5):
            self.assertIsNone(median_unlock_hc({"MedianTimeToUnlockHardcore": value}))

    def test_game_medians(self):
        game = {"MedianTimeToBeat": 17878, "MedianTimeToBeatHardcore": 19224, "MedianTimeToComplete": 67017,
                "MedianTimeToMaster": 79744}
        self.assertEqual(median_beat_hc(game), 19224)
        self.assertEqual(median_master(game), 79744)
        self.assertIsNone(median_beat_hc({"MedianTimeToBeat": 17878}))

    def test_duration_format(self):
        self.assertEqual(fmt_duration(45), "45 s")
        self.assertEqual(fmt_duration(323), "5 min 23 s")
        self.assertEqual(fmt_duration(3600), "1 h")
        self.assertEqual(fmt_duration(19224), "5 h 20 min")
        self.assertEqual(fmt_duration(79744), "22 h 09 min")
        self.assertEqual(fmt_duration(400000), "111 h")
        self.assertEqual(fmt_duration(None), "")
        self.assertEqual(fmt_duration("323"), "5 min 23 s")


if __name__ == "__main__":
    unittest.main()
