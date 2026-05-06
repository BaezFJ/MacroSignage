from __future__ import annotations

from datetime import datetime, timezone

from macrosignage.extensions import db

from ..associations import schedule_displays, schedule_media


class Schedule(db.Model):
    __tablename__ = "schedules"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    status = db.Column(db.String(24), nullable=False, default="DRAFT")
    starts_at = db.Column(db.DateTime(timezone=True), nullable=True)
    ends_at = db.Column(db.DateTime(timezone=True), nullable=True)
    times_are_utc = db.Column(db.Boolean, nullable=False, default=True, server_default="1")
    weekdays = db.Column(db.String(32), nullable=True)
    default_duration_seconds = db.Column(db.Integer, nullable=False, default=30)
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
        secondary=schedule_displays,
        back_populates="schedules",
        order_by="Display.name",
    )
    media_assets = db.relationship(
        "MediaAsset",
        secondary=schedule_media,
        back_populates="schedules",
        order_by="MediaAsset.title",
    )

    @property
    def weekday_values(self) -> list[str]:
        if not self.weekdays:
            return []
        return [value for value in self.weekdays.split(",") if value]
