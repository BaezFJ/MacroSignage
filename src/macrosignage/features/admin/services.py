from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from macrosignage.extensions import db

from .models import ContentVersion, SignageSettings


@dataclass(frozen=True)
class DashboardActivity:
    title: str
    subject: str
    description: str
    happened_at: datetime
    endpoint: str
    route_values: dict[str, int]
    badge_class: str


def get_signage_settings() -> SignageSettings:
    settings = db.session.get(SignageSettings, 1)
    if settings is None:
        settings = SignageSettings(id=1)
        db.session.add(settings)
        db.session.commit()
    return settings


def apply_logo_settings(settings: SignageSettings, form_data: dict[str, object]) -> None:
    from ..media.services import delete_upload, save_upload

    settings.logo_enabled = bool(form_data["logo_enabled"])
    settings.logo_position = str(form_data["logo_position"])

    if form_data["remove_logo"]:
        delete_upload(settings.logo_file_path)
        settings.logo_file_path = None
        settings.logo_original_filename = None
        settings.logo_mime_type = None

    logo_upload = form_data.get("logo_upload")
    if logo_upload and logo_upload.filename:
        delete_upload(settings.logo_file_path)
        settings.logo_file_path, settings.logo_original_filename, settings.logo_mime_type = save_upload(logo_upload)


def get_content_version() -> ContentVersion:
    content_version = db.session.get(ContentVersion, 1)
    if content_version is None:
        content_version = ContentVersion(id=1, version=1)
        db.session.add(content_version)
        db.session.commit()
    return content_version


def touch_content_version() -> ContentVersion:
    content_version = get_content_version()
    content_version.version += 1
    db.session.commit()
    return content_version


def normalized_datetime(value: datetime | None) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def is_meaningful_update(created_at: datetime | None, updated_at: datetime | None) -> bool:
    created = normalized_datetime(created_at)
    updated = normalized_datetime(updated_at)
    return (updated - created).total_seconds() > 1


def change_activity(
    *,
    noun: str,
    subject: str,
    created_at: datetime,
    updated_at: datetime,
    endpoint: str,
    route_values: dict[str, int],
    badge_class: str,
) -> DashboardActivity:
    updated = is_meaningful_update(created_at, updated_at)
    happened_at = updated_at if updated else created_at
    action = "updated" if updated else "created"
    return DashboardActivity(
        title=f"{noun} {action}",
        subject=subject,
        description=f"{noun} was {action}.",
        happened_at=happened_at,
        endpoint=endpoint,
        route_values=route_values,
        badge_class=badge_class,
    )


def recent_dashboard_activities(limit: int = 8) -> list[DashboardActivity]:
    from ..displays.models import Display
    from ..media.models import MediaAsset
    from ..schedules.models import Schedule

    activities: list[DashboardActivity] = []

    displays = db.session.scalars(
        db.select(Display).order_by(Display.updated_at.desc(), Display.id.desc()).limit(limit)
    ).all()
    for display in displays:
        activities.append(
            change_activity(
                noun="Display",
                subject=display.name,
                created_at=display.created_at,
                updated_at=display.updated_at,
                endpoint="admin_displays.get_display_view",
                route_values={"display_id": display.id},
                badge_class="text-bg-primary",
            )
        )

    checked_in_displays = db.session.scalars(
        db.select(Display)
        .where(Display.player_token_last_used_at.is_not(None))
        .order_by(Display.player_token_last_used_at.desc(), Display.id.desc())
        .limit(limit)
    ).all()
    for display in checked_in_displays:
        activities.append(
            DashboardActivity(
                title="Player check-in",
                subject=display.name,
                description="Connected for playback.",
                happened_at=display.player_token_last_used_at,
                endpoint="admin_displays.get_display_view",
                route_values={"display_id": display.id},
                badge_class="text-bg-success",
            )
        )

    media_items = db.session.scalars(
        db.select(MediaAsset).order_by(MediaAsset.updated_at.desc(), MediaAsset.id.desc()).limit(limit)
    ).all()
    for media in media_items:
        activities.append(
            change_activity(
                noun="Media",
                subject=media.title,
                created_at=media.created_at,
                updated_at=media.updated_at,
                endpoint="admin_media.get_media_view",
                route_values={"media_id": media.id},
                badge_class="text-bg-info",
            )
        )

    schedules = db.session.scalars(
        db.select(Schedule).order_by(Schedule.updated_at.desc(), Schedule.id.desc()).limit(limit)
    ).all()
    for schedule in schedules:
        activities.append(
            change_activity(
                noun="Schedule",
                subject=schedule.name,
                created_at=schedule.created_at,
                updated_at=schedule.updated_at,
                endpoint="admin_schedules.get_schedule_view",
                route_values={"schedule_id": schedule.id},
                badge_class="text-bg-warning",
            )
        )

    return sorted(activities, key=lambda activity: normalized_datetime(activity.happened_at), reverse=True)[:limit]
