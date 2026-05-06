from __future__ import annotations

from datetime import datetime, timezone

from flask import url_for

from ..admin.models import SignageSettings
from ..auth.models import User
from ..displays.models import Display
from ..media.models import MediaAsset, MediaFont, MediaSlide
from ..schedules.models import Schedule


def iso_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def serialize_user(user: User) -> dict[str, object]:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "active": user.active,
        "createdAt": iso_datetime(user.created_at),
        "updatedAt": iso_datetime(user.updated_at),
    }


def serialize_display(display: Display) -> dict[str, object]:
    return {
        "id": display.id,
        "name": display.name,
        "location": display.location,
        "status": display.status,
        "orientation": display.orientation,
        "resolutionWidth": display.resolution_width,
        "resolutionHeight": display.resolution_height,
        "notes": display.notes,
        "mediaIds": [media.id for media in display.media_assets],
        "scheduleIds": [schedule.id for schedule in display.schedules],
        "createdAt": iso_datetime(display.created_at),
        "updatedAt": iso_datetime(display.updated_at),
    }


def serialize_slide(slide: MediaSlide) -> dict[str, object]:
    return {
        "id": slide.id,
        "sortOrder": slide.sort_order,
        "backgroundUrl": media_file_url(slide.background_file_path),
        "foregroundUrl": media_file_url(slide.foreground_file_path),
        "foregroundSize": slide.foreground_size,
        "foregroundPosition": slide.foreground_position,
        "foregroundAnimation": slide.foreground_animation,
        "text": slide.text,
        "textPosition": slide.text_position,
        "textFontFamily": slide.text_font_family,
        "textFontSize": slide.text_font_size,
        "textAnimation": slide.text_animation,
        "durationSeconds": slide.duration_seconds,
    }


def media_file_url(file_path: str | None) -> str | None:
    if not file_path:
        return None
    return url_for("display_player.player_media_file", filename=file_path, _external=False)


def serialize_media(media: MediaAsset) -> dict[str, object]:
    return {
        "id": media.id,
        "title": media.title,
        "mediaType": media.media_type,
        "fileUrl": media_file_url(media.file_path),
        "originalFilename": media.original_filename,
        "mimeType": media.mime_type,
        "body": media.body,
        "sourceUrl": media.source_url,
        "notes": media.notes,
        "displayIds": [display.id for display in media.displays],
        "scheduleIds": [schedule.id for schedule in media.schedules],
        "sliderSlides": [serialize_slide(slide) for slide in media.slider_slides],
        "createdAt": iso_datetime(media.created_at),
        "updatedAt": iso_datetime(media.updated_at),
    }


def serialize_schedule(schedule: Schedule) -> dict[str, object]:
    return {
        "id": schedule.id,
        "name": schedule.name,
        "status": schedule.status,
        "startsAt": iso_datetime(schedule.starts_at),
        "endsAt": iso_datetime(schedule.ends_at),
        "weekdays": schedule.weekday_values,
        "defaultDurationSeconds": schedule.default_duration_seconds,
        "notes": schedule.notes,
        "displayIds": [display.id for display in schedule.displays],
        "mediaIds": [media.id for media in schedule.media_assets],
        "createdAt": iso_datetime(schedule.created_at),
        "updatedAt": iso_datetime(schedule.updated_at),
    }


def serialize_font(font: MediaFont) -> dict[str, object]:
    return {
        "id": font.id,
        "family": font.family,
        "displayName": font.display_name,
        "provider": font.provider,
        "active": font.active,
        "createdAt": iso_datetime(font.created_at),
        "updatedAt": iso_datetime(font.updated_at),
    }


def serialize_settings(settings: SignageSettings) -> dict[str, object]:
    return {
        "logoEnabled": settings.logo_enabled,
        "logoPosition": settings.logo_position,
        "logoUrl": media_file_url(settings.logo_file_path),
        "logoOriginalFilename": settings.logo_original_filename,
    }
