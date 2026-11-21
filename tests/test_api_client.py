"""Unit tests against the mock server (NOT live GenLogin).
Run: python -m unittest tests.test_api_client -v
"""
import os
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.test_mock_server import Handler  # noqa: E402
from app.integrations.genlogin_api import GenLoginApi  # noqa: E402
from app.services.version_service import (  # noqa: E402
    UpdateNotSupportedError, dry_run, preview_update, update_profile)
from app.services.profile_service import search_filter  # noqa: E402
from app.core.models import Profile  # noqa: E402


class MockTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 8787), Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.api = GenLoginApi("http://127.0.0.1:8787/", timeout=5)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_connection(self):
        r = self.api.test_connection()
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["total"], 3)

    def test_list_and_search(self):
        profiles = self.api.list_all_profiles()
        self.assertEqual(len(profiles), 3)
        self.assertEqual(search_filter(profiles, query="shop 1")[0].id, "prof-001")
        self.assertEqual(len(search_filter(profiles, status="running")), 1)

    def test_run_and_verify_running(self):
        self.api.run_profile("prof-001")
        self.assertTrue(self.api.is_running("prof-001"))

    def test_update_is_gated(self):
        items = preview_update(self.api.list_all_profiles(), "156", {"prof-002"})
        by_id = {i.profile_id: i for i in items}
        self.assertEqual(by_id["prof-002"].status, "skipped")  # running
        self.assertEqual(by_id["prof-001"].status, "pending")  # 155 -> 156
        self.assertEqual(by_id["prof-003"].status, "pending")
        dry_run(items)
        self.assertTrue(all(i.status == "skipped" for i in items))
        with self.assertRaises(UpdateNotSupportedError):
            update_profile(self.api, items[0], "156")


if __name__ == "__main__":
    unittest.main()
