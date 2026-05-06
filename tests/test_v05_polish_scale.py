from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from macrosignage.app import create_app
from macrosignage.extensions import db
from macrosignage.features.auth.models import ApiToken, User
from macrosignage.features.auth.services import create_api_token, hash_password, revoke_api_token
from macrosignage.features.displays.models import Display
from macrosignage.features.displays.services import rotate_player_token
from macrosignage.features.media.models import MediaAsset


class PolishScaleTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "test.sqlite3"
        self.app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{self.db_path}",
                "MEDIA_UPLOAD_FOLDER": str(Path(self.tempdir.name) / "media"),
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

    def login(self, username: str):
        return self.client.post(
            "/auth/login",
            data={"identifier": username, "password": "password123"},
            follow_redirects=False,
        )

    def api_headers(self, user: User) -> dict[str, str]:
        _api_token, plaintext = create_api_token(user, f"{user.username} token")
        db.session.commit()
        return {"Authorization": f"Bearer {plaintext}"}

    def test_admin_editor_viewer_rbac_for_admin_routes(self):
        admin = self.create_user("admin-user", "ADMIN")
        editor = self.create_user("editor-user", "EDITOR")
        viewer = self.create_user("viewer-user", "VIEWER")

        self.login(viewer.username)
        self.assertEqual(self.client.get("/admin/displays/").status_code, 200)
        self.assertEqual(self.client.post("/admin/displays/new", data={}).status_code, 403)

        self.client.post("/auth/logout")
        self.login(editor.username)
        self.assertEqual(self.client.post("/admin/users/new", data={}).status_code, 403)
        response = self.client.post(
            "/admin/displays/new",
            data={
                "name": "Lobby",
                "status": "ONLINE",
                "orientation": "LANDSCAPE",
                "resolution_width": "1920",
                "resolution_height": "1080",
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)

        self.client.post("/auth/logout")
        self.login(admin.username)
        self.assertEqual(self.client.get("/admin/api-tokens/").status_code, 200)

    def test_api_tokens_enforce_owner_role(self):
        editor = self.create_user("editor-api", "EDITOR")
        viewer = self.create_user("viewer-api", "VIEWER")
        editor_headers = self.api_headers(editor)
        viewer_headers = self.api_headers(viewer)

        response = self.client.post(
            "/api/v1/displays",
            json={"name": "API Display", "status": "ONLINE", "orientation": "LANDSCAPE"},
            headers=editor_headers,
        )
        self.assertEqual(response.status_code, 201)
        display_id = response.get_json()["data"]["id"]

        response = self.client.get("/api/v1/displays", headers=viewer_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"][0]["id"], display_id)

        response = self.client.post(
            "/api/v1/displays",
            json={"name": "Denied"},
            headers=viewer_headers,
        )
        self.assertEqual(response.status_code, 403)

        token = editor.api_tokens[0]
        revoke_api_token(token)
        db.session.commit()
        self.assertEqual(self.client.get("/api/v1/displays", headers=editor_headers).status_code, 401)

    def test_admin_can_reset_api_token_and_old_secret_stops_working(self):
        admin = self.create_user("token-admin", "ADMIN")
        editor = self.create_user("reset-editor", "EDITOR")
        api_token, plaintext = create_api_token(editor, "Reset me")
        db.session.commit()
        old_hash = api_token.token_hash

        self.assertEqual(self.login(admin.username).status_code, 302)
        response = self.client.post(f"/admin/api-tokens/{api_token.id}/reset")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Copy this token now", body)
        self.assertIn("Reset me", body)

        db.session.refresh(api_token)
        self.assertTrue(api_token.active)
        self.assertIsNone(api_token.last_used_at)
        self.assertNotEqual(api_token.token_hash, old_hash)
        self.assertNotIn(api_token.token_hash, body)

        self.assertEqual(
            self.client.get("/api/v1/displays", headers={"Authorization": f"Bearer {plaintext}"}).status_code,
            401,
        )

        token_match = re.search(r"<code class=\"d-block text-break\">([^<]+)</code>", body)
        self.assertIsNotNone(token_match)
        rotated_plaintext = token_match.group(1)
        self.assertEqual(
            self.client.get("/api/v1/displays", headers={"Authorization": f"Bearer {rotated_plaintext}"}).status_code,
            200,
        )

    def test_admin_can_delete_api_token(self):
        admin = self.create_user("delete-admin", "ADMIN")
        editor = self.create_user("delete-editor", "EDITOR")
        api_token, plaintext = create_api_token(editor, "Delete me")
        db.session.commit()
        token_id = api_token.id

        self.assertEqual(self.login(admin.username).status_code, 302)
        response = self.client.post(f"/admin/api-tokens/{token_id}/delete", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(db.session.get(ApiToken, token_id))
        self.assertEqual(
            self.client.get("/api/v1/displays", headers={"Authorization": f"Bearer {plaintext}"}).status_code,
            401,
        )

    def test_api_media_schedule_and_player_playlist(self):
        editor = self.create_user("playlist-editor", "EDITOR")
        headers = self.api_headers(editor)
        display = Display(name="Player", status="ONLINE")
        db.session.add(display)
        db.session.commit()

        media_response = self.client.post(
            "/api/v1/media",
            json={
                "title": "Welcome",
                "mediaType": "TEXT",
                "body": "Hello",
                "displayIds": [display.id],
            },
            headers=headers,
        )
        self.assertEqual(media_response.status_code, 201)
        media_id = media_response.get_json()["data"]["id"]

        schedule_response = self.client.post(
            "/api/v1/schedules",
            json={
                "name": "Default",
                "status": "ACTIVE",
                "defaultDurationSeconds": 20,
                "displayIds": [display.id],
                "mediaIds": [media_id],
            },
            headers=headers,
        )
        self.assertEqual(schedule_response.status_code, 201)

        player_token = rotate_player_token(display)
        db.session.commit()
        response = self.client.get(
            f"/api/v1/player/displays/{display.id}/playlist",
            headers={"X-Display-Token": player_token},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()["data"]
        self.assertEqual(data["status"], "ONLINE")
        self.assertEqual(data["media"][0]["id"], media_id)

    def test_sse_event_stream_contains_content_version(self):
        user = self.create_user("player-admin", "ADMIN")
        self.login(user.username)
        display = Display(name="Event Display", status="ONLINE")
        db.session.add(display)
        token = rotate_player_token(display)
        db.session.commit()

        pair_response = self.client.post(f"/displays/{display.id}/pair", data={"token": token})
        self.assertEqual(pair_response.status_code, 302)

        response = self.client.get(f"/displays/{display.id}/events", buffered=False)
        first_chunk = next(response.response).decode("utf-8")
        self.assertIn("event: content.updated", first_chunk)
        self.assertIn("contentVersion", first_chunk)


if __name__ == "__main__":
    unittest.main()
