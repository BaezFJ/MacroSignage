from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from macrosignage.config import database_form_from_uri, database_uri_from_parts, validate_database_uri, write_database_uri
from macrosignage.diagnostics import redacted_database_label
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

    def test_database_label_redacts_credentials(self):
        label = redacted_database_label("postgresql+psycopg://macro:secret@db.example.com:5432/macrosignage")

        self.assertEqual(label, "postgresql+psycopg / db.example.com:5432/macrosignage")
        self.assertNotIn("secret", label)
        self.assertNotIn("macro:", label)

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

    def test_health_endpoint_reports_readiness_without_auth_or_secrets(self):
        temp_path = Path(self.tempdir.name)
        database_uri = "postgresql+psycopg://user:secret-password@db.example.com:5432/macrosignage"
        app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SECRET_KEY": "configured-secret",
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{temp_path / 'health.sqlite3'}",
                "MEDIA_UPLOAD_FOLDER": str(temp_path / "media"),
                "MACROSIGNAGE_PRODUCTION": True,
                "SESSION_COOKIE_SECURE": True,
            }
        )
        app.config["SQLALCHEMY_DATABASE_URI_PUBLIC_TEST_VALUE"] = database_uri

        response = app.test_client().get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["ready"])
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["version"], app.config["APP_VERSION"])
        self.assertEqual(payload["checks"]["database"]["status"], "ok")
        self.assertTrue(payload["checks"]["mediaStorage"]["writable"])
        self.assertEqual(payload["playerUpdates"]["contentVersion"], payload["contentVersion"])
        self.assertNotIn("secret-password", response.get_data(as_text=True))

    def test_admin_settings_show_redacted_operational_diagnostics(self):
        temp_path = Path(self.tempdir.name)
        app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SECRET_KEY": "configured-secret",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "MEDIA_UPLOAD_FOLDER": str(temp_path / "media"),
                "MACROSIGNAGE_PRODUCTION": True,
                "SESSION_COOKIE_SECURE": True,
                "MACROSIGNAGE_ENABLE_HSTS": True,
            }
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
                client.post("/auth/login", data={"identifier": "site-admin", "password": "password123"}).status_code,
                302,
            )
            response = client.get("/admin/settings/")
            body = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Operational Diagnostics", body)
            self.assertIn("Database readiness", body)
            self.assertIn("Media storage", body)
            self.assertIn("Secret key", body)
            self.assertIn("Configured", body)
            self.assertIn("Content version", body)
            self.assertNotIn("configured-secret", body)
            self.assertNotIn("password123", body)

            db.session.remove()
            db.drop_all()

    def test_existing_sqlite_database_is_upgraded_without_data_loss(self):
        temp_path = Path(self.tempdir.name)
        database_path = temp_path / "legacy.sqlite3"
        created_at = "2026-01-01 12:00:00"
        with sqlite3.connect(database_path) as connection:
            connection.executescript(
                """
                CREATE TABLE displays (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(120) NOT NULL,
                    location VARCHAR(160),
                    status VARCHAR(24) NOT NULL,
                    orientation VARCHAR(24) NOT NULL,
                    resolution_width INTEGER NOT NULL,
                    resolution_height INTEGER NOT NULL,
                    notes TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                );
                CREATE TABLE schedules (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(140) NOT NULL,
                    status VARCHAR(24) NOT NULL,
                    starts_at DATETIME,
                    ends_at DATETIME,
                    weekdays VARCHAR(32),
                    default_duration_seconds INTEGER NOT NULL,
                    notes TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                );
                CREATE TABLE media_assets (
                    id INTEGER PRIMARY KEY,
                    title VARCHAR(140) NOT NULL,
                    media_type VARCHAR(24) NOT NULL,
                    file_path VARCHAR(260),
                    original_filename VARCHAR(260),
                    mime_type VARCHAR(120),
                    body TEXT,
                    source_url VARCHAR(500),
                    notes TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                );
                CREATE TABLE media_slides (
                    id INTEGER PRIMARY KEY,
                    media_asset_id INTEGER NOT NULL,
                    sort_order INTEGER NOT NULL,
                    background_file_path VARCHAR(260),
                    background_original_filename VARCHAR(260),
                    text TEXT,
                    text_position VARCHAR(24) NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                );
                CREATE TABLE media_fonts (
                    id INTEGER PRIMARY KEY,
                    family VARCHAR(80) NOT NULL,
                    display_name VARCHAR(120) NOT NULL,
                    provider VARCHAR(24) NOT NULL,
                    active BOOLEAN NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                );
                CREATE TABLE signage_settings (
                    id INTEGER PRIMARY KEY,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                );
                """
            )
            connection.execute(
                """
                INSERT INTO displays (
                    id, name, location, status, orientation, resolution_width, resolution_height,
                    notes, created_at, updated_at
                ) VALUES (1, 'Legacy Lobby', 'Main floor', 'ONLINE', 'LANDSCAPE', 1920, 1080, 'Keep me', ?, ?)
                """,
                (created_at, created_at),
            )
            connection.execute(
                """
                INSERT INTO schedules (
                    id, name, status, starts_at, ends_at, weekdays, default_duration_seconds,
                    notes, created_at, updated_at
                ) VALUES (1, 'Legacy Schedule', 'ACTIVE', '2026-01-01 08:00:00', NULL, 'MON,TUE', 45, 'Keep schedule', ?, ?)
                """,
                (created_at, created_at),
            )
            connection.execute(
                """
                INSERT INTO media_assets (
                    id, title, media_type, body, notes, created_at, updated_at
                ) VALUES (1, 'Legacy Slider', 'SLIDER', NULL, 'Keep media', ?, ?)
                """,
                (created_at, created_at),
            )
            connection.execute(
                """
                INSERT INTO media_slides (
                    id, media_asset_id, sort_order, background_file_path, background_original_filename,
                    text, text_position, duration_seconds, created_at, updated_at
                ) VALUES (1, 1, 0, 'legacy-bg.png', 'legacy-bg.png', 'Legacy text', 'CENTER', 12, ?, ?)
                """,
                (created_at, created_at),
            )
            connection.execute(
                """
                INSERT INTO media_fonts (
                    id, family, display_name, provider, active, created_at, updated_at
                ) VALUES (1, 'Legacy Font', 'Legacy Font', 'GOOGLE', 1, ?, ?)
                """,
                (created_at, created_at),
            )
            connection.execute(
                "INSERT INTO signage_settings (id, created_at, updated_at) VALUES (1, ?, ?)",
                (created_at, created_at),
            )

        app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
                "MEDIA_UPLOAD_FOLDER": str(temp_path / "media"),
            }
        )

        with app.app_context():
            inspector = db.inspect(db.engine)
            media_columns = {column["name"] for column in inspector.get_columns("media_assets")}
            display_columns = {column["name"] for column in inspector.get_columns("displays")}
            schedule_columns = {column["name"] for column in inspector.get_columns("schedules")}
            slide_columns = {column["name"] for column in inspector.get_columns("media_slides")}
            font_columns = {column["name"] for column in inspector.get_columns("media_fonts")}
            settings_columns = {column["name"] for column in inspector.get_columns("signage_settings")}

            self.assertTrue(
                {
                    "neon_text_color",
                    "neon_frame_color",
                    "neon_background_color",
                    "neon_font_family",
                    "neon_font_size",
                    "neon_frame_thickness",
                    "vcard_name",
                    "vcard_phone",
                    "vcard_email",
                    "vcard_address",
                    "vcard_url",
                    "vcard_top_text",
                    "vcard_bottom_text",
                }.issubset(media_columns)
            )
            self.assertTrue(
                {
                    "player_token_hash",
                    "player_token_enabled",
                    "player_access_key",
                    "player_token_created_at",
                    "player_token_last_used_at",
                }.issubset(display_columns)
            )
            self.assertIn("times_are_utc", schedule_columns)
            self.assertTrue(
                {
                    "foreground_file_path",
                    "foreground_original_filename",
                    "foreground_size",
                    "foreground_position",
                    "foreground_animation",
                    "text_font_family",
                    "text_font_size",
                    "text_animation",
                }.issubset(slide_columns)
            )
            self.assertTrue({"local_css_path", "download_status", "download_error"}.issubset(font_columns))
            self.assertTrue(
                {
                    "logo_enabled",
                    "logo_position",
                    "logo_file_path",
                    "logo_original_filename",
                    "logo_mime_type",
                }.issubset(settings_columns)
            )

            display_row = db.session.execute(
                db.text("SELECT name, notes, player_token_enabled FROM displays WHERE id = 1")
            ).one()
            schedule_row = db.session.execute(
                db.text("SELECT name, notes, times_are_utc FROM schedules WHERE id = 1")
            ).one()
            slide_row = db.session.execute(
                db.text(
                    """
                    SELECT text, foreground_size, foreground_position, foreground_animation,
                           text_font_family, text_font_size, text_animation
                    FROM media_slides WHERE id = 1
                    """
                )
            ).one()
            settings_row = db.session.execute(
                db.text("SELECT logo_enabled, logo_position FROM signage_settings WHERE id = 1")
            ).one()

            self.assertEqual(display_row.name, "Legacy Lobby")
            self.assertEqual(display_row.notes, "Keep me")
            self.assertEqual(display_row.player_token_enabled, 0)
            self.assertEqual(schedule_row.name, "Legacy Schedule")
            self.assertEqual(schedule_row.notes, "Keep schedule")
            self.assertEqual(schedule_row.times_are_utc, 0)
            self.assertEqual(slide_row.text, "Legacy text")
            self.assertEqual(slide_row.foreground_size, 50)
            self.assertEqual(slide_row.foreground_position, "CENTER")
            self.assertEqual(slide_row.foreground_animation, "NONE")
            self.assertEqual(slide_row.text_font_family, "Inter")
            self.assertEqual(slide_row.text_font_size, 72)
            self.assertEqual(slide_row.text_animation, "NONE")
            self.assertEqual(settings_row.logo_enabled, 0)
            self.assertEqual(settings_row.logo_position, "TOP_RIGHT")


if __name__ == "__main__":
    unittest.main()
