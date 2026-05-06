from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from macrosignage.app import create_app
from macrosignage.extensions import db
from macrosignage.features.admin.services import recent_dashboard_activities
from macrosignage.features.auth.models import User
from macrosignage.features.auth.services import hash_password
from macrosignage.features.displays.models import Display
from macrosignage.features.media.models import MediaAsset
from macrosignage.features.schedules.models import Schedule


class AdminDashboardTestCase(unittest.TestCase):
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

    def create_admin(self):
        user = User(
            username="site-admin",
            email="admin@example.com",
            password_hash=hash_password("password123"),
            role="ADMIN",
            active=True,
        )
        db.session.add(user)
        db.session.commit()
        return user

    def login(self):
        return self.client.post(
            "/auth/login",
            data={"identifier": "site-admin", "password": "password123"},
            follow_redirects=False,
        )

    def seed_recent_activity(self):
        now = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)
        display = Display(
            name="Lobby Display",
            status="ONLINE",
            created_at=now - timedelta(days=4),
            updated_at=now - timedelta(days=4),
            player_token_last_used_at=now,
        )
        media = MediaAsset(
            title="Welcome Reel",
            media_type="VIDEO",
            created_at=now - timedelta(days=3),
            updated_at=now - timedelta(minutes=20),
        )
        schedule = Schedule(
            name="Morning Rotation",
            status="ACTIVE",
            created_at=now - timedelta(days=2),
            updated_at=now - timedelta(days=2),
        )
        db.session.add_all([display, media, schedule])
        db.session.commit()
        return display, media, schedule

    def test_recent_dashboard_activity_service_sorts_newest_first(self):
        display, media, schedule = self.seed_recent_activity()

        activities = recent_dashboard_activities(limit=3)

        self.assertEqual([activity.title for activity in activities], ["Player check-in", "Media updated", "Schedule created"])
        self.assertEqual(activities[0].subject, display.name)
        self.assertEqual(activities[0].endpoint, "admin_displays.get_display_view")
        self.assertEqual(activities[1].subject, media.title)
        self.assertEqual(activities[2].subject, schedule.name)

    def test_dashboard_renders_recent_activity(self):
        self.create_admin()
        self.seed_recent_activity()
        self.assertEqual(self.login().status_code, 302)

        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Recent Activity", body)
        self.assertIn("Player check-in", body)
        self.assertIn("Lobby Display", body)
        self.assertIn("Media updated", body)
        self.assertIn("Welcome Reel", body)
        self.assertNotIn("No activity yet", body)


if __name__ == "__main__":
    unittest.main()
