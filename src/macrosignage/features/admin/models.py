from datetime import datetime, timezone

from macrosignage.extensions import db

from ..displays.models import Display
from ..media.models import MediaAsset, MediaFont, MediaSlide
from ..schedules.models import Schedule


class SignageSettings(db.Model):
    __tablename__ = "signage_settings"

    id = db.Column(db.Integer, primary_key=True)
    logo_enabled = db.Column(db.Boolean, nullable=False, default=False)
    logo_position = db.Column(db.String(24), nullable=False, default="TOP_RIGHT")
    logo_file_path = db.Column(db.String(260), nullable=True)
    logo_original_filename = db.Column(db.String(260), nullable=True)
    logo_mime_type = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def has_logo(self) -> bool:
        return bool(self.logo_file_path)


__all__ = ["Display", "MediaAsset", "MediaFont", "MediaSlide", "Schedule", "SignageSettings"]
