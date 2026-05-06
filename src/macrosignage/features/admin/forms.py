from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

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
