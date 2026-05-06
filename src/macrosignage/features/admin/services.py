from macrosignage.extensions import db

from ..media.services import delete_upload, save_upload
from .models import SignageSettings


def get_signage_settings() -> SignageSettings:
    settings = db.session.get(SignageSettings, 1)
    if settings is None:
        settings = SignageSettings(id=1)
        db.session.add(settings)
        db.session.commit()
    return settings


def apply_logo_settings(settings: SignageSettings, form_data: dict[str, object]) -> None:
    settings.logo_enabled = bool(form_data["logo_enabled"])
    settings.logo_position = str(form_data["logo_position"])

    if form_data["remove_logo"]:
        delete_upload(settings.logo_file_path)
        settings.logo_file_path = None
        settings.logo_original_filename = None
        settings.logo_mime_type = None

    logo_upload = form_data.get("logo_upload")
    if logo_upload and logo_upload.filename:
        delete_upload(settings.logo_file_path)
        settings.logo_file_path, settings.logo_original_filename, settings.logo_mime_type = save_upload(logo_upload)
