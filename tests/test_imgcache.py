import os
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import imgcache

BADGE = "https://media.retroachievements.org/Badge/12345.png"
AVATAR = "https://media.retroachievements.org/UserPic/Nicolas.png"


class ImageCacheTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.calls = []
        self.real = imgcache.http_get
        imgcache.http_get = self.fake_get
        imgcache._FAILED.clear()

    def tearDown(self):
        imgcache.http_get = self.real

    def fake_get(self, url, binary=False):
        self.calls.append(url)
        return b"PNGDATA"

    def age(self, url, days):
        path = imgcache.path_for(self.folder, url)
        old = time.time() - days * 86400
        os.utime(path, (old, old))

    def test_downloaded_once_then_read_from_disk(self):
        self.assertEqual(imgcache.get_bytes(self.folder, BADGE), b"PNGDATA")
        self.assertEqual(imgcache.get_bytes(self.folder, BADGE), b"PNGDATA")
        self.assertEqual(self.calls, [BADGE])

    def test_badges_never_expire(self):
        imgcache.get_bytes(self.folder, BADGE)
        self.age(BADGE, 400)
        self.assertIsNotNone(imgcache.cached_path(self.folder, BADGE))

    def test_avatars_expire_after_a_week(self):
        imgcache.get_bytes(self.folder, AVATAR)
        self.age(AVATAR, 3)
        self.assertIsNotNone(imgcache.cached_path(self.folder, AVATAR))
        self.age(AVATAR, 8)
        self.assertIsNone(imgcache.cached_path(self.folder, AVATAR))

    def test_old_copy_is_used_when_the_network_fails(self):
        imgcache.get_bytes(self.folder, AVATAR)
        self.age(AVATAR, 30)

        def broken(url, binary=False):
            raise OSError("offline")
        imgcache.http_get = broken
        self.assertEqual(imgcache.get_bytes(self.folder, AVATAR), b"PNGDATA")

    def test_failed_download_gives_none_and_leaves_no_file(self):
        def broken(url, binary=False):
            raise OSError("404")
        imgcache.http_get = broken
        self.assertIsNone(imgcache.get_bytes(self.folder, BADGE))
        self.assertEqual(os.listdir(self.folder), [])

    def test_extension_is_kept(self):
        self.assertTrue(imgcache.path_for(self.folder, BADGE).endswith(".png"))
        self.assertTrue(imgcache.path_for(self.folder, "https://x.org/a.jpg?w=64").endswith(".jpg"))

    def test_async_download_once_for_several_requests(self):
        results, done = [], threading.Event()

        def callback(path):
            results.append(path)
            if len(results) == 3:
                done.set()
        for _ in range(3):
            imgcache.fetch_async(self.folder, BADGE, callback)
        self.assertTrue(done.wait(5))
        self.assertEqual(len(self.calls), 1)
        self.assertTrue(all(os.path.exists(p) for p in results))

    def test_failed_address_is_not_retried_at_once(self):
        def broken(url, binary=False):
            self.calls.append(url)
            raise OSError("404")
        imgcache.http_get = broken
        imgcache.fetch_async(self.folder, BADGE, lambda p: None)
        for _ in range(100):
            if BADGE in imgcache._FAILED:
                break
            time.sleep(0.05)
        imgcache.fetch_async(self.folder, BADGE, lambda p: None)
        time.sleep(0.2)
        self.assertEqual(len(self.calls), 1)


if __name__ == "__main__":
    unittest.main()
