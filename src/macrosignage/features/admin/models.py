from datetime import datetime, timezone

from macrosignage.extensions import db


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


class ContentVersion(db.Model):
    __tablename__ = "content_versions"

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


__all__ = ["SignageSettings", "ContentVersion"]
