from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from macrosignage.app import create_app
from macrosignage.extensions import db
from macrosignage.features.auth.models import User
from macrosignage.features.auth.services import hash_password, verify_password


class AuthFlowTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "test.sqlite3"
        self.app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{self.db_path}",
                "MEDIA_UPLOAD_FOLDER": str(Path(self.tempdir.name) / "media"),
                "AUTH_SHOW_RESET_LINKS": True,
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

    def create_user(self, *, username="site-admin", email="admin@example.com", password="password123", role="ADMIN"):
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=role,
            active=True,
        )
        db.session.add(user)
        db.session.commit()
        return user

    def login(self, identifier="site-admin", password="password123"):
        return self.client.post(
            "/auth/login",
            data={"identifier": identifier, "password": password},
            follow_redirects=False,
        )

    def test_setup_login_logout_and_admin_guard(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login", response.headers["Location"])

        response = self.client.get("/auth/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Create the first admin account", response.get_data(as_text=True))

        response = self.client.post(
            "/auth/setup",
            data={
                "username": "site-admin",
                "email": "admin@example.com",
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/", response.headers["Location"])

        user = User.query.one()
        self.assertEqual(user.role, "ADMIN")
        self.assertTrue(user.active)
        self.assertNotEqual(user.password_hash, "password123")
        self.assertTrue(verify_password(user, "password123"))

        self.assertEqual(self.client.get("/admin/users/").status_code, 200)

        response = self.client.post("/auth/logout", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login", response.headers["Location"])
        self.assertEqual(self.client.get("/admin/users/").status_code, 302)

        bad_login = self.client.post(
            "/auth/login",
            data={"identifier": "site-admin", "password": "wrong-password"},
        )
        self.assertEqual(bad_login.status_code, 422)

        good_login = self.login()
        self.assertEqual(good_login.status_code, 302)
        self.assertIn("/admin/", good_login.headers["Location"])

    def test_user_crud_and_final_admin_protection(self):
        admin = self.create_user()
        self.assertEqual(self.login().status_code, 302)

        response = self.client.post(
            "/admin/users/new",
            data={
                "username": "editor-user",
                "email": "editor@example.com",
                "role": "EDITOR",
                "active": "on",
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        editor = User.query.filter_by(username="editor-user").one()
        self.assertEqual(editor.role, "EDITOR")

        response = self.client.post(
            f"/admin/users/{editor.id}/edit",
            data={
                "username": "viewer-user",
                "email": "viewer@example.com",
                "role": "VIEWER",
                "active": "on",
                "password": "",
                "confirm_password": "",
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        db.session.refresh(editor)
        self.assertEqual(editor.username, "viewer-user")
        self.assertEqual(editor.role, "VIEWER")

        response = self.client.post(
            f"/admin/users/{admin.id}/edit",
            data={
                "username": "site-admin",
                "email": "admin@example.com",
                "role": "VIEWER",
                "password": "",
                "confirm_password": "",
            },
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("At least one active admin account is required.", response.get_data(as_text=True))

        response = self.client.post(f"/admin/users/{editor.id}/delete", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(db.session.get(User, editor.id))

    def test_password_reset_token_flow(self):
        self.create_user(email="reset@example.com", password="old-password")

        response = self.client.post(
            "/auth/password-reset",
            data={"email": "reset@example.com"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        match = re.search(r"/auth/password-reset/([A-Za-z0-9_-]+)", body)
        self.assertIsNotNone(match)
        token = match.group(1)

        response = self.client.post(
            f"/auth/password-reset/{token}",
            data={"password": "new-password", "confirm_password": "new-password"},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login", response.headers["Location"])

        self.assertEqual(self.login(identifier="reset@example.com", password="new-password").status_code, 302)


if __name__ == "__main__":
    unittest.main()
