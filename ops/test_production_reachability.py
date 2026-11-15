import io
import unittest
import urllib.error
from ops.production_reachability import classify_response, probe, exit_code


class FakeResponse:
    status = 200
    url = "https://pms-bersoch-mobile.netlify.app/"
    def __init__(self, text):
        self.content = text.encode()
    def read(self, length):
        return self.content[:length]
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False


class ReachabilityTests(unittest.TestCase):
    def test_valid_mobile_html_only_proves_reachability(self):
        html = b'<!doctype html><html><title>PMS Bersoch Mobile</title></html>'
        self.assertEqual(classify_response("mobile", 200, html,
            "https://pms-bersoch-mobile.netlify.app/"), "REACHABLE_HTML_NOT_FUNCTIONALITY")

    def test_valid_streamlit_html_only_proves_reachability(self):
        self.assertEqual(classify_response("streamlit", 200,
            b'<!doctype html><html><title>Streamlit</title></html>',
            "https://pms-max.streamlit.app/"), "REACHABLE_HTML_NOT_FUNCTIONALITY")

    def test_gateway_never_counts_as_success(self):
        self.assertEqual(classify_response("streamlit", 200,
            b'<html>Login</html>', "https://example.com/login"), "INCONCLUSIVE_GATEWAY")

    def test_unrecognized_mobile_html_is_not_certified(self):
        self.assertEqual(classify_response("mobile", 200,
            b'<html>Some other app</html>', "https://pms-bersoch-mobile.netlify.app/"),
            "INCONCLUSIVE_UNRECOGNIZED_HTML")

    def test_html_not_empty(self):
        self.assertEqual(classify_response("mobile", 200,
            b'', "https://pms-bersoch-mobile.netlify.app/"), "ERROR_EMPTY_RESPONSE")

    def test_failed_request_is_not_green(self):
        def failed(req, timeout):
            raise urllib.error.URLError("bad network")
        result = probe("BERSOCH_MOBILE", "https://pms-bersoch-mobile.netlify.app/",
                       "mobile", "PMS Bersoch", opener=failed)
        self.assertEqual(result["status"], "ERROR_NETWORK")
        self.assertEqual(exit_code([result]), 1)

    def test_inconclusive_gets_nonzero_status(self):
        self.assertEqual(exit_code([{"status":"INCONCLUSIVE_GATEWAY"}]), 2)

    def test_all_reachable_is_zero(self):
        self.assertEqual(exit_code([{"status":"REACHABLE_HTML_NOT_FUNCTIONALITY"}]), 0)


if __name__ == "__main__":
    unittest.main()
