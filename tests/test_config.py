from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from macrosignage.config import database_form_from_uri, database_uri_from_parts, validate_database_uri, write_database_uri
from macrosignage.app import create_app
from macrosignage.extensions import db
from macrosignage.features.auth.models import User
from macrosignage.features.auth.services import hash_password


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

    def test_database_uri_validation_accepts_sqlalchemy_urls(self):
        self.assertIsNone(validate_database_uri("sqlite:///instance/macrosignage.sqlite3"))
        self.assertIsNone(validate_database_uri("postgresql+psycopg://user:password@localhost/macrosignage"))
        self.assertIsNone(validate_database_uri("mysql+pymysql://user:password@localhost/macrosignage"))
        self.assertEqual(validate_database_uri("not a uri"), "Enter a valid SQLAlchemy database URI.")

    def test_database_uri_builder_supports_friendly_database_fields(self):
        self.assertEqual(
            database_uri_from_parts(
                database_type="sqlite",
                sqlite_path="/tmp/macrosignage.sqlite3",
            ),
            "sqlite:////tmp/macrosignage.sqlite3",
        )
        self.assertEqual(
            database_uri_from_parts(
                database_type="postgresql",
                host="localhost",
                port="5432",
                username="macro",
                password="secret",
                database_name="macrosignage",
                query="sslmode=require",
            ),
            "postgresql+psycopg://macro:secret@localhost:5432/macrosignage?sslmode=require",
        )

    def test_database_form_from_uri_prefills_friendly_fields(self):
        form = database_form_from_uri(
            "mysql+pymysql://macro:secret@db.example.com:3306/macrosignage?charset=utf8mb4",
            "instance/macrosignage.sqlite3",
        )

        self.assertEqual(form["database_type"], "mysql")
        self.assertEqual(form["host"], "db.example.com")
        self.assertEqual(form["port"], "3306")
        self.assertEqual(form["username"], "macro")
        self.assertEqual(form["password"], "secret")
        self.assertEqual(form["database_name"], "macrosignage")
        self.assertEqual(form["query"], "charset=utf8mb4")

    def test_write_database_uri_updates_dotenv(self):
        env_file = Path(self.tempdir.name) / ".env"
        write_database_uri(env_file, "postgresql+psycopg://user:password@localhost/macrosignage")

        content = env_file.read_text(encoding="utf-8")
        self.assertIn(
            "MACROSIGNAGE_DATABASE_URI='postgresql+psycopg://user:password@localhost/macrosignage'",
            content,
        )

    def test_admin_can_save_database_uri_setting(self):
        temp_path = Path(self.tempdir.name)
        env_file = temp_path / ".env"
        app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{temp_path / 'settings.sqlite3'}",
                "MEDIA_UPLOAD_FOLDER": str(temp_path / "media"),
            },
            env_file=env_file,
        )

        with app.app_context():
            user = User(
                username="site-admin",
                email="admin@example.com",
                password_hash=hash_password("password123"),
                role="ADMIN",
                active=True,
            )
            db.session.add(user)
            db.session.commit()

            client = app.test_client()
            self.assertEqual(
                client.post(
                    "/auth/login",
                    data={"identifier": "site-admin", "password": "password123"},
                ).status_code,
                302,
            )
            settings_response = client.get("/admin/settings/")
            self.assertEqual(settings_response.status_code, 200)
            settings_body = settings_response.get_data(as_text=True)
            self.assertIn("Manage database", settings_body)
            self.assertNotIn("data-database-driver-message", settings_body)

            database_response = client.get("/admin/settings/database")
            self.assertEqual(database_response.status_code, 200)
            database_body = database_response.get_data(as_text=True)
            self.assertIn("PostgreSQL", database_body)
            self.assertIn("uv add psycopg", database_body)
            self.assertIn("Advanced SQLAlchemy URI", database_body)
            self.assertIn("data-database-driver-message", database_body)
            self.assertIn("data-database-install-button", database_body)

            response = client.post(
                "/admin/settings/database",
                data={
                    "database_type": "postgresql",
                    "host": "localhost",
                    "port": "5432",
                    "username": "user",
                    "password": "password",
                    "database_name": "macrosignage",
                    "query": "sslmode=require",
                },
                follow_redirects=False,
            )
            self.assertEqual(response.status_code, 302)
            self.assertIn(
                "postgresql+psycopg://user:password@localhost:5432/macrosignage?sslmode=require",
                env_file.read_text(encoding="utf-8"),
            )

            db.session.remove()
            db.drop_all()


if __name__ == "__main__":
    unittest.main()
