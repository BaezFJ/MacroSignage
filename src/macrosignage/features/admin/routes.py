from urllib.parse import urlsplit

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from macrosignage.config import (
    DATABASE_ENV_KEY,
    DATABASE_OPTIONS,
    database_form_from_uri,
    default_database_uri,
    write_database_uri,
)
from macrosignage.extensions import db

from .forms import LOGO_POSITIONS, database_settings_form_data, logo_settings_form_data
from .services import apply_logo_settings, get_signage_settings, recent_dashboard_activities
from ..displays.forms import DISPLAY_ORIENTATIONS, DISPLAY_STATUSES
from ..displays.services import count_displays, count_online_displays
from ..media.forms import IMAGE_EXTENSIONS, MEDIA_TYPES, VIDEO_EXTENSIONS, font_form_data
from ..media.models import MediaFont
from ..media.services import (
    apply_font_data,
    count_fonts,
    count_media,
    font_conflict_errors,
    font_usage_count,
    get_font,
    list_fonts as query_fonts,
)
from ..schedules.forms import SCHEDULE_STATUSES, WEEKDAYS
from ..schedules.services import count_active_schedules

admin_bp = Blueprint("admin", __name__, template_folder="templates", url_prefix="/admin")


def format_bytes(value):
    if value is None:
        return "Not limited"

    size = float(value)
    for unit in ("bytes", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            if unit == "bytes":
                return f"{int(size)} {unit}"
            return f"{size:.0f} {unit}"
        size /= 1024

    return f"{int(value)} bytes"


def safe_database_label(uri):
    if not uri:
        return "Not configured"

    if uri.startswith("sqlite:///"):
        return f"SQLite / {uri.removeprefix('sqlite:///')}"

    parsed = urlsplit(uri)
    if parsed.scheme and parsed.hostname:
        port = f":{parsed.port}" if parsed.port else ""
        database = parsed.path.strip("/") or "default"
        return f"{parsed.scheme} / {parsed.hostname}{port}/{database}"

    return uri


def settings_context():
    max_upload_bytes = current_app.config.get("MAX_CONTENT_LENGTH")
    media_folder = current_app.config.get("MEDIA_UPLOAD_FOLDER", "Not configured")
    database_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI")
    default_uri = default_database_uri(current_app.instance_path)
    default_sqlite_path = default_uri.removeprefix("sqlite:///")
    database_label = safe_database_label(database_uri)
    logo_settings = get_signage_settings()

    return {
        "application": [
            ("Version", current_app.config.get("APP_VERSION", "Unknown")),
            ("Runtime mode", "Debug" if current_app.debug else "Production"),
            ("CSRF protection", "Enabled"),
            ("Database", database_label),
        ],
        "production_warnings": current_app.config.get("MACROSIGNAGE_CONFIG_WARNINGS", []),
        "database": {
            "uri": database_uri,
            "label": database_label,
            "default_uri": default_uri,
            "form": database_form_from_uri(database_uri, default_sqlite_path),
            "env_file": current_app.config.get("MACROSIGNAGE_ENV_FILE", ".env"),
            "env_key": DATABASE_ENV_KEY,
            "options": DATABASE_OPTIONS,
        },
        "storage": [
            ("Media upload folder", media_folder),
            ("Maximum upload size", format_bytes(max_upload_bytes)),
            ("Image extensions", ", ".join(sorted(IMAGE_EXTENSIONS))),
            ("Video extensions", ", ".join(sorted(VIDEO_EXTENSIONS))),
        ],
        "catalog": [
            ("Display statuses", ", ".join(DISPLAY_STATUSES.values())),
            ("Display orientations", ", ".join(DISPLAY_ORIENTATIONS.values())),
            ("Media types", ", ".join(MEDIA_TYPES.values())),
            ("Managed fonts", str(count_fonts())),
            ("Schedule statuses", ", ".join(SCHEDULE_STATUSES.values())),
            ("Schedule weekdays", ", ".join(WEEKDAYS.values())),
        ],
        "logo": [
            ("Status", "Visible" if logo_settings.logo_enabled else "Hidden"),
            ("Position", LOGO_POSITIONS.get(logo_settings.logo_position, logo_settings.logo_position)),
            ("File", logo_settings.logo_original_filename or "No logo uploaded"),
        ],
    }


@admin_bp.get("/")
def get_dashboard():
    return render_template(
        "admin/dashboard.html",
        title="Admin Dashboard",
        display_count=count_displays(),
        online_display_count=count_online_displays(),
        media_count=count_media(),
        active_schedule_count=count_active_schedules(),
        recent_activities=recent_dashboard_activities(),
    )


@admin_bp.get("/settings/")
def get_settings():
    return render_template(
        "admin/settings.html",
        title="Settings",
        settings=settings_context(),
        logo_positions=LOGO_POSITIONS,
        logo_settings=get_signage_settings(),
    )


@admin_bp.route("/settings/database", methods=["GET", "POST"])
def manage_database_settings():
    settings = settings_context()
    form_data = settings["database"]["form"]
    errors: dict[str, str] = {}

    if request.method == "POST":
        form_data, errors = database_settings_form_data(request.form)
        if not errors:
            write_database_uri(current_app.config["MACROSIGNAGE_ENV_FILE"], str(form_data["database_uri"]))
            flash("Database configuration saved. Restart MacroSignage for the new database to take effect.", "warning")
            return redirect(url_for("admin.get_settings"))

    return render_template(
        "admin/database.html",
        title="Database Settings",
        settings=settings,
        database_options=DATABASE_OPTIONS,
        database_errors=errors,
        database_form=form_data,
    ), (422 if errors else 200)


@admin_bp.route("/settings/logo", methods=["GET", "POST"])
def manage_logo_settings():
    logo_settings = get_signage_settings()
    errors: dict[str, str] = {}

    if request.method == "POST":
        form_data, errors = logo_settings_form_data(request.form, request.files)
        if not errors:
            apply_logo_settings(logo_settings, form_data)
            db.session.commit()
            flash("Logo settings were updated.", "success")
            return redirect(url_for("admin.get_settings"))

    return render_template(
        "admin/logo.html",
        title="Logo Settings",
        settings=settings_context(),
        logo_positions=LOGO_POSITIONS,
        logo_settings=logo_settings,
        logo_errors=errors,
    ), (422 if errors else 200)


@admin_bp.get("/settings/fonts/")
def list_fonts():
    fonts = query_fonts()
    usage_counts = {font.family: font_usage_count(font.family) for font in fonts}
    return render_template(
        "admin/fonts/list.html",
        title="Fonts",
        fonts=fonts,
        usage_counts=usage_counts,
    )


@admin_bp.route("/settings/fonts/new", methods=["GET", "POST"])
def create_font():
    font = MediaFont(provider="GOOGLE", active=True)
    errors: dict[str, str] = {}

    if request.method == "POST":
        form_data, errors = font_form_data(request.form)
        apply_font_data(font, form_data)
        font_conflict_errors(font, errors)

        if not errors:
            db.session.add(font)
            db.session.commit()
            flash(f"{font.display_name} was added.", "success")
            return redirect(url_for("admin.list_fonts"))

    return render_template(
        "admin/fonts/form.html",
        title="New Font",
        font=font,
        errors=errors,
        form_action=url_for("admin.create_font"),
        submit_label="Add font",
    ), (422 if errors else 200)


@admin_bp.route("/settings/fonts/<int:font_id>/edit", methods=["GET", "POST"])
def edit_font(font_id: int):
    font = get_font(font_id)
    errors: dict[str, str] = {}

    if request.method == "POST":
        old_family = font.family
        form_data, errors = font_form_data(request.form)
        apply_font_data(font, form_data)
        font_conflict_errors(font, errors)

        if old_family != font.family and font_usage_count(old_family) > 0:
            errors["family"] = "Fonts already used by slider media cannot be renamed."

        if not errors:
            db.session.commit()
            flash(f"{font.display_name} was updated.", "success")
            return redirect(url_for("admin.list_fonts"))

    return render_template(
        "admin/fonts/form.html",
        title=f"Edit {font.display_name}",
        font=font,
        errors=errors,
        form_action=url_for("admin.edit_font", font_id=font.id),
        submit_label="Save changes",
    ), (422 if errors else 200)


@admin_bp.post("/settings/fonts/<int:font_id>/delete")
def delete_font(font_id: int):
    font = get_font(font_id)
    if font_usage_count(font.family) > 0:
        flash(f"{font.display_name} is used by slider media and cannot be deleted.", "warning")
        return redirect(url_for("admin.list_fonts"))

    flash(f"{font.display_name} was deleted.", "success")
    db.session.delete(font)
    db.session.commit()
    return redirect(url_for("admin.list_fonts"))
