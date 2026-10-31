import email.message
import unittest
import urllib.error
from unittest import mock

import ra_api


def http_error(code, retry_after=None):
    headers = email.message.Message()
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    return urllib.error.HTTPError("http://x", code, "err", headers, None)


class CallApiRetryTest(unittest.TestCase):
    def run_call(self, side_effect):
        with mock.patch.object(ra_api, "http_get", side_effect=side_effect) as get, \
                mock.patch.object(ra_api.time, "sleep") as sleep:
            try:
                result = ra_api.call_api("API_X.php", "KEY", u="me", g="")
                error = None
            except Exception as e:
                result, error = None, e
        return result, error, get, sleep

    def test_success_without_retry(self):
        result, error, get, sleep = self.run_call([{"ok": 1}])
        self.assertEqual(result, {"ok": 1})
        self.assertEqual(get.call_count, 1)
        sleep.assert_not_called()

    def test_url_has_key_and_drops_empty_params(self):
        _, _, get, _ = self.run_call([{}])
        url = get.call_args[0][0]
        self.assertIn("y=KEY", url)
        self.assertIn("u=me", url)
        self.assertNotIn("g=", url)

    def test_retries_on_429_then_succeeds(self):
        result, error, get, sleep = self.run_call([http_error(429), {"ok": 1}])
        self.assertEqual(result, {"ok": 1})
        self.assertEqual(get.call_count, 2)
        sleep.assert_called_once_with(1.0)

    def test_retry_after_header_is_used_and_capped(self):
        _, _, _, sleep = self.run_call([http_error(429, 4), http_error(503, 999), {"ok": 1}])
        self.assertEqual([c[0][0] for c in sleep.call_args_list], [4.0, ra_api.RETRY_MAX_WAIT])

    def test_gives_up_after_two_retries_with_last_error(self):
        errors = [http_error(503), http_error(503), http_error(503)]
        _, error, get, sleep = self.run_call(errors)
        self.assertIs(error, errors[-1])
        self.assertEqual(get.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_network_error_is_retried(self):
        result, _, get, _ = self.run_call([urllib.error.URLError("down"), TimeoutError(), {"ok": 1}])
        self.assertEqual(result, {"ok": 1})
        self.assertEqual(get.call_count, 3)

    def test_bad_key_and_not_found_are_not_retried(self):
        for code in (401, 403, 404):
            err = http_error(code)
            _, error, get, sleep = self.run_call([err])
            self.assertIs(error, err)
            self.assertEqual(get.call_count, 1)
            sleep.assert_not_called()

    def test_invalid_json_is_not_retried(self):
        _, error, get, _ = self.run_call([ValueError("bad json")])
        self.assertIsInstance(error, ValueError)
        self.assertEqual(get.call_count, 1)


if __name__ == "__main__":
    unittest.main()
