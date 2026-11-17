"""Detection of the web links in the comments (utils.split_links / utils.markup_links)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils  # noqa: E402


class LinkTests(unittest.TestCase):
    def test_text_without_link_is_one_piece(self):
        self.assertEqual(utils.split_links("hello world"), [("hello world", None)])
        self.assertEqual(utils.split_links(""), [])

    def test_link_in_a_sentence_without_its_final_punctuation(self):
        self.assertEqual(utils.split_links("see https://youtu.be/abc?t=3&x=1. Thanks"),
                         [("see ", None), ("https://youtu.be/abc?t=3&x=1", "https://youtu.be/abc?t=3&x=1"), (". Thanks", None)])

    def test_www_address_gets_https(self):
        self.assertEqual(utils.split_links("www.example.com/page, ok"),
                         [("www.example.com/page", "https://www.example.com/page"), (", ok", None)])

    def test_closing_parenthesis_belongs_to_the_sentence_unless_balanced(self):
        self.assertEqual(utils.split_links("(https://a.org/x)")[1][1], "https://a.org/x")
        self.assertEqual(utils.split_links("https://a.org/x_(y)")[0][1], "https://a.org/x_(y)")

    def test_brackets_end_the_link(self):
        self.assertEqual([u for _p, u in utils.split_links("[b]https://z.io/a[/b]") if u], ["https://z.io/a"])

    def test_several_links(self):
        self.assertEqual([u for _p, u in utils.split_links("https://a.io and http://b.io") if u], ["https://a.io", "http://b.io"])

    def test_markup_marks_links_and_escapes_the_rest(self):
        out = utils.markup_links("a [b] & https://a.org/p fin", "#7cc0ff")
        self.assertEqual(out, "a &bl;b&br; &amp; [ref=https://a.org/p][color=#7cc0ff][u]https://a.org/p[/u][/color][/ref] fin")


if __name__ == "__main__":
    unittest.main()
