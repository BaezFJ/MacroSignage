from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from macrosignage.config import DATABASE_OPTIONS, database_uri_from_parts, validate_database_uri

from ..media.forms import IMAGE_EXTENSIONS, IMAGE_MIME_TYPES


LOGO_POSITIONS = {
    "TOP_LEFT": "Top left",
    "TOP_RIGHT": "Top right",
    "BOTTOM_LEFT": "Bottom left",
    "BOTTOM_RIGHT": "Bottom right",
}


def validate_logo_upload(file: FileStorage, errors: dict[str, str]) -> None:
    filename = secure_filename(file.filename or "")
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in IMAGE_EXTENSIONS or file.mimetype not in IMAGE_MIME_TYPES:
        errors["logo"] = "Upload a JPG, PNG, GIF, or WebP image."


def logo_settings_form_data(form, files) -> tuple[dict[str, object], dict[str, str]]:
    errors: dict[str, str] = {}
    logo_position = form.get("logo_position", "TOP_RIGHT").strip()
    logo_upload = files.get("logo")

    if logo_position not in LOGO_POSITIONS:
        errors["logo_position"] = "Choose a valid logo position."
    if logo_upload and logo_upload.filename:
        validate_logo_upload(logo_upload, errors)

    return (
        {
            "logo_enabled": form.get("logo_enabled") == "on",
            "logo_position": logo_position,
            "logo_upload": logo_upload,
            "remove_logo": form.get("remove_logo") == "on",
        },
        errors,
    )


def database_settings_form_data(form) -> tuple[dict[str, object], dict[str, str]]:
    errors: dict[str, str] = {}
    database_type = form.get("database_type", "advanced").strip()
    if not database_type and form.get("database_uri"):
        database_type = "advanced"
    if database_type not in DATABASE_OPTIONS:
        database_type = "advanced"

    form_data = {
        "database_type": database_type,
        "sqlite_path": form.get("sqlite_path", "").strip(),
        "host": form.get("host", "").strip(),
        "port": form.get("port", "").strip(),
        "username": form.get("username", "").strip(),
        "password": form.get("password", ""),
        "database_name": form.get("database_name", "").strip(),
        "query": form.get("query", "").strip(),
        "database_uri": form.get("database_uri", "").strip(),
    }

    if database_type == "sqlite" and not form_data["sqlite_path"]:
        errors["sqlite_path"] = "SQLite database location is required."
    elif database_type not in {"sqlite", "advanced"}:
        if not form_data["host"]:
            errors["host"] = "Database host is required."
        if not form_data["database_name"]:
            errors["database_name"] = "Database name is required."
        if form_data["port"]:
            try:
                port = int(str(form_data["port"]))
            except ValueError:
                errors["port"] = "Port must be a whole number."
            else:
                if not 1 <= port <= 65535:
                    errors["port"] = "Port must be between 1 and 65535."

    if not errors:
        try:
            database_uri = database_uri_from_parts(**form_data)
        except (KeyError, TypeError, ValueError):
            database_uri = ""
            errors["database_uri"] = "Database settings could not be converted to a URI."
        form_data["database_uri"] = database_uri
    else:
        database_uri = str(form_data["database_uri"])

    if not errors and len(database_uri) > 1000:
        errors["database_uri"] = "Database URI cannot exceed 1000 characters."
    elif not errors:
        database_error = validate_database_uri(database_uri)
        if database_error:
            errors["database_uri"] = database_error

    return form_data, errors
