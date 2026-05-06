from __future__ import annotations

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import current_app, has_app_context


def configured_timezone():
    timezone_name = ""
    if has_app_context():
        timezone_name = current_app.config.get("MACROSIGNAGE_TIMEZONE", "")
    timezone_name = timezone_name or os.environ.get("MACROSIGNAGE_TIMEZONE", "")
    if timezone_name:
        try:
            return ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            return timezone.utc

    return datetime.now().astimezone().tzinfo or timezone.utc


def datetime_as_utc(value: datetime | None, naive_timezone=timezone.utc) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        value = value.replace(tzinfo=naive_timezone)
    return value.astimezone(timezone.utc)


def local_datetime_to_stored_utc(value: datetime | None) -> datetime | None:
    utc_value = datetime_as_utc(value, configured_timezone())
    if utc_value is None:
        return None
    return utc_value.replace(tzinfo=None)


def stored_datetime_as_utc(value: datetime | None) -> datetime | None:
    return datetime_as_utc(value, timezone.utc)


def stored_datetime_to_local(value: datetime | None) -> datetime | None:
    utc_value = stored_datetime_as_utc(value)
    if utc_value is None:
        return None
    return utc_value.astimezone(configured_timezone())
