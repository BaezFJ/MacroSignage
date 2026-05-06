from flask import Blueprint, flash, redirect, render_template, request, url_for

from macrosignage.extensions import db

from ..displays.services import list_all_displays, selected_displays
from ..media.services import list_all_media, selected_media
from .forms import SCHEDULE_STATUSES, WEEKDAYS, format_datetime_display, format_datetime_local, schedule_form_data
from .models import Schedule
from .services import apply_schedule_data, get_schedule, list_schedules as query_schedules

schedules_bp = Blueprint("admin_schedules", __name__, url_prefix="/admin/schedules")


@schedules_bp.get("/")
def list_schedules():
    search_query = request.args.get("q", "").strip()
    selected_status = request.args.get("status", "").strip()
    status_filter = selected_status if selected_status in SCHEDULE_STATUSES else ""

    return render_template(
        "admin/schedules/list.html",
        title="Schedules",
        schedules=query_schedules(search_query, status_filter),
        schedule_statuses=SCHEDULE_STATUSES,
        format_datetime_display=format_datetime_display,
        search_query=search_query,
        selected_status=selected_status,
    )


@schedules_bp.route("/new", methods=["GET", "POST"])
def create_schedule():
    schedule = Schedule(status="DRAFT", default_duration_seconds=30)
    errors: dict[str, str] = {}
    displays = list_all_displays()
    media_items = list_all_media()

    if request.method == "POST":
        form_data, errors = schedule_form_data(request.form)
        apply_schedule_data(schedule, form_data, selected_displays(request.form), selected_media(request.form))

        if not errors:
            db.session.add(schedule)
            db.session.commit()
            flash(f"{schedule.name} was created.", "success")
            return redirect(url_for("admin_schedules.get_schedule_view", schedule_id=schedule.id))

    return render_template(
        "admin/schedules/form.html",
        title="New Schedule",
        schedule=schedule,
        errors=errors,
        schedule_statuses=SCHEDULE_STATUSES,
        weekdays=WEEKDAYS,
        displays=displays,
        media_items=media_items,
        format_datetime_local=format_datetime_local,
        form_action=url_for("admin_schedules.create_schedule"),
        submit_label="Create schedule",
    ), (422 if errors else 200)


@schedules_bp.get("/<int:schedule_id>")
def get_schedule_view(schedule_id: int):
    schedule = get_schedule(schedule_id)
    return render_template(
        "admin/schedules/detail.html",
        title=schedule.name,
        schedule=schedule,
        schedule_statuses=SCHEDULE_STATUSES,
        weekdays=WEEKDAYS,
        format_datetime_display=format_datetime_display,
    )


@schedules_bp.route("/<int:schedule_id>/edit", methods=["GET", "POST"])
def edit_schedule(schedule_id: int):
    schedule = get_schedule(schedule_id)
    errors: dict[str, str] = {}
    displays = list_all_displays()
    media_items = list_all_media()

    if request.method == "POST":
        form_data, errors = schedule_form_data(request.form)
        apply_schedule_data(schedule, form_data, selected_displays(request.form), selected_media(request.form))

        if not errors:
            db.session.commit()
            flash(f"{schedule.name} was updated.", "success")
            return redirect(url_for("admin_schedules.get_schedule_view", schedule_id=schedule.id))

    return render_template(
        "admin/schedules/form.html",
        title=f"Edit {schedule.name}",
        schedule=schedule,
        errors=errors,
        schedule_statuses=SCHEDULE_STATUSES,
        weekdays=WEEKDAYS,
        displays=displays,
        media_items=media_items,
        format_datetime_local=format_datetime_local,
        form_action=url_for("admin_schedules.edit_schedule", schedule_id=schedule.id),
        submit_label="Save changes",
    ), (422 if errors else 200)


@schedules_bp.post("/<int:schedule_id>/delete")
def delete_schedule(schedule_id: int):
    schedule = get_schedule(schedule_id)
    flash(f"{schedule.name} was deleted.", "success")
    db.session.delete(schedule)
    db.session.commit()
    return redirect(url_for("admin_schedules.list_schedules"))
