import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from io import BytesIO

import qrcode
import qrcode.image.svg
from sqlalchemy import func, or_

from macrosignage.extensions import db
from macrosignage.time_utils import configured_timezone, datetime_as_utc, stored_datetime_as_utc

from .models import Display, DisplayRegistration


DISPLAY_REGISTRATION_TTL = timedelta(minutes=20)


def count_displays() -> int:
    return db.session.scalar(db.select(func.count(Display.id))) or 0


def count_online_displays() -> int:
    return db.session.scalar(db.select(func.count(Display.id)).where(Display.status == "ONLINE")) or 0


def list_displays(search_query: str = "", selected_status: str = "") -> list[Display]:
    query = db.select(Display).order_by(Display.name.asc(), Display.id.asc())
    if search_query:
        like_query = f"%{search_query}%"
        query = query.where(or_(Display.name.ilike(like_query), Display.location.ilike(like_query)))
    if selected_status:
        query = query.where(Display.status == selected_status)

    return db.session.scalars(query).all()


def list_all_displays() -> list[Display]:
    with db.session.no_autoflush:
        return db.session.scalars(db.select(Display).order_by(Display.name.asc())).all()


def get_display(display_id: int) -> Display:
    return db.get_or_404(Display, display_id)


def get_display_for_player(display_id: int) -> Display:
    return get_display(display_id)


def generate_player_token() -> str:
    return secrets.token_urlsafe(32)


def hash_player_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_registration_token() -> str:
    return secrets.token_urlsafe(24)


def rotate_player_token(display: Display) -> str:
    token = generate_player_token()
    now = datetime.now(timezone.utc)
    display.player_token_hash = hash_player_token(token)
    display.player_token_enabled = True
    display.player_access_key = secrets.token_urlsafe(24)
    display.player_token_created_at = now
    display.player_token_last_used_at = None
    return token


def enable_player_token(display: Display) -> bool:
    if not display.player_token_hash:
        return False
    display.player_token_enabled = True
    if not display.player_access_key:
        display.player_access_key = secrets.token_urlsafe(24)
    return True


def disable_player_token(display: Display) -> None:
    display.player_token_enabled = False
    display.player_access_key = secrets.token_urlsafe(24)


def player_token_is_valid(display: Display, token: str) -> bool:
    if not display.player_token_enabled or not display.player_token_hash or not token:
        return False
    return hmac.compare_digest(display.player_token_hash, hash_player_token(token))


def display_for_player_token(token: str) -> Display | None:
    if not token:
        return None

    hashed_token = hash_player_token(token)
    display = db.session.scalar(
        db.select(Display).where(
            Display.player_token_hash == hashed_token,
            Display.player_token_enabled.is_(True),
        )
    )
    if display is None or not hmac.compare_digest(display.player_token_hash or "", hashed_token):
        return None
    return display


def create_display_registration(now: datetime | None = None) -> tuple[DisplayRegistration, str, str]:
    claim_code = generate_registration_token()
    registration_key = generate_registration_token()
    registration = DisplayRegistration(
        claim_code_hash=hash_player_token(claim_code),
        registration_key_hash=hash_player_token(registration_key),
        expires_at=(now or datetime.now(timezone.utc)) + DISPLAY_REGISTRATION_TTL,
    )
    db.session.add(registration)
    return registration, claim_code, registration_key


def registration_is_expired(registration: DisplayRegistration, now: datetime | None = None) -> bool:
    return stored_datetime_as_utc(registration.expires_at) <= (now or datetime.now(timezone.utc))


def display_registration_for_claim_code(claim_code: str) -> DisplayRegistration | None:
    if not claim_code:
        return None
    hashed_code = hash_player_token(claim_code)
    registration = db.session.scalar(
        db.select(DisplayRegistration).where(DisplayRegistration.claim_code_hash == hashed_code)
    )
    if registration is None or not hmac.compare_digest(registration.claim_code_hash, hashed_code):
        return None
    return registration


def display_registration_for_key(registration_key: str) -> DisplayRegistration | None:
    if not registration_key:
        return None
    hashed_key = hash_player_token(registration_key)
    registration = db.session.scalar(
        db.select(DisplayRegistration).where(DisplayRegistration.registration_key_hash == hashed_key)
    )
    if registration is None or not hmac.compare_digest(registration.registration_key_hash, hashed_key):
        return None
    return registration


def claim_display_registration(registration: DisplayRegistration, display: Display) -> None:
    registration.display = display
    registration.claimed_at = datetime.now(timezone.utc)


def qr_code_svg(value: str) -> str:
    image = qrcode.make(
        value,
        image_factory=qrcode.image.svg.SvgPathImage,
        border=2,
        box_size=10,
    )
    output = BytesIO()
    image.save(output)
    svg = output.getvalue().decode("utf-8")
    if svg.startswith("<?xml"):
        svg = svg.split("?>", 1)[1].lstrip()
    return svg


def remember_player_token_use(display: Display) -> None:
    if not display.player_access_key:
        display.player_access_key = secrets.token_urlsafe(24)
    display.player_token_last_used_at = datetime.now(timezone.utc)


def display_has_player_access(display: Display, access_key: str | None) -> bool:
    return (
        display.player_token_enabled
        and bool(display.player_token_hash)
        and bool(display.player_access_key)
        and hmac.compare_digest(display.player_access_key, access_key or "")
    )


def selected_displays(form) -> list[Display]:
    display_ids = []
    for raw_display_id in form.getlist("display_ids"):
        try:
            display_ids.append(int(raw_display_id))
        except ValueError:
            continue

    if not display_ids:
        return []

    with db.session.no_autoflush:
        return db.session.scalars(db.select(Display).where(Display.id.in_(display_ids))).all()


def apply_display_data(display: Display, form_data: dict[str, object]) -> None:
    for key, value in form_data.items():
        setattr(display, key, value)


def schedule_is_playable(schedule, now: datetime | None = None) -> bool:
    local_timezone = configured_timezone()
    now_utc = datetime_as_utc(now or datetime.now(timezone.utc), local_timezone)
    local_weekday = now_utc.astimezone(local_timezone).strftime("%a").upper()
    weekday_values = schedule.weekday_values

    starts_at = schedule_boundary_as_utc(schedule, schedule.starts_at, local_timezone)
    ends_at = schedule_boundary_as_utc(schedule, schedule.ends_at, local_timezone)

    return (
        schedule.status == "ACTIVE"
        and (starts_at is None or starts_at <= now_utc)
        and (ends_at is None or ends_at > now_utc)
        and (not weekday_values or local_weekday in weekday_values)
    )


def schedule_boundary_as_utc(schedule, value: datetime | None, local_timezone) -> datetime | None:
    if value is None:
        return None
    if not getattr(schedule, "times_are_utc", True) and (value.tzinfo is None or value.utcoffset() is None):
        return datetime_as_utc(value, local_timezone)
    return stored_datetime_as_utc(value)


def schedule_next_refresh_at(display: Display, now: datetime | None = None) -> datetime | None:
    local_timezone = configured_timezone()
    now_utc = datetime_as_utc(now or datetime.now(timezone.utc), local_timezone)
    candidates = []

    for schedule in display.schedules:
        if schedule.status != "ACTIVE":
            continue

        starts_at = schedule_boundary_as_utc(schedule, schedule.starts_at, local_timezone)
        ends_at = schedule_boundary_as_utc(schedule, schedule.ends_at, local_timezone)
        if starts_at and starts_at > now_utc:
            candidates.append(starts_at)
        if ends_at and ends_at > now_utc:
            candidates.append(ends_at)

    return min(candidates) if candidates else None


def display_playlist(display: Display, now: datetime | None = None) -> tuple[list, int]:
    playable_schedules = [
        schedule
        for schedule in display.schedules
        if schedule_is_playable(schedule, now)
    ]
    playlist = []
    seen_media_ids = set()
    default_duration = 30

    for schedule in sorted(playable_schedules, key=lambda item: (item.starts_at is None, item.starts_at or datetime.min)):
        default_duration = schedule.default_duration_seconds or default_duration
        for media in schedule.media_assets:
            if media.id not in seen_media_ids:
                playlist.append(media)
                seen_media_ids.add(media.id)

    return playlist, default_duration
