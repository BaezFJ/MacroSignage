from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from macrosignage.app import create_app
from macrosignage.extensions import db
from macrosignage.features.auth.models import ApiToken, User
from macrosignage.features.auth.services import hash_password
from macrosignage.features.displays.models import Display
from macrosignage.features.media.models import MediaAsset, MediaFont
from macrosignage.features.media.services import download_font_assets
from macrosignage.features.schedules.models import Schedule


class AdminCrudTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        temp_path = Path(self.tempdir.name)
        self.app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{temp_path / 'test.sqlite3'}",
                "MEDIA_UPLOAD_FOLDER": str(temp_path / "media"),
            }
        )
        self.context = self.app.app_context()
        self.context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()
        self.tempdir.cleanup()

    def create_user(self, username="site-admin", role="ADMIN"):
        user = User(
            username=username,
            email=f"{username}@example.com",
            password_hash=hash_password("password123"),
            role=role,
            active=True,
        )
        db.session.add(user)
        db.session.commit()
        return user

    def login(self, username="site-admin"):
        return self.client.post(
            "/auth/login",
            data={"identifier": username, "password": "password123"},
            follow_redirects=False,
        )

    def mark_font_downloaded(self, font):
        slug = font.family.lower().replace(" ", "-")
        font.local_css_path = f"fonts/{slug}/font.css"
        font.download_status = "LOCAL"
        font.download_error = None

    def test_display_crud_validation_and_viewer_permission_failure(self):
        self.create_user("viewer-user", "VIEWER")
        self.assertEqual(self.login("viewer-user").status_code, 302)
        self.assertEqual(self.client.get("/admin/displays/").status_code, 200)
        self.assertEqual(self.client.post("/admin/displays/new", data={}).status_code, 403)

        self.client.post("/auth/logout")
        self.create_user()
        self.assertEqual(self.login().status_code, 302)

        invalid = self.client.post("/admin/displays/new", data={})
        self.assertEqual(invalid.status_code, 422)
        self.assertIn("Display name is required.", invalid.get_data(as_text=True))

        created = self.client.post(
            "/admin/displays/new",
            data={
                "name": "Lobby Display",
                "location": "Lobby",
                "status": "ONLINE",
                "orientation": "LANDSCAPE",
                "resolution_width": "1920",
                "resolution_height": "1080",
                "notes": "Entry signage",
            },
            follow_redirects=False,
        )
        self.assertEqual(created.status_code, 302)
        display = Display.query.one()
        self.assertEqual(display.name, "Lobby Display")

        edited = self.client.post(
            f"/admin/displays/{display.id}/edit",
            data={
                "name": "Lobby Portrait",
                "location": "Lobby",
                "status": "MAINTENANCE",
                "orientation": "PORTRAIT",
                "resolution_width": "1080",
                "resolution_height": "1920",
                "notes": "Maintenance test",
            },
            follow_redirects=False,
        )
        self.assertEqual(edited.status_code, 302)
        db.session.refresh(display)
        self.assertEqual(display.name, "Lobby Portrait")
        self.assertEqual(display.status, "MAINTENANCE")
        self.assertEqual(display.orientation, "PORTRAIT")

        deleted = self.client.post(f"/admin/displays/{display.id}/delete", follow_redirects=False)
        self.assertEqual(deleted.status_code, 302)
        self.assertIsNone(db.session.get(Display, display.id))

    def test_media_crud_validation_and_relationships(self):
        self.create_user()
        self.assertEqual(self.login().status_code, 302)
        display = Display(name="Media Display", status="ONLINE")
        db.session.add(display)
        db.session.commit()

        invalid = self.client.post(
            "/admin/media/new",
            data={"title": "", "media_type": "TEXT", "body": "", "display_ids": [str(display.id)]},
        )
        self.assertEqual(invalid.status_code, 422)
        body = invalid.get_data(as_text=True)
        self.assertIn("Media title is required.", body)
        self.assertIn("Content is required for this media type.", body)

        created = self.client.post(
            "/admin/media/new",
            data={
                "title": "Welcome Text",
                "media_type": "TEXT",
                "body": "Welcome",
                "notes": "Morning message",
                "display_ids": [str(display.id)],
            },
            follow_redirects=False,
        )
        self.assertEqual(created.status_code, 302)
        media = MediaAsset.query.one()
        self.assertEqual(media.title, "Welcome Text")
        self.assertEqual([item.id for item in media.displays], [display.id])

        edited = self.client.post(
            f"/admin/media/{media.id}/edit",
            data={
                "title": "Updated Welcome",
                "media_type": "HTML",
                "body": "<p>Updated</p>",
                "notes": "Updated note",
                "display_ids": [str(display.id)],
            },
            follow_redirects=False,
        )
        self.assertEqual(edited.status_code, 302)
        db.session.refresh(media)
        self.assertEqual(media.title, "Updated Welcome")
        self.assertEqual(media.media_type, "HTML")

        deleted = self.client.post(f"/admin/media/{media.id}/delete", follow_redirects=False)
        self.assertEqual(deleted.status_code, 302)
        self.assertIsNone(db.session.get(MediaAsset, media.id))

    def test_schedule_crud_validation_and_relationships(self):
        self.create_user()
        self.assertEqual(self.login().status_code, 302)
        display = Display(name="Schedule Display", status="ONLINE")
        media = MediaAsset(title="Schedule Media", media_type="TEXT", body="Hello")
        db.session.add_all([display, media])
        db.session.commit()

        invalid = self.client.post(
            "/admin/schedules/new",
            data={
                "name": "",
                "status": "ACTIVE",
                "starts_at": "2026-01-01T12:00",
                "ends_at": "2026-01-01T11:00",
                "default_duration_seconds": "30",
            },
        )
        self.assertEqual(invalid.status_code, 422)
        body = invalid.get_data(as_text=True)
        self.assertIn("Schedule name is required.", body)
        self.assertIn("End time must be after the start time.", body)

        created = self.client.post(
            "/admin/schedules/new",
            data={
                "name": "Morning Schedule",
                "status": "ACTIVE",
                "starts_at": "2026-01-01T08:00",
                "ends_at": "2026-01-01T12:00",
                "default_duration_seconds": "45",
                "weekdays": ["MON", "TUE"],
                "display_ids": [str(display.id)],
                "media_ids": [str(media.id)],
            },
            follow_redirects=False,
        )
        self.assertEqual(created.status_code, 302)
        schedule = Schedule.query.one()
        self.assertEqual(schedule.name, "Morning Schedule")
        self.assertEqual(schedule.weekday_values, ["MON", "TUE"])
        self.assertEqual([item.id for item in schedule.displays], [display.id])
        self.assertEqual([item.id for item in schedule.media_assets], [media.id])

        edited = self.client.post(
            f"/admin/schedules/{schedule.id}/edit",
            data={
                "name": "Paused Schedule",
                "status": "PAUSED",
                "starts_at": "",
                "ends_at": "",
                "default_duration_seconds": "60",
                "weekdays": ["WED"],
                "display_ids": [str(display.id)],
                "media_ids": [str(media.id)],
            },
            follow_redirects=False,
        )
        self.assertEqual(edited.status_code, 302)
        db.session.refresh(schedule)
        self.assertEqual(schedule.name, "Paused Schedule")
        self.assertEqual(schedule.status, "PAUSED")
        self.assertEqual(schedule.weekday_values, ["WED"])

        deleted = self.client.post(f"/admin/schedules/{schedule.id}/delete", follow_redirects=False)
        self.assertEqual(deleted.status_code, 302)
        self.assertIsNone(db.session.get(Schedule, schedule.id))

    def test_font_crud_validation_and_duplicate_failure(self):
        self.create_user()
        self.assertEqual(self.login().status_code, 302)

        invalid = self.client.post("/admin/settings/fonts/new", data={"family": "Bad/Font"})
        self.assertEqual(invalid.status_code, 422)
        self.assertIn("Use the Google Fonts family name without URL syntax.", invalid.get_data(as_text=True))

        with patch("macrosignage.features.admin.routes.download_font_assets", side_effect=self.mark_font_downloaded):
            created = self.client.post(
                "/admin/settings/fonts/new",
                data={"family": "Noto Sans", "display_name": "Noto Sans", "active": "on"},
                follow_redirects=False,
            )
        self.assertEqual(created.status_code, 302)
        font = MediaFont.query.filter_by(family="Noto Sans").one()
        self.assertEqual(font.download_status, "LOCAL")
        self.assertEqual(font.local_css_path, "fonts/noto-sans/font.css")

        duplicate = self.client.post(
            "/admin/settings/fonts/new",
            data={"family": "Noto Sans", "display_name": "Duplicate", "active": "on"},
        )
        self.assertEqual(duplicate.status_code, 422)
        self.assertIn("A font with this family already exists.", duplicate.get_data(as_text=True))

        with (
            patch("macrosignage.features.admin.routes.download_font_assets", side_effect=self.mark_font_downloaded),
            patch("macrosignage.features.admin.routes.delete_font_assets") as delete_assets,
        ):
            edited = self.client.post(
                f"/admin/settings/fonts/{font.id}/edit",
                data={"family": "Noto Serif", "display_name": "Noto Serif", "active": ""},
                follow_redirects=False,
            )
        self.assertEqual(edited.status_code, 302)
        db.session.refresh(font)
        self.assertEqual(font.family, "Noto Serif")
        self.assertFalse(font.active)
        self.assertEqual(font.local_css_path, "fonts/noto-serif/font.css")
        delete_assets.assert_called_once()

        with patch("macrosignage.features.admin.routes.delete_font_assets") as delete_assets:
            deleted = self.client.post(f"/admin/settings/fonts/{font.id}/delete", follow_redirects=False)
        self.assertEqual(deleted.status_code, 302)
        delete_assets.assert_called_once()
        self.assertIsNone(db.session.get(MediaFont, font.id))

    def test_download_font_assets_saves_google_css_and_font_file(self):
        font = MediaFont(family="Roboto Condensed", display_name="Roboto Condensed", provider="GOOGLE", active=True)
        css = (
            "@font-face{font-family:'Roboto Condensed';font-style:normal;font-weight:400;"
            "src:url(https://fonts.gstatic.com/s/robotocondensed/v1/font.woff2) format('woff2');}"
        ).encode()

        with patch(
            "macrosignage.features.media.services.fetch_font_url",
            side_effect=[css, b"font-bytes"],
        ):
            download_font_assets(font)

        css_path = Path(self.app.config["MEDIA_UPLOAD_FOLDER"]) / font.local_css_path
        font_files = list(css_path.parent.glob("*.woff2"))

        self.assertEqual(font.download_status, "LOCAL")
        self.assertIsNone(font.download_error)
        self.assertTrue(css_path.exists())
        self.assertEqual(len(font_files), 1)
        self.assertEqual(font_files[0].read_bytes(), b"font-bytes")
        self.assertNotIn("fonts.gstatic.com", css_path.read_text(encoding="utf-8"))

    def test_api_token_create_revoke_delete_validation(self):
        admin = self.create_user()
        owner = self.create_user("token-owner", "EDITOR")
        self.assertEqual(self.login(admin.username).status_code, 302)

        invalid = self.client.post("/admin/api-tokens/", data={"name": "", "user_id": ""})
        self.assertEqual(invalid.status_code, 422)
        body = invalid.get_data(as_text=True)
        self.assertIn("Token name is required.", body)
        self.assertIn("Choose an active token owner.", body)

        created = self.client.post(
            "/admin/api-tokens/",
            data={"name": "Editor API", "user_id": str(owner.id)},
        )
        self.assertEqual(created.status_code, 200)
        self.assertIn("Copy this token now", created.get_data(as_text=True))
        token = ApiToken.query.filter_by(name="Editor API").one()
        self.assertTrue(token.active)

        revoked = self.client.post(f"/admin/api-tokens/{token.id}/revoke", follow_redirects=False)
        self.assertEqual(revoked.status_code, 302)
        db.session.refresh(token)
        self.assertFalse(token.active)

        deleted = self.client.post(f"/admin/api-tokens/{token.id}/delete", follow_redirects=False)
        self.assertEqual(deleted.status_code, 302)
        self.assertIsNone(db.session.get(ApiToken, token.id))


if __name__ == "__main__":
    unittest.main()
