from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from macrosignage.app import create_app
from macrosignage.extensions import db
from macrosignage.features.auth.models import User
from macrosignage.features.auth.services import create_api_token, hash_password
from macrosignage.features.displays.models import Display
from macrosignage.features.displays.services import rotate_player_token
from macrosignage.features.media.models import MediaAsset
from macrosignage.features.schedules.models import Schedule


class ApiContractTestCase(unittest.TestCase):
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

    def create_user(self, username: str, role: str) -> User:
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

    def headers_for(self, user: User) -> dict[str, str]:
        _token, plaintext = create_api_token(user, f"{user.username} token")
        db.session.commit()
        return {"Authorization": f"Bearer {plaintext}"}

    def test_api_authentication_and_authorization_failures(self):
        viewer = self.create_user("viewer", "VIEWER")
        viewer_headers = self.headers_for(viewer)

        missing = self.client.get("/api/v1/displays")
        self.assertEqual(missing.status_code, 401)
        self.assertEqual(missing.get_json()["error"]["code"], "UNAUTHENTICATED")

        invalid = self.client.get("/api/v1/displays", headers={"Authorization": "Bearer invalid"})
        self.assertEqual(invalid.status_code, 401)

        forbidden = self.client.post("/api/v1/displays", json={"name": "Denied"}, headers=viewer_headers)
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(forbidden.get_json()["error"]["code"], "FORBIDDEN")

    def test_display_api_crud_contract_and_validation(self):
        editor = self.create_user("display-editor", "EDITOR")
        headers = self.headers_for(editor)

        invalid = self.client.post("/api/v1/displays", json={"name": ""}, headers=headers)
        self.assertEqual(invalid.status_code, 422)
        self.assertEqual(invalid.get_json()["error"]["details"]["name"], "Display name is required.")

        created = self.client.post(
            "/api/v1/displays",
            json={
                "name": "API Lobby",
                "location": "Lobby",
                "status": "ONLINE",
                "orientation": "LANDSCAPE",
                "resolutionWidth": 1920,
                "resolutionHeight": 1080,
            },
            headers=headers,
        )
        self.assertEqual(created.status_code, 201)
        display_data = created.get_json()["data"]
        self.assertEqual(
            {"id", "name", "location", "status", "orientation", "resolutionWidth", "resolutionHeight"}.issubset(
                display_data
            ),
            True,
        )

        display_id = display_data["id"]
        listed = self.client.get("/api/v1/displays", headers=headers)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.get_json()["data"][0]["id"], display_id)

        fetched = self.client.get(f"/api/v1/displays/{display_id}", headers=headers)
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.get_json()["data"]["name"], "API Lobby")

        updated = self.client.patch(
            f"/api/v1/displays/{display_id}",
            json={"name": "API Lobby Updated", "status": "MAINTENANCE"},
            headers=headers,
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["data"]["name"], "API Lobby Updated")
        self.assertEqual(updated.get_json()["data"]["status"], "MAINTENANCE")

        deleted = self.client.delete(f"/api/v1/displays/{display_id}", headers=headers)
        self.assertEqual(deleted.status_code, 204)
        self.assertIsNone(db.session.get(Display, display_id))

    def test_media_api_crud_contract_and_validation(self):
        editor = self.create_user("media-editor", "EDITOR")
        headers = self.headers_for(editor)
        display = Display(name="Media Display", status="ONLINE")
        db.session.add(display)
        db.session.commit()

        invalid = self.client.post("/api/v1/media", json={"title": "", "mediaType": "TEXT"}, headers=headers)
        self.assertEqual(invalid.status_code, 422)
        self.assertIn("title", invalid.get_json()["error"]["details"])
        self.assertIn("body", invalid.get_json()["error"]["details"])

        created = self.client.post(
            "/api/v1/media",
            json={"title": "API Text", "mediaType": "TEXT", "body": "Hello", "displayIds": [display.id]},
            headers=headers,
        )
        self.assertEqual(created.status_code, 201)
        media_data = created.get_json()["data"]
        self.assertEqual(media_data["title"], "API Text")
        self.assertEqual(media_data["mediaType"], "TEXT")
        self.assertEqual(media_data["displayIds"], [display.id])
        media_id = media_data["id"]

        listed = self.client.get("/api/v1/media", headers=headers)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.get_json()["data"][0]["id"], media_id)

        fetched = self.client.get(f"/api/v1/media/{media_id}", headers=headers)
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.get_json()["data"]["body"], "Hello")

        updated = self.client.patch(
            f"/api/v1/media/{media_id}",
            json={"title": "API HTML", "mediaType": "HTML", "body": "<p>Hello</p>"},
            headers=headers,
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["data"]["mediaType"], "HTML")

        neon = self.client.post(
            "/api/v1/media",
            json={
                "title": "API Neon",
                "mediaType": "NEON_SIGN",
                "body": "Open",
                "neonTextColor": "#ff33cc",
                "neonFrameColor": "#33ff77",
                "neonBackgroundColor": "#201514",
            },
            headers=headers,
        )
        self.assertEqual(neon.status_code, 201)
        neon_data = neon.get_json()["data"]
        self.assertEqual(neon_data["mediaType"], "NEON_SIGN")
        self.assertEqual(neon_data["neonTextColor"], "#ff33cc")
        self.assertEqual(neon_data["neonFrameColor"], "#33ff77")
        self.assertEqual(neon_data["neonBackgroundColor"], "#201514")

        deleted = self.client.delete(f"/api/v1/media/{media_id}", headers=headers)
        self.assertEqual(deleted.status_code, 204)
        self.assertIsNone(db.session.get(MediaAsset, media_id))

    def test_schedule_api_crud_contract_and_validation(self):
        editor = self.create_user("schedule-editor", "EDITOR")
        headers = self.headers_for(editor)
        display = Display(name="Schedule Display", status="ONLINE")
        media = MediaAsset(title="Schedule Text", media_type="TEXT", body="Hello")
        db.session.add_all([display, media])
        db.session.commit()

        invalid = self.client.post("/api/v1/schedules", json={"name": "", "status": "BAD"}, headers=headers)
        self.assertEqual(invalid.status_code, 422)
        self.assertIn("name", invalid.get_json()["error"]["details"])
        self.assertIn("status", invalid.get_json()["error"]["details"])

        created = self.client.post(
            "/api/v1/schedules",
            json={
                "name": "API Schedule",
                "status": "ACTIVE",
                "startsAt": "2026-01-01T08:00:00",
                "endsAt": "2026-01-01T12:00:00",
                "weekdays": ["MON"],
                "defaultDurationSeconds": 20,
                "displayIds": [display.id],
                "mediaIds": [media.id],
            },
            headers=headers,
        )
        self.assertEqual(created.status_code, 201)
        schedule_data = created.get_json()["data"]
        self.assertEqual(schedule_data["name"], "API Schedule")
        self.assertEqual(schedule_data["displayIds"], [display.id])
        self.assertEqual(schedule_data["mediaIds"], [media.id])
        schedule_id = schedule_data["id"]

        listed = self.client.get("/api/v1/schedules", headers=headers)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.get_json()["data"][0]["id"], schedule_id)

        fetched = self.client.get(f"/api/v1/schedules/{schedule_id}", headers=headers)
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.get_json()["data"]["weekdays"], ["MON"])

        updated = self.client.patch(
            f"/api/v1/schedules/{schedule_id}",
            json={"name": "API Schedule Paused", "status": "PAUSED"},
            headers=headers,
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["data"]["status"], "PAUSED")

        deleted = self.client.delete(f"/api/v1/schedules/{schedule_id}", headers=headers)
        self.assertEqual(deleted.status_code, 204)
        self.assertIsNone(db.session.get(Schedule, schedule_id))

    def test_player_token_api_access_contract(self):
        display = Display(name="Player API", status="ONLINE")
        media = MediaAsset(title="Player Text", media_type="TEXT", body="Hello")
        schedule = Schedule(name="Player Schedule", status="ACTIVE", default_duration_seconds=30)
        display.schedules.append(schedule)
        schedule.media_assets.append(media)
        db.session.add_all([display, media, schedule])
        token = rotate_player_token(display)
        db.session.commit()

        denied = self.client.get(f"/api/v1/player/displays/{display.id}/playlist")
        self.assertEqual(denied.status_code, 401)
        self.assertEqual(denied.get_json()["error"]["code"], "UNAUTHENTICATED")

        allowed = self.client.get(
            f"/api/v1/player/displays/{display.id}/playlist",
            headers={"X-Display-Token": token},
        )
        self.assertEqual(allowed.status_code, 200)
        data = allowed.get_json()["data"]
        self.assertEqual(data["display"]["id"], display.id)
        self.assertEqual(data["status"], "ONLINE")
        self.assertEqual(data["media"][0]["id"], media.id)

        access_key = display.player_access_key
        allowed_again = self.client.get(
            f"/api/v1/player/displays/{display.id}/status",
            headers={"X-Display-Access-Key": access_key},
        )
        self.assertEqual(allowed_again.status_code, 200)
        self.assertEqual(allowed_again.get_json()["data"]["display"]["id"], display.id)


if __name__ == "__main__":
    unittest.main()
