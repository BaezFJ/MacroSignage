from __future__ import annotations

from datetime import datetime, timezone

from macrosignage.extensions import db

display_media = db.Table(
    "display_media",
    db.Column("display_id", db.Integer, db.ForeignKey("displays.id"), primary_key=True),
    db.Column("media_id", db.Integer, db.ForeignKey("media_assets.id"), primary_key=True),
    db.Column("assigned_at", db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
)

schedule_displays = db.Table(
    "schedule_displays",
    db.Column("schedule_id", db.Integer, db.ForeignKey("schedules.id"), primary_key=True),
    db.Column("display_id", db.Integer, db.ForeignKey("displays.id"), primary_key=True),
    db.Column("assigned_at", db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
)

schedule_media = db.Table(
    "schedule_media",
    db.Column("schedule_id", db.Integer, db.ForeignKey("schedules.id"), primary_key=True),
    db.Column("media_id", db.Integer, db.ForeignKey("media_assets.id"), primary_key=True),
    db.Column("assigned_at", db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
)
