from __future__ import annotations

from datetime import datetime

from macrosignage.time_utils import local_datetime_to_stored_utc, stored_datetime_to_local

from ..displays.forms import positive_int

SCHEDULE_STATUSES = {
    "DRAFT": "Draft",
    "ACTIVE": "Active",
    "PAUSED": "Paused",
}

WEEKDAYS = {
    "MON": "Mon",
    "TUE": "Tue",
    "WED": "Wed",
    "THU": "Thu",
    "FRI": "Fri",
    "SAT": "Sat",
    "SUN": "Sun",
}


def parse_datetime(value: str, field_label: str) -> tuple[datetime | None, str | None]:
    if not value:
        return None, None

    try:
        return local_datetime_to_stored_utc(datetime.fromisoformat(value)), None
    except ValueError:
        return None, f"{field_label} must be a valid date and time."


def stored_or_local_datetime_to_local(value: datetime | None, times_are_utc: bool = True) -> datetime | None:
    if value is None:
        return None
    if not times_are_utc and (value.tzinfo is None or value.utcoffset() is None):
        return value
    return stored_datetime_to_local(value)


def format_datetime_local(value: datetime | None, times_are_utc: bool = True) -> str:
    if value is None:
        return ""
    local_value = stored_or_local_datetime_to_local(value, times_are_utc)
    return local_value.strftime("%Y-%m-%dT%H:%M") if local_value else ""


def format_datetime_display(value: datetime | None, fallback: str, times_are_utc: bool = True) -> str:
    if value is None:
        return fallback
    local_value = stored_or_local_datetime_to_local(value, times_are_utc)
    return local_value.strftime("%b %d, %Y %H:%M") if local_value else fallback


def schedule_form_data(form) -> tuple[dict[str, object], dict[str, str]]:
    errors: dict[str, str] = {}
    name = form.get("name", "").strip()
    status = form.get("status", "DRAFT").strip()
    notes = form.get("notes", "").strip()
    starts_at, starts_error = parse_datetime(form.get("starts_at", "").strip(), "Start time")
    ends_at, ends_error = parse_datetime(form.get("ends_at", "").strip(), "End time")
    default_duration_seconds, duration_error = positive_int(
        form.get("default_duration_seconds", ""), "Default duration"
    )
    selected_weekdays = [value for value in form.getlist("weekdays") if value in WEEKDAYS]

    if not name:
        errors["name"] = "Schedule name is required."
    if status not in SCHEDULE_STATUSES:
        errors["status"] = "Choose a valid schedule status."
    if starts_error:
        errors["starts_at"] = starts_error
    if ends_error:
        errors["ends_at"] = ends_error
    if starts_at and ends_at and ends_at <= starts_at:
        errors["ends_at"] = "End time must be after the start time."
    if duration_error:
        errors["default_duration_seconds"] = duration_error
    elif default_duration_seconds and default_duration_seconds > 86400:
        errors["default_duration_seconds"] = "Default duration cannot exceed 24 hours."

    return (
        {
            "name": name,
            "status": status,
            "starts_at": starts_at,
            "ends_at": ends_at,
            "times_are_utc": True,
            "weekdays": ",".join(selected_weekdays) or None,
            "default_duration_seconds": default_duration_seconds,
            "notes": notes or None,
        },
        errors,
    )
