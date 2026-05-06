from __future__ import annotations

import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from macrosignage.app import create_app
from macrosignage.extensions import db
from macrosignage.features.auth.models import User
from macrosignage.features.auth.services import hash_password
from macrosignage.features.displays.models import Display
from macrosignage.features.displays.services import rotate_player_token
from macrosignage.features.media.models import MediaAsset, MediaFont


class SliderMediaTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.upload_path = Path(self.tempdir.name) / "media"
        self.db_path = Path(self.tempdir.name) / "test.sqlite3"
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

        db.session.add(
            User(
                username="site-admin",
                email="admin@example.com",
                password_hash=hash_password("password123"),
                role="ADMIN",
                active=True,
            )
        )
        db.session.commit()
        self.client.post(
            "/auth/login",
            data={"identifier": "site-admin", "password": "password123"},
        )

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

    def image_file(self, name: str):
        return BytesIO(b"image-bytes"), name, "image/png"

    def authorize_display(self, display):
        token = rotate_player_token(display)
        db.session.commit()
        self.client.post(f"/displays/{display.id}/pair", data={"token": token})
        return self.client.get(f"/displays/{display.id}/play")

    def test_create_slider_media_and_render_display_player(self):
        display = self.create_display()

        response = self.client.post(
            "/admin/media/new",
            data={
                "title": "Homepage Slider",
                "media_type": "SLIDER",
                "display_ids": str(display.id),
                "slider_slide_count": "2",
                "slider_background_0": self.image_file("background-1.png"),
                "slider_foreground_0": self.image_file("foreground-1.png"),
                "slider_foreground_size_0": "58",
                "slider_foreground_position_0": "TOP_RIGHT",
                "slider_foreground_animation_0": "zoomIn",
                "slider_text_0": "Welcome",
                "slider_text_position_0": "CENTER",
                "slider_text_animation_0": "fadeInUp",
                "slider_font_family_0": "Montserrat",
                "slider_font_size_0": "96",
                "slider_duration_0": "7",
                "slider_background_1": self.image_file("background-2.png"),
                "slider_foreground_size_1": "50",
                "slider_foreground_position_1": "CENTER",
                "slider_foreground_animation_1": "NONE",
                "slider_text_1": "Today's specials",
                "slider_text_position_1": "BOTTOM_CENTER",
                "slider_text_animation_1": "NONE",
                "slider_font_family_1": "Playfair Display",
                "slider_font_size_1": "64",
                "slider_duration_1": "11",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        media = MediaAsset.query.filter_by(title="Homepage Slider").one()
        self.assertEqual(media.media_type, "SLIDER")
        self.assertEqual(len(media.slider_slides), 2)
        self.assertEqual(media.slider_slides[0].duration_seconds, 7)
        self.assertEqual(media.slider_slides[0].foreground_size, 58)
        self.assertEqual(media.slider_slides[0].foreground_position, "TOP_RIGHT")
        self.assertEqual(media.slider_slides[0].foreground_animation, "zoomIn")
        self.assertEqual(media.slider_slides[0].text_font_family, "Montserrat")
        self.assertEqual(media.slider_slides[0].text_font_size, 96)
        self.assertEqual(media.slider_slides[0].text_animation, "fadeInUp")
        self.assertEqual(media.slider_slides[1].text_position, "BOTTOM_CENTER")
        self.assertEqual(media.slider_slides[1].text_font_family, "Playfair Display")
        self.assertTrue((self.upload_path / media.slider_slides[0].background_file_path).exists())
        self.assertTrue((self.upload_path / media.slider_slides[0].foreground_file_path).exists())
        self.authorize_display(display)

        player = self.client.get(f"/displays/{display.id}/play")
        self.assertEqual(player.status_code, 200)
        body = player.get_data(as_text=True)
        self.assertIn("data-player-slider", body)
        self.assertIn("Welcome", body)
        self.assertIn("Today&#39;s specials", body)
        self.assertIn("display-slider-content-bottom-center", body)
        self.assertIn("fonts.googleapis.com", body)
        self.assertIn("display-slider-foreground-top-right", body)
        self.assertIn("animate__zoomIn", body)
        self.assertIn("animate__fadeInUp", body)
        self.assertIn("data-animate-target", body)
        self.assertIn("style=\"width: 58%;\"", body)
        self.assertIn("font-family: 'Montserrat', sans-serif; font-size: 96px;", body)

    def test_add_google_font_and_use_it_for_slider_media(self):
        display = self.create_display()

        font_response = self.client.post(
            "/admin/settings/fonts/new",
            data={
                "family": "Roboto Condensed",
                "display_name": "Roboto Condensed",
                "active": "on",
            },
            follow_redirects=False,
        )

        self.assertEqual(font_response.status_code, 302)
        self.assertIsNotNone(MediaFont.query.filter_by(family="Roboto Condensed").one_or_none())

        form = self.client.get("/admin/media/new")
        self.assertEqual(form.status_code, 200)
        self.assertIn("Roboto Condensed", form.get_data(as_text=True))

        response = self.client.post(
            "/admin/media/new",
            data={
                "title": "Custom Font Slider",
                "media_type": "SLIDER",
                "display_ids": str(display.id),
                "slider_slide_count": "1",
                "slider_background_0": self.image_file("background.png"),
                "slider_foreground_size_0": "50",
                "slider_foreground_position_0": "CENTER",
                "slider_foreground_animation_0": "NONE",
                "slider_text_0": "Custom font",
                "slider_text_position_0": "CENTER",
                "slider_text_animation_0": "NONE",
                "slider_font_family_0": "Roboto Condensed",
                "slider_font_size_0": "88",
                "slider_duration_0": "9",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        media = MediaAsset.query.filter_by(title="Custom Font Slider").one()
        self.assertEqual(media.slider_slides[0].text_font_family, "Roboto Condensed")
        self.authorize_display(display)

        player = self.client.get(f"/displays/{display.id}/play")
        body = player.get_data(as_text=True)
        self.assertIn("Roboto+Condensed", body)
        self.assertIn("font-family: 'Roboto Condensed', sans-serif; font-size: 88px;", body)


if __name__ == "__main__":
    unittest.main()
