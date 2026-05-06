from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from macrosignage.app import create_app


class AppConfigTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.previous_env = {
            key: os.environ.get(key)
            for key in (
                "MACROSIGNAGE_SECRET_KEY",
                "MACROSIGNAGE_DATABASE_URI",
                "MACROSIGNAGE_MEDIA_UPLOAD_FOLDER",
            )
        }
        for key in self.previous_env:
            os.environ.pop(key, None)

    def tearDown(self):
        self.tempdir.cleanup()
        for key, value in self.previous_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_create_app_loads_explicit_dotenv_file(self):
        temp_path = Path(self.tempdir.name)
        db_path = temp_path / "env.sqlite3"
        media_path = temp_path / "media-from-env"
        env_file = temp_path / ".env"
        env_file.write_text(
            "\n".join(
                [
                    "MACROSIGNAGE_SECRET_KEY=env-secret",
                    f"MACROSIGNAGE_DATABASE_URI=sqlite:///{db_path}",
                    f"MACROSIGNAGE_MEDIA_UPLOAD_FOLDER={media_path}",
                ]
            ),
            encoding="utf-8",
        )

        app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
            },
            env_file=env_file,
        )

        self.assertEqual(app.config["SECRET_KEY"], "env-secret")
        self.assertEqual(app.config["SQLALCHEMY_DATABASE_URI"], f"sqlite:///{db_path}")
        self.assertEqual(app.config["MEDIA_UPLOAD_FOLDER"], str(media_path))
        self.assertTrue(media_path.exists())

    def test_explicit_config_overrides_dotenv_values(self):
        temp_path = Path(self.tempdir.name)
        env_file = temp_path / ".env"
        override_db = temp_path / "override.sqlite3"
        env_file.write_text(
            "\n".join(
                [
                    "MACROSIGNAGE_SECRET_KEY=env-secret",
                    f"MACROSIGNAGE_DATABASE_URI=sqlite:///{temp_path / 'env.sqlite3'}",
                ]
            ),
            encoding="utf-8",
        )

        app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SECRET_KEY": "config-secret",
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{override_db}",
            },
            env_file=env_file,
        )

        self.assertEqual(app.config["SECRET_KEY"], "config-secret")
        self.assertEqual(app.config["SQLALCHEMY_DATABASE_URI"], f"sqlite:///{override_db}")


if __name__ == "__main__":
    unittest.main()
