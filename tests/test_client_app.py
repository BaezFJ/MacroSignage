from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

CLIENT_PATH = Path(__file__).resolve().parents[1] / "client"
sys.path.insert(0, str(CLIENT_PATH))

from macrosignage_client.app import load_config, normalize_server_url, save_config


class MacroSignageClientTestCase(unittest.TestCase):
    def test_normalize_server_url_accepts_host_or_http_url(self):
        self.assertEqual(normalize_server_url("signage.local:5000"), "http://signage.local:5000")
        self.assertEqual(normalize_server_url("https://signage.example.com/"), "https://signage.example.com")
        self.assertEqual(normalize_server_url("ftp://signage.example.com"), "")
        self.assertEqual(normalize_server_url(""), "")

    def test_save_config_only_persists_token_when_auto_pair_enabled(self):
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "client.json"
            config = save_config(
                {
                    "server_url": "signage.local:5000",
                    "display_token": "display-secret",
                    "auto_pair": True,
                },
                path,
            )

            self.assertEqual(config["server_url"], "http://signage.local:5000")
            self.assertEqual(load_config(path)["display_token"], "display-secret")
            if os.name != "nt":
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            save_config(
                {
                    "server_url": "signage.local:5000",
                    "display_token": "display-secret",
                    "auto_pair": False,
                },
                path,
            )
            self.assertEqual(load_config(path)["display_token"], "")


if __name__ == "__main__":
    unittest.main()
