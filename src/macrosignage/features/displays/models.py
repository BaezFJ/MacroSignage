from __future__ import annotations

from datetime import datetime, timezone

from macrosignage.extensions import db

from ..associations import display_media, schedule_displays


class Display(db.Model):
    __tablename__ = "displays"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(160), nullable=True)
    status = db.Column(db.String(24), nullable=False, default="OFFLINE")
    orientation = db.Column(db.String(24), nullable=False, default="LANDSCAPE")
    resolution_width = db.Column(db.Integer, nullable=False, default=1920)
    resolution_height = db.Column(db.Integer, nullable=False, default=1080)
    notes = db.Column(db.Text, nullable=True)
    player_token_hash = db.Column(db.String(64), nullable=True)
    player_token_enabled = db.Column(db.Boolean, nullable=False, default=False)
    player_access_key = db.Column(db.String(64), nullable=True)
    player_token_created_at = db.Column(db.DateTime(timezone=True), nullable=True)
    player_token_last_used_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    media_assets = db.relationship(
        "MediaAsset",
        secondary=display_media,
        back_populates="displays",
        order_by="MediaAsset.title",
    )
    schedules = db.relationship(
        "Schedule",
        secondary=schedule_displays,
        back_populates="displays",
        order_by="Schedule.name",
    )

    @property
    def resolution_label(self) -> str:
        return f"{self.resolution_width} x {self.resolution_height}"


class DisplayRegistration(db.Model):
    __tablename__ = "display_registrations"

    id = db.Column(db.Integer, primary_key=True)
    claim_code_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    registration_key_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    display_id = db.Column(db.Integer, db.ForeignKey("displays.id"), nullable=True, index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    claimed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    display = db.relationship("Display")

    @property
    def is_claimed(self) -> bool:
        return self.display_id is not None and self.claimed_at is not None
