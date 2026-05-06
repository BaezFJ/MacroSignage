from __future__ import annotations

import tempfile
import unittest
import re
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

from macrosignage.app import create_app
from macrosignage.extensions import db
from macrosignage.features.admin.models import SignageSettings
from macrosignage.features.auth.models import User
from macrosignage.features.auth.services import hash_password
from macrosignage.features.displays.models import Display
from macrosignage.features.displays.services import display_playlist, rotate_player_token, schedule_is_playable
from macrosignage.features.media.models import MediaAsset
from macrosignage.features.schedules.models import Schedule


class DisplayPlayerTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "test.sqlite3"
        self.upload_path = Path(self.tempdir.name) / "media"
        self.app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{self.db_path}",
                "MEDIA_UPLOAD_FOLDER": str(self.upload_path),
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

    def create_display(self):
        display = Display(
            name="Lobby Display",
            status="ONLINE",
            orientation="LANDSCAPE",
            resolution_width=1920,
            resolution_height=1080,
        )
        db.session.add(display)
        db.session.commit()
        return display

    def create_media(self, title: str, media_type: str = "TEXT", source_url: str | None = None):
        media = MediaAsset(
            title=title,
            media_type=media_type,
            body=f"{title} body" if media_type == "TEXT" else None,
            source_url=source_url,
        )
        db.session.add(media)
        db.session.commit()
        return media

    def create_admin_user(self):
        user = User(
            username="site-admin",
            email="admin@example.com",
            password_hash=hash_password("password123"),
            role="ADMIN",
            active=True,
        )
        db.session.add(user)
        db.session.commit()
        self.client.post(
            "/auth/login",
            data={"identifier": "site-admin", "password": "password123"},
            follow_redirects=False,
        )
        return user

    def image_file(self, name: str):
        return BytesIO(b"logo-bytes"), name, "image/png"

    def authorize_display(self, display):
        token = rotate_player_token(display)
        db.session.commit()
        self.client.post(f"/displays/{display.id}/pair", data={"token": token})
        return self.client.get(f"/displays/{display.id}/play")

    def test_player_route_requires_token_then_remembers_client_and_can_be_disabled(self):
        self.create_admin_user()
        display = self.create_display()
        media = self.create_media("Welcome")
        display.media_assets = [media]
        db.session.commit()

        response = self.client.get(f"/displays/{display.id}/play")
        self.assertEqual(response.status_code, 401)
        self.assertIn("display-auth", response.get_data(as_text=True))

        response = self.client.post(f"/admin/displays/{display.id}/player-token/rotate")
        self.assertEqual(response.status_code, 200)
        admin_body = response.get_data(as_text=True)
        token_match = re.search(r'<code class="player-token-value">([^<]+)</code>', admin_body)
        self.assertIsNotNone(token_match)

        token = token_match.group(1)
        self.assertIsNotNone(display.player_token_hash)
        self.assertNotIn(token, display.player_token_hash)

        query_token_response = self.client.get(f"/displays/{display.id}/play?token={token}")
        self.assertEqual(query_token_response.status_code, 401)

        pair_response = self.client.post(f"/displays/{display.id}/pair", data={"token": token})
        self.assertEqual(pair_response.status_code, 302)

        response = self.client.get(f"/displays/{display.id}/play")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Welcome body", body)
        self.assertIn("display-player", body)

        remembered_response = self.client.get(f"/displays/{display.id}/play")
        self.assertEqual(remembered_response.status_code, 200)
        self.assertIn("Welcome body", remembered_response.get_data(as_text=True))

        response = self.client.post(f"/admin/displays/{display.id}/player-token/disable")
        self.assertEqual(response.status_code, 302)

        disabled_response = self.client.get(f"/displays/{display.id}/play")
        self.assertEqual(disabled_response.status_code, 401)
        self.assertIn("Display access disabled", disabled_response.get_data(as_text=True))

    def test_rotating_player_token_invalidates_existing_pairing_and_old_token(self):
        display = self.create_display()
        media = self.create_media("Welcome")
        display.media_assets = [media]
        first_token = rotate_player_token(display)
        db.session.commit()

        pair_response = self.client.post(f"/displays/{display.id}/pair", data={"token": first_token})
        self.assertEqual(pair_response.status_code, 302)
        response = self.client.get(f"/displays/{display.id}/play")
        self.assertEqual(response.status_code, 200)

        second_token = rotate_player_token(display)
        db.session.commit()

        old_session_response = self.client.get(f"/displays/{display.id}/play")
        self.assertEqual(old_session_response.status_code, 401)

        old_token_response = self.client.post(f"/displays/{display.id}/pair", data={"token": first_token})
        self.assertEqual(old_token_response.status_code, 401)

        pair_response = self.client.post(f"/displays/{display.id}/pair", data={"token": second_token})
        self.assertEqual(pair_response.status_code, 302)
        new_token_response = self.client.get(f"/displays/{display.id}/play")
        self.assertEqual(new_token_response.status_code, 200)

    def test_maintenance_display_renders_maintenance_page_instead_of_media(self):
        display = self.create_display()
        display.status = "MAINTENANCE"
        media = self.create_media("Welcome")
        display.media_assets = [media]
        db.session.commit()
        self.authorize_display(display)

        response = self.client.get(f"/displays/{display.id}/play")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("display-maintenance", body)
        self.assertIn("temporarily unavailable", body)
        self.assertNotIn("Welcome body", body)
        self.assertNotIn("display-player.js", body)

    def test_offline_display_renders_offline_page_instead_of_media(self):
        display = self.create_display()
        display.status = "OFFLINE"
        media = self.create_media("Welcome")
        display.media_assets = [media]
        db.session.commit()
        self.authorize_display(display)

        response = self.client.get(f"/displays/{display.id}/play")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("display-offline", body)
        self.assertIn("not currently available", body)
        self.assertNotIn("Welcome body", body)
        self.assertNotIn("display-player.js", body)

    def test_youtube_player_slide_autoplays_when_active(self):
        display = self.create_display()
        media = self.create_media(
            "Launch Video",
            media_type="YOUTUBE",
            source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )
        display.media_assets = [media]
        db.session.commit()
        self.authorize_display(display)

        response = self.client.get(f"/displays/{display.id}/play")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("data-player-youtube", body)
        self.assertIn("autoplay=1", body)
        self.assertIn("mute=1", body)
        self.assertIn("playsinline=1", body)
        self.assertNotIn('title="Launch Video"\n                                    src=', body)

    def test_global_logo_settings_render_and_hide_player_overlay(self):
        self.create_admin_user()
        display = self.create_display()
        media = self.create_media("Welcome")
        display.media_assets = [media]
        db.session.commit()
        self.authorize_display(display)

        settings_response = self.client.get("/admin/settings/")
        self.assertEqual(settings_response.status_code, 200)
        settings_body = settings_response.get_data(as_text=True)
        self.assertIn("Manage logo", settings_body)
        self.assertNotIn("logoUpload", settings_body)

        logo_response = self.client.get("/admin/settings/logo")
        self.assertEqual(logo_response.status_code, 200)
        logo_body = logo_response.get_data(as_text=True)
        self.assertIn("Logo Settings", logo_body)
        self.assertIn("logoUpload", logo_body)

        response = self.client.post(
            "/admin/settings/logo",
            data={
                "logo_enabled": "on",
                "logo_position": "BOTTOM_LEFT",
                "logo": self.image_file("logo.png"),
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        logo_settings = db.session.get(SignageSettings, 1)
        self.assertTrue(logo_settings.logo_enabled)
        self.assertEqual(logo_settings.logo_position, "BOTTOM_LEFT")
        self.assertTrue((self.upload_path / logo_settings.logo_file_path).exists())

        player = self.client.get(f"/displays/{display.id}/play")
        body = player.get_data(as_text=True)
        self.assertIn("display-logo-bottom-left", body)
        self.assertIn(f"/displays/uploads/{logo_settings.logo_file_path}", body)

        response = self.client.post(
            "/admin/settings/logo",
            data={"logo_position": "BOTTOM_LEFT"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        db.session.refresh(logo_settings)
        self.assertFalse(logo_settings.logo_enabled)

        player = self.client.get(f"/displays/{display.id}/play")
        self.assertNotIn("display-logo-bottom-left", player.get_data(as_text=True))

    def test_playlist_prefers_active_schedule_then_direct_media(self):
        now = datetime.now(timezone.utc)
        display = self.create_display()
        scheduled_media = self.create_media("Scheduled")
        direct_media = self.create_media("Direct")
        inactive_media = self.create_media("Inactive")
        display.media_assets = [direct_media, scheduled_media]

        active_schedule = Schedule(
            name="Morning",
            status="ACTIVE",
            starts_at=now - timedelta(hours=1),
            ends_at=now + timedelta(hours=1),
            default_duration_seconds=45,
            displays=[display],
            media_assets=[scheduled_media],
        )
        inactive_schedule = Schedule(
            name="Expired",
            status="ACTIVE",
            starts_at=now - timedelta(days=2),
            ends_at=now - timedelta(days=1),
            displays=[display],
            media_assets=[inactive_media],
        )
        db.session.add_all([active_schedule, inactive_schedule])
        db.session.commit()

        playlist, default_duration = display_playlist(display, now)
        self.assertEqual([media.title for media in playlist], ["Scheduled", "Direct"])
        self.assertEqual(default_duration, 45)
        self.assertTrue(schedule_is_playable(active_schedule, now))
        self.assertFalse(schedule_is_playable(inactive_schedule, now))


if __name__ == "__main__":
    unittest.main()
