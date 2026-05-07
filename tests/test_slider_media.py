from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from macrosignage.app import create_app
from macrosignage.extensions import db
from macrosignage.features.auth.models import User
from macrosignage.features.auth.services import hash_password
from macrosignage.features.displays.models import Display
from macrosignage.features.displays.services import rotate_player_token
from macrosignage.features.media.models import MediaAsset, MediaFont
from macrosignage.features.media.services import vcard_payload
from macrosignage.features.schedules.models import Schedule


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

    def mark_font_downloaded(self, font):
        slug = font.family.lower().replace(" ", "-")
        font.local_css_path = f"fonts/{slug}/font.css"
        font.download_status = "LOCAL"
        font.download_error = None

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

    def create_active_schedule(self, display, media):
        now = datetime.now(timezone.utc)
        schedule = Schedule(
            name="Slider Playback",
            status="ACTIVE",
            starts_at=now - timedelta(hours=1),
            ends_at=now + timedelta(hours=1),
            displays=[display],
            media_assets=[media],
        )
        db.session.add(schedule)
        db.session.commit()
        return schedule

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
        self.create_active_schedule(display, media)
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

        with patch("macrosignage.features.admin.routes.download_font_assets", side_effect=self.mark_font_downloaded):
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
        font = MediaFont.query.filter_by(family="Roboto Condensed").one()
        self.assertEqual(font.local_css_path, "fonts/roboto-condensed/font.css")

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
        self.create_active_schedule(display, media)
        self.authorize_display(display)

        player = self.client.get(f"/displays/{display.id}/play")
        body = player.get_data(as_text=True)
        self.assertIn("/displays/uploads/fonts/roboto-condensed/font.css", body)
        self.assertNotIn("Roboto+Condensed", body)
        self.assertIn("font-family: 'Roboto Condensed', sans-serif; font-size: 88px;", body)

    def test_create_neon_sign_media_and_render_display_player(self):
        display = self.create_display()

        response = self.client.post(
            "/admin/media/new",
            data={
                "title": "Open Sign",
                "media_type": "NEON_SIGN",
                "display_ids": str(display.id),
                "body": "Open Late",
                "neon_text_color": "#ff33cc",
                "neon_frame_color": "#33ff77",
                "neon_background_color": "#201514",
                "neon_font_family": "Montserrat",
                "neon_font_size": "144",
                "neon_frame_thickness": "18",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        media = MediaAsset.query.filter_by(title="Open Sign").one()
        self.assertEqual(media.media_type, "NEON_SIGN")
        self.assertEqual(media.body, "Open Late")
        self.assertEqual(media.neon_text_color, "#ff33cc")
        self.assertEqual(media.neon_frame_color, "#33ff77")
        self.assertEqual(media.neon_background_color, "#201514")
        self.assertEqual(media.neon_font_family, "Montserrat")
        self.assertEqual(media.neon_font_size, 144)
        self.assertEqual(media.neon_frame_thickness, 18)
        self.create_active_schedule(display, media)
        self.authorize_display(display)

        player = self.client.get(f"/displays/{display.id}/play")
        self.assertEqual(player.status_code, 200)
        body = player.get_data(as_text=True)
        self.assertIn("display-neon-sign", body)
        self.assertIn("Open Late", body)
        self.assertIn("--neon-text-color: #ff33cc", body)
        self.assertIn("--neon-frame-color: #33ff77", body)
        self.assertIn("--neon-background-color: #201514", body)
        self.assertIn("--neon-font-size: 144px", body)
        self.assertIn("--neon-frame-thickness: 18px", body)
        self.assertIn("font-family: 'Montserrat', sans-serif;", body)
        self.assertIn("Montserrat", body)

    def test_text_elements_accept_literal_newline_sequence(self):
        display = self.create_display()

        text_response = self.client.post(
            "/admin/media/new",
            data={
                "title": "Line Break Text",
                "media_type": "TEXT",
                "display_ids": str(display.id),
                "body": "First line\\nSecond line",
            },
            follow_redirects=False,
        )
        self.assertEqual(text_response.status_code, 302)
        text_media = MediaAsset.query.filter_by(title="Line Break Text").one()
        self.assertEqual(text_media.body, "First line\nSecond line")

        slider_response = self.client.post(
            "/admin/media/new",
            data={
                "title": "Line Break Slider",
                "media_type": "SLIDER",
                "display_ids": str(display.id),
                "slider_slide_count": "1",
                "slider_background_0": self.image_file("background.png"),
                "slider_foreground_size_0": "50",
                "slider_foreground_position_0": "CENTER",
                "slider_foreground_animation_0": "NONE",
                "slider_text_0": "Menu\\nSpecials",
                "slider_text_position_0": "CENTER",
                "slider_text_animation_0": "NONE",
                "slider_font_family_0": "Inter",
                "slider_font_size_0": "88",
                "slider_duration_0": "9",
            },
            follow_redirects=False,
        )
        self.assertEqual(slider_response.status_code, 302)
        slider_media = MediaAsset.query.filter_by(title="Line Break Slider").one()
        self.assertEqual(slider_media.slider_slides[0].text, "Menu\nSpecials")

        vcard_response = self.client.post(
            "/admin/media/new",
            data={
                "title": "Line Break vCard",
                "media_type": "VCARD",
                "display_ids": str(display.id),
                "vcard_name": "Javier Baez",
                "vcard_phone": "+1 555 0100",
                "vcard_top_text": "Scan\\nHere",
                "vcard_bottom_text": "Save\\nContact",
            },
            follow_redirects=False,
        )
        self.assertEqual(vcard_response.status_code, 302)
        vcard_media = MediaAsset.query.filter_by(title="Line Break vCard").one()
        self.assertEqual(vcard_media.vcard_top_text, "Scan\nHere")
        self.assertEqual(vcard_media.vcard_bottom_text, "Save\nContact")

    def test_neon_sign_rejects_invalid_color(self):
        response = self.client.post(
            "/admin/media/new",
            data={
                "title": "Bad Neon",
                "media_type": "NEON_SIGN",
                "body": "Broken",
                "neon_text_color": "hotpink",
                "neon_frame_color": "#33ff77",
                "neon_background_color": "#201514",
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertIn("Neon text color must be a 6-digit hex color.", response.get_data(as_text=True))

    def test_neon_sign_rejects_invalid_font_and_frame_values(self):
        response = self.client.post(
            "/admin/media/new",
            data={
                "title": "Bad Neon Settings",
                "media_type": "NEON_SIGN",
                "body": "Broken",
                "neon_text_color": "#ff33cc",
                "neon_frame_color": "#33ff77",
                "neon_background_color": "#201514",
                "neon_font_family": "Missing Font",
                "neon_font_size": "10",
                "neon_frame_thickness": "80",
            },
        )

        self.assertEqual(response.status_code, 422)
        body = response.get_data(as_text=True)
        self.assertIn("Choose a valid font style.", body)
        self.assertIn("Font size must be between 24 and 260 pixels.", body)
        self.assertIn("Frame thickness must be between 2 and 48 pixels.", body)

    def test_create_vcard_media_and_render_display_player(self):
        display = self.create_display()

        response = self.client.post(
            "/admin/media/new",
            data={
                "title": "Sales Contact",
                "media_type": "VCARD",
                "display_ids": str(display.id),
                "vcard_name": "Javier Baez",
                "vcard_phone": "+1 555 0100",
                "vcard_email": "sales@example.com",
                "vcard_address": "123 Main Street, Chicago, IL",
                "vcard_url": "https://example.com",
                "vcard_top_text": "Scan to save our contact",
                "vcard_bottom_text": "We will follow up today",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        media = MediaAsset.query.filter_by(title="Sales Contact").one()
        self.assertEqual(media.media_type, "VCARD")
        self.assertEqual(media.vcard_name, "Javier Baez")
        self.assertEqual(media.vcard_phone, "+1 555 0100")
        self.assertEqual(media.vcard_email, "sales@example.com")
        self.assertEqual(media.vcard_address, "123 Main Street, Chicago, IL")
        self.assertEqual(media.vcard_url, "https://example.com")
        self.assertEqual(media.vcard_top_text, "Scan to save our contact")
        self.assertEqual(media.vcard_bottom_text, "We will follow up today")
        self.create_active_schedule(display, media)
        self.authorize_display(display)

        player = self.client.get(f"/displays/{display.id}/play")
        self.assertEqual(player.status_code, 200)
        body = player.get_data(as_text=True)
        self.assertIn("display-vcard", body)
        self.assertIn("display-vcard-qr", body)
        self.assertIn("Scan to save our contact", body)
        self.assertIn("We will follow up today", body)
        self.assertIn("<svg", body)

    def test_vcard_requires_name_and_contact_detail(self):
        response = self.client.post(
            "/admin/media/new",
            data={
                "title": "Missing Contact",
                "media_type": "VCARD",
                "vcard_name": "",
                "vcard_phone": "",
                "vcard_email": "",
                "vcard_address": "",
                "vcard_url": "",
            },
        )

        self.assertEqual(response.status_code, 422)
        body = response.get_data(as_text=True)
        self.assertIn("Contact name is required.", body)
        self.assertIn("Enter at least one phone, email, address, or URL.", body)

    def test_vcard_payload_escapes_contact_values(self):
        media = MediaAsset(
            title="Contact",
            media_type="VCARD",
            vcard_name="Example, Inc.",
            vcard_phone="+1 555 0100",
            vcard_email="sales@example.com",
            vcard_address="123 Main Street; Suite 5",
            vcard_url="https://example.com/contact",
        )

        payload = vcard_payload(media)

        self.assertIn("BEGIN:VCARD", payload)
        self.assertIn("VERSION:3.0", payload)
        self.assertIn("FN:Example\\, Inc.", payload)
        self.assertIn("ADR;TYPE=WORK:;;123 Main Street\\; Suite 5;;;;", payload)
        self.assertIn("END:VCARD", payload)


if __name__ == "__main__":
    unittest.main()
