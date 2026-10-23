"""Tests of layoututil.py. Run: python -m unittest discover -s tests"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import layoututil  # noqa: E402


class LayoutTests(unittest.TestCase):
    def test_weights_are_proportional_and_never_zero(self):
        self.assertEqual(layoututil.weights([30, 60, 90]), [30.0, 60.0, 90.0])
        self.assertEqual(layoututil.weights([0, 10]), [1.0, 10.0])

    def test_fit_size(self):
        width = lambda text, size: len(text) * size * 0.6                  # a simple fake font
        self.assertEqual(layoututil.fit_size(width, "abcd", 100, 12, 8), 12)         # fits: biggest size
        self.assertEqual(layoututil.fit_size(width, "x" * 10, 60, 12, 8), 10)         # shrinks until it fits
        self.assertEqual(layoututil.fit_size(width, "x" * 40, 60, 12, 8), 8)          # never below the smallest size


if __name__ == "__main__":
    unittest.main()
