from sqlalchemy import func, or_

from macrosignage.extensions import db

from .models import Schedule


def count_active_schedules() -> int:
    return db.session.scalar(db.select(func.count(Schedule.id)).where(Schedule.status == "ACTIVE")) or 0


def list_schedules(search_query: str = "", selected_status: str = "") -> list[Schedule]:
    query = db.select(Schedule).order_by(Schedule.name.asc(), Schedule.id.asc())
    if search_query:
        like_query = f"%{search_query}%"
        query = query.where(or_(Schedule.name.ilike(like_query), Schedule.notes.ilike(like_query)))
    if selected_status:
        query = query.where(Schedule.status == selected_status)

    return db.session.scalars(query).all()


def get_schedule(schedule_id: int) -> Schedule:
    return db.get_or_404(Schedule, schedule_id)


def apply_schedule_data(schedule: Schedule, form_data: dict[str, object], displays, media_assets) -> None:
    for key, value in form_data.items():
        setattr(schedule, key, value)
    schedule.displays = displays
    schedule.media_assets = media_assets
