import hashlib
import hmac
import secrets
from datetime import datetime, timezone

from sqlalchemy import func, or_

from macrosignage.extensions import db

from .models import Display


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
    return db.session.scalars(db.select(Display).order_by(Display.name.asc())).all()


def get_display(display_id: int) -> Display:
    return db.get_or_404(Display, display_id)


def get_display_for_player(display_id: int) -> Display:
    return get_display(display_id)


def generate_player_token() -> str:
    return secrets.token_urlsafe(32)


def hash_player_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


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

    return db.session.scalars(db.select(Display).where(Display.id.in_(display_ids))).all()


def apply_display_data(display: Display, form_data: dict[str, object]) -> None:
    for key, value in form_data.items():
        setattr(display, key, value)


def schedule_is_playable(schedule, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    local_weekday = now.strftime("%a").upper()
    weekday_values = schedule.weekday_values

    starts_at = schedule.starts_at
    if starts_at and starts_at.tzinfo is None:
        starts_at = starts_at.replace(tzinfo=timezone.utc)

    ends_at = schedule.ends_at
    if ends_at and ends_at.tzinfo is None:
        ends_at = ends_at.replace(tzinfo=timezone.utc)

    return (
        schedule.status == "ACTIVE"
        and (starts_at is None or starts_at <= now)
        and (ends_at is None or ends_at >= now)
        and (not weekday_values or local_weekday in weekday_values)
    )


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

    for media in display.media_assets:
        if media.id not in seen_media_ids:
            playlist.append(media)
            seen_media_ids.add(media.id)

    return playlist, default_duration
