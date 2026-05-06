from __future__ import annotations

from datetime import datetime
from functools import wraps

from flask import Blueprint, g, jsonify, request

from macrosignage.diagnostics import health_payload
from macrosignage.extensions import csrf, db
from macrosignage.time_utils import local_datetime_to_stored_utc

from ..admin.services import get_content_version, get_signage_settings
from ..auth.forms import USER_ROLES
from ..auth.models import User
from ..auth.permissions import has_role
from ..auth.services import authenticate_api_token, hash_password, user_data_conflict_errors
from ..displays.forms import DISPLAY_ORIENTATIONS, DISPLAY_STATUSES
from ..displays.models import Display
from ..displays.services import (
    display_has_player_access,
    display_playlist,
    get_display,
    player_token_is_valid,
    remember_player_token_use,
)
from ..media.forms import MEDIA_TYPES
from ..media.models import MediaAsset, MediaFont
from ..schedules.forms import SCHEDULE_STATUSES, WEEKDAYS
from ..schedules.models import Schedule
from .serializers import (
    serialize_display,
    serialize_font,
    serialize_media,
    serialize_schedule,
    serialize_settings,
    serialize_user,
)

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")
csrf.exempt(api_bp)


def api_error(status_code: int, code: str, message: str, details=None):
    body: dict[str, object] = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return jsonify(body), status_code


@api_bp.errorhandler(404)
def not_found(_error):
    return api_error(404, "NOT_FOUND", "Resource not found.")


def bearer_token() -> str:
    value = request.headers.get("Authorization", "")
    if not value.startswith("Bearer "):
        return ""
    return value.removeprefix("Bearer ").strip()


@api_bp.before_request
def authenticate_api_request():
    if request.endpoint == "api.health":
        return None
    if request.endpoint in {"api.display_status", "api.display_playlist_view"} and display_access_is_valid():
        g.api_user = None
        return None

    user = authenticate_api_token(bearer_token())
    if user is None:
        return api_error(401, "UNAUTHENTICATED", "Valid bearer token required.")
    g.api_user = user
    return None


def require_role(minimum_role: str):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not has_role(g.api_user, minimum_role):
                return api_error(403, "FORBIDDEN", "You do not have permission to perform this action.")
            return view(*args, **kwargs)

        return wrapped

    return decorator


def request_json() -> tuple[dict[str, object], object | None]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return {}, api_error(400, "INVALID_JSON", "Request body must be a JSON object.")
    return data, None


def parse_datetime(value) -> datetime | None:
    if value in {None, ""}:
        return None
    if not isinstance(value, str):
        raise ValueError
    return local_datetime_to_stored_utc(datetime.fromisoformat(value))


def related_displays(ids) -> list[Display]:
    if ids is None or ids == "":
        return []
    if not isinstance(ids, list):
        raise ValueError
    return db.session.scalars(db.select(Display).where(Display.id.in_([int(item) for item in ids]))).all()


def related_media(ids) -> list[MediaAsset]:
    if ids is None or ids == "":
        return []
    if not isinstance(ids, list):
        raise ValueError
    return db.session.scalars(db.select(MediaAsset).where(MediaAsset.id.in_([int(item) for item in ids]))).all()


def apply_display_json(display: Display, data: dict[str, object], partial: bool = False) -> dict[str, str]:
    errors = {}
    if not partial or "name" in data:
        display.name = str(data.get("name", "")).strip()
        if not display.name:
            errors["name"] = "Display name is required."
    if "location" in data or not partial:
        display.location = str(data.get("location") or "").strip() or None
    if "status" in data or not partial:
        display.status = str(data.get("status", "OFFLINE")).strip()
        if display.status not in DISPLAY_STATUSES:
            errors["status"] = "Choose a valid display status."
    if "orientation" in data or not partial:
        display.orientation = str(data.get("orientation", "LANDSCAPE")).strip()
        if display.orientation not in DISPLAY_ORIENTATIONS:
            errors["orientation"] = "Choose a valid orientation."
    for api_key, attr in (("resolutionWidth", "resolution_width"), ("resolutionHeight", "resolution_height")):
        if api_key in data or not partial:
            try:
                value = int(data.get(api_key, 1920 if api_key == "resolutionWidth" else 1080))
            except (TypeError, ValueError):
                errors[api_key] = "Value must be a whole number."
                continue
            if value <= 0:
                errors[api_key] = "Value must be greater than zero."
            setattr(display, attr, value)
    if "notes" in data or not partial:
        display.notes = str(data.get("notes") or "").strip() or None
    return errors


def apply_media_json(media: MediaAsset, data: dict[str, object], partial: bool = False) -> dict[str, str]:
    errors = {}
    if "title" in data or not partial:
        media.title = str(data.get("title", "")).strip()
        if not media.title:
            errors["title"] = "Media title is required."
    if "mediaType" in data or not partial:
        media.media_type = str(data.get("mediaType", "TEXT")).strip()
        if media.media_type not in MEDIA_TYPES:
            errors["mediaType"] = "Choose a valid media type."
    if "body" in data or not partial:
        media.body = str(data.get("body") or "").strip() or None
    if "sourceUrl" in data or not partial:
        media.source_url = str(data.get("sourceUrl") or "").strip() or None
    if "notes" in data or not partial:
        media.notes = str(data.get("notes") or "").strip() or None
    if "displayIds" in data:
        try:
            media.displays = related_displays(data.get("displayIds"))
        except (TypeError, ValueError):
            errors["displayIds"] = "Display ids must be an array of integers."
    if media.media_type in {"TEXT", "HTML"} and not media.body:
        errors["body"] = "Content is required for this media type."
    if media.media_type == "YOUTUBE" and not media.source_url:
        errors["sourceUrl"] = "YouTube URL is required."
    if media.media_type in {"IMAGE", "VIDEO"} and not media.file_path:
        errors["file"] = "File upload is not available through the JSON API."
    return errors


def apply_schedule_json(schedule: Schedule, data: dict[str, object], partial: bool = False) -> dict[str, str]:
    errors = {}
    if "name" in data or not partial:
        schedule.name = str(data.get("name", "")).strip()
        if not schedule.name:
            errors["name"] = "Schedule name is required."
    if "status" in data or not partial:
        schedule.status = str(data.get("status", "DRAFT")).strip()
        if schedule.status not in SCHEDULE_STATUSES:
            errors["status"] = "Choose a valid schedule status."
    try:
        if "startsAt" in data or not partial:
            schedule.starts_at = parse_datetime(data.get("startsAt"))
        if "endsAt" in data or not partial:
            schedule.ends_at = parse_datetime(data.get("endsAt"))
        if "startsAt" in data or "endsAt" in data or not partial:
            schedule.times_are_utc = True
    except ValueError:
        errors["datetime"] = "Date fields must be ISO 8601 strings."
    weekdays = data.get("weekdays")
    if "weekdays" in data:
        if not isinstance(weekdays, list) or any(value not in WEEKDAYS for value in weekdays):
            errors["weekdays"] = "Weekdays must be an array of weekday codes."
        else:
            schedule.weekdays = ",".join(weekdays) or None
    if "defaultDurationSeconds" in data or not partial:
        try:
            schedule.default_duration_seconds = int(data.get("defaultDurationSeconds", 30))
        except (TypeError, ValueError):
            errors["defaultDurationSeconds"] = "Default duration must be a whole number."
    if "notes" in data or not partial:
        schedule.notes = str(data.get("notes") or "").strip() or None
    try:
        if "displayIds" in data:
            schedule.displays = related_displays(data.get("displayIds"))
        if "mediaIds" in data:
            schedule.media_assets = related_media(data.get("mediaIds"))
    except (TypeError, ValueError):
        errors["relationships"] = "Relationship ids must be arrays of integers."
    return errors


@api_bp.get("/health")
def health():
    payload = health_payload(get_content_version().version)
    return jsonify(payload), (200 if payload["ready"] else 503)


@api_bp.get("/displays")
@require_role("VIEWER")
def list_displays():
    return jsonify({"data": [serialize_display(item) for item in Display.query.order_by(Display.name.asc()).all()]})


@api_bp.post("/displays")
@require_role("EDITOR")
def create_display():
    data, error = request_json()
    if error:
        return error
    display = Display()
    errors = apply_display_json(display, data)
    if errors:
        return api_error(422, "VALIDATION_ERROR", "Invalid display data.", errors)
    db.session.add(display)
    db.session.commit()
    return jsonify({"data": serialize_display(display)}), 201


@api_bp.get("/displays/<int:display_id>")
@require_role("VIEWER")
def get_display_view(display_id: int):
    return jsonify({"data": serialize_display(get_display(display_id))})


@api_bp.patch("/displays/<int:display_id>")
@require_role("EDITOR")
def update_display(display_id: int):
    data, error = request_json()
    if error:
        return error
    display = get_display(display_id)
    errors = apply_display_json(display, data, partial=True)
    if errors:
        return api_error(422, "VALIDATION_ERROR", "Invalid display data.", errors)
    db.session.commit()
    return jsonify({"data": serialize_display(display)})


@api_bp.delete("/displays/<int:display_id>")
@require_role("EDITOR")
def delete_display(display_id: int):
    display = get_display(display_id)
    db.session.delete(display)
    db.session.commit()
    return "", 204


@api_bp.get("/media")
@require_role("VIEWER")
def list_media():
    return jsonify({"data": [serialize_media(item) for item in MediaAsset.query.order_by(MediaAsset.title.asc()).all()]})


@api_bp.post("/media")
@require_role("EDITOR")
def create_media():
    data, error = request_json()
    if error:
        return error
    media = MediaAsset(media_type="TEXT")
    db.session.add(media)
    errors = apply_media_json(media, data)
    if errors:
        db.session.rollback()
        return api_error(422, "VALIDATION_ERROR", "Invalid media data.", errors)
    db.session.commit()
    return jsonify({"data": serialize_media(media)}), 201


@api_bp.get("/media/<int:media_id>")
@require_role("VIEWER")
def get_media_view(media_id: int):
    return jsonify({"data": serialize_media(db.get_or_404(MediaAsset, media_id))})


@api_bp.patch("/media/<int:media_id>")
@require_role("EDITOR")
def update_media(media_id: int):
    data, error = request_json()
    if error:
        return error
    media = db.get_or_404(MediaAsset, media_id)
    errors = apply_media_json(media, data, partial=True)
    if errors:
        return api_error(422, "VALIDATION_ERROR", "Invalid media data.", errors)
    db.session.commit()
    return jsonify({"data": serialize_media(media)})


@api_bp.delete("/media/<int:media_id>")
@require_role("EDITOR")
def delete_media(media_id: int):
    media = db.get_or_404(MediaAsset, media_id)
    db.session.delete(media)
    db.session.commit()
    return "", 204


@api_bp.get("/schedules")
@require_role("VIEWER")
def list_schedules():
    return jsonify({"data": [serialize_schedule(item) for item in Schedule.query.order_by(Schedule.name.asc()).all()]})


@api_bp.post("/schedules")
@require_role("EDITOR")
def create_schedule():
    data, error = request_json()
    if error:
        return error
    schedule = Schedule()
    db.session.add(schedule)
    errors = apply_schedule_json(schedule, data)
    if errors:
        db.session.rollback()
        return api_error(422, "VALIDATION_ERROR", "Invalid schedule data.", errors)
    db.session.commit()
    return jsonify({"data": serialize_schedule(schedule)}), 201


@api_bp.get("/schedules/<int:schedule_id>")
@require_role("VIEWER")
def get_schedule_view(schedule_id: int):
    return jsonify({"data": serialize_schedule(db.get_or_404(Schedule, schedule_id))})


@api_bp.patch("/schedules/<int:schedule_id>")
@require_role("EDITOR")
def update_schedule(schedule_id: int):
    data, error = request_json()
    if error:
        return error
    schedule = db.get_or_404(Schedule, schedule_id)
    errors = apply_schedule_json(schedule, data, partial=True)
    if errors:
        return api_error(422, "VALIDATION_ERROR", "Invalid schedule data.", errors)
    db.session.commit()
    return jsonify({"data": serialize_schedule(schedule)})


@api_bp.delete("/schedules/<int:schedule_id>")
@require_role("EDITOR")
def delete_schedule(schedule_id: int):
    schedule = db.get_or_404(Schedule, schedule_id)
    db.session.delete(schedule)
    db.session.commit()
    return "", 204


@api_bp.get("/users")
@require_role("ADMIN")
def list_users():
    return jsonify({"data": [serialize_user(item) for item in User.query.order_by(User.username.asc()).all()]})


@api_bp.post("/users")
@require_role("ADMIN")
def create_user():
    data, error = request_json()
    if error:
        return error
    user = User(
        username=str(data.get("username", "")).strip(),
        email=str(data.get("email", "")).strip().lower(),
        role=str(data.get("role", "VIEWER")).strip(),
        active=bool(data.get("active", True)),
    )
    errors = {}
    if not user.username:
        errors["username"] = "Username is required."
    if not user.email:
        errors["email"] = "Email is required."
    if user.role not in USER_ROLES:
        errors["role"] = "Choose a valid role."
    password = str(data.get("password", ""))
    if len(password) < 8:
        errors["password"] = "Password must be at least 8 characters."
    user_data_conflict_errors(None, user.username, user.email, errors)
    if errors:
        return api_error(422, "VALIDATION_ERROR", "Invalid user data.", errors)
    user.password_hash = hash_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"data": serialize_user(user)}), 201


@api_bp.get("/users/<int:user_id>")
@require_role("ADMIN")
def get_user_view(user_id: int):
    return jsonify({"data": serialize_user(db.get_or_404(User, user_id))})


@api_bp.get("/fonts")
@require_role("VIEWER")
def list_fonts():
    return jsonify({"data": [serialize_font(item) for item in MediaFont.query.order_by(MediaFont.display_name.asc()).all()]})


@api_bp.post("/fonts")
@require_role("ADMIN")
def create_font():
    data, error = request_json()
    if error:
        return error
    font = MediaFont(
        family=str(data.get("family", "")).strip(),
        display_name=str(data.get("displayName") or data.get("family", "")).strip(),
        provider="GOOGLE",
        active=bool(data.get("active", True)),
    )
    if not font.family:
        return api_error(422, "VALIDATION_ERROR", "Invalid font data.", {"family": "Font family is required."})
    existing = MediaFont.query.filter(db.func.lower(MediaFont.family) == font.family.lower()).first()
    if existing:
        return api_error(409, "CONFLICT", "Font family already exists.")
    db.session.add(font)
    db.session.commit()
    return jsonify({"data": serialize_font(font)}), 201


@api_bp.get("/settings")
@require_role("VIEWER")
def get_settings():
    return jsonify({"data": serialize_settings(get_signage_settings())})


def display_access_is_valid() -> bool:
    display_id = request.view_args.get("display_id") if request.view_args else None
    if display_id is None:
        return False
    display = db.session.get(Display, display_id)
    if display is None:
        return False
    access_key = request.headers.get("X-Display-Access-Key")
    display_token = request.headers.get("X-Display-Token", "")
    if display_has_player_access(display, access_key):
        return True
    if player_token_is_valid(display, display_token):
        remember_player_token_use(display)
        db.session.commit()
        return True
    return False


@api_bp.get("/player/displays/<int:display_id>/status")
def display_status(display_id: int):
    display = get_display(display_id)
    return jsonify({"data": {"display": serialize_display(display), "contentVersion": get_content_version().version}})


@api_bp.get("/player/displays/<int:display_id>/playlist")
def display_playlist_view(display_id: int):
    display = get_display(display_id)
    playlist, default_duration = display_playlist(display)
    return jsonify(
        {
            "data": {
                "display": serialize_display(display),
                "status": display.status,
                "defaultDurationSeconds": default_duration,
                "contentVersion": get_content_version().version,
                "logo": serialize_settings(get_signage_settings()),
                "media": [serialize_media(media) for media in playlist] if display.status == "ONLINE" else [],
            }
        }
    )
