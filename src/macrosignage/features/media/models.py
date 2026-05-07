from __future__ import annotations

from datetime import datetime, timezone

from macrosignage.extensions import db

from ..associations import display_media, schedule_media


DEFAULT_GOOGLE_FONT_FAMILIES = (
    "Inter",
    "Roboto",
    "Open Sans",
    "Lato",
    "Montserrat",
    "Poppins",
    "Oswald",
    "Playfair Display",
    "Merriweather",
    "Source Sans 3",
)


class MediaAsset(db.Model):
    __tablename__ = "media_assets"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    media_type = db.Column(db.String(24), nullable=False)
    file_path = db.Column(db.String(260), nullable=True)
    original_filename = db.Column(db.String(260), nullable=True)
    mime_type = db.Column(db.String(120), nullable=True)
    body = db.Column(db.Text, nullable=True)
    source_url = db.Column(db.String(500), nullable=True)
    neon_text_color = db.Column(db.String(7), nullable=True, default="#ff4fd8")
    neon_frame_color = db.Column(db.String(7), nullable=True, default="#37ff79")
    neon_background_color = db.Column(db.String(7), nullable=True, default="#1b1210")
    neon_font_family = db.Column(db.String(80), nullable=True, default="Inter")
    neon_font_size = db.Column(db.Integer, nullable=True, default=120)
    neon_frame_thickness = db.Column(db.Integer, nullable=True, default=8)
    vcard_name = db.Column(db.String(160), nullable=True)
    vcard_phone = db.Column(db.String(80), nullable=True)
    vcard_email = db.Column(db.String(254), nullable=True)
    vcard_address = db.Column(db.String(500), nullable=True)
    vcard_url = db.Column(db.String(500), nullable=True)
    vcard_top_text = db.Column(db.String(220), nullable=True)
    vcard_bottom_text = db.Column(db.String(220), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    displays = db.relationship(
        "Display",
        secondary=display_media,
        back_populates="media_assets",
        order_by="Display.name",
    )
    schedules = db.relationship(
        "Schedule",
        secondary=schedule_media,
        back_populates="media_assets",
        order_by="Schedule.name",
    )
    slider_slides = db.relationship(
        "MediaSlide",
        back_populates="media_asset",
        cascade="all, delete-orphan",
        order_by="MediaSlide.sort_order",
    )

    @property
    def has_file(self) -> bool:
        return bool(self.file_path)

    @property
    def slider_duration_seconds(self) -> int:
        total = sum(slide.duration_seconds for slide in self.slider_slides)
        return total or 30


class MediaSlide(db.Model):
    __tablename__ = "media_slides"

    id = db.Column(db.Integer, primary_key=True)
    media_asset_id = db.Column(db.Integer, db.ForeignKey("media_assets.id"), nullable=False, index=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    background_file_path = db.Column(db.String(260), nullable=True)
    background_original_filename = db.Column(db.String(260), nullable=True)
    foreground_file_path = db.Column(db.String(260), nullable=True)
    foreground_original_filename = db.Column(db.String(260), nullable=True)
    foreground_size = db.Column(db.Integer, nullable=False, default=50)
    foreground_position = db.Column(db.String(24), nullable=False, default="CENTER")
    foreground_animation = db.Column(db.String(40), nullable=False, default="NONE")
    text = db.Column(db.Text, nullable=True)
    text_position = db.Column(db.String(24), nullable=False, default="CENTER")
    text_font_family = db.Column(db.String(80), nullable=False, default="Inter")
    text_font_size = db.Column(db.Integer, nullable=False, default=72)
    text_animation = db.Column(db.String(40), nullable=False, default="NONE")
    duration_seconds = db.Column(db.Integer, nullable=False, default=10)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    media_asset = db.relationship("MediaAsset", back_populates="slider_slides")


class MediaFont(db.Model):
    __tablename__ = "media_fonts"

    id = db.Column(db.Integer, primary_key=True)
    family = db.Column(db.String(80), nullable=False, unique=True, index=True)
    display_name = db.Column(db.String(120), nullable=False)
    provider = db.Column(db.String(24), nullable=False, default="GOOGLE")
    local_css_path = db.Column(db.String(260), nullable=True)
    download_status = db.Column(db.String(24), nullable=False, default="REMOTE")
    download_error = db.Column(db.Text, nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
