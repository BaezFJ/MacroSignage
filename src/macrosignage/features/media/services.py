from pathlib import Path
from uuid import uuid4

from flask import current_app
from sqlalchemy import func, or_
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from macrosignage.extensions import db

from .models import DEFAULT_GOOGLE_FONT_FAMILIES, MediaAsset, MediaFont, MediaSlide


def count_media() -> int:
    return db.session.scalar(db.select(func.count(MediaAsset.id))) or 0


def count_fonts() -> int:
    return db.session.scalar(db.select(func.count(MediaFont.id))) or 0


def seed_default_fonts() -> None:
    if count_fonts() > 0:
        return

    for family in DEFAULT_GOOGLE_FONT_FAMILIES:
        db.session.add(MediaFont(family=family, display_name=family, provider="GOOGLE", active=True))
    db.session.commit()


def list_fonts() -> list[MediaFont]:
    with db.session.no_autoflush:
        return db.session.scalars(db.select(MediaFont).order_by(MediaFont.display_name.asc(), MediaFont.id.asc())).all()


def list_active_fonts() -> list[MediaFont]:
    with db.session.no_autoflush:
        return db.session.scalars(
            db.select(MediaFont)
            .where(MediaFont.active.is_(True))
            .order_by(MediaFont.display_name.asc(), MediaFont.id.asc())
        ).all()


def get_font(font_id: int) -> MediaFont:
    return db.get_or_404(MediaFont, font_id)


def apply_font_data(font: MediaFont, form_data: dict[str, object]) -> None:
    font.family = str(form_data["family"])
    font.display_name = str(form_data["display_name"])
    font.provider = str(form_data["provider"])
    font.active = bool(form_data["active"])


def font_conflict_errors(font: MediaFont, errors: dict[str, str]) -> None:
    existing = MediaFont.query.filter(db.func.lower(MediaFont.family) == font.family.lower()).first()
    if existing and existing.id != font.id:
        errors["family"] = "A font with this family already exists."


def font_usage_count(family: str) -> int:
    return db.session.scalar(db.select(func.count(MediaSlide.id)).where(MediaSlide.text_font_family == family)) or 0


def list_media(search_query: str = "", selected_type: str = "") -> list[MediaAsset]:
    query = db.select(MediaAsset).order_by(MediaAsset.title.asc(), MediaAsset.id.asc())
    if search_query:
        like_query = f"%{search_query}%"
        query = query.where(or_(MediaAsset.title.ilike(like_query), MediaAsset.notes.ilike(like_query)))
    if selected_type:
        query = query.where(MediaAsset.media_type == selected_type)

    return db.session.scalars(query).all()


def list_all_media() -> list[MediaAsset]:
    with db.session.no_autoflush:
        return db.session.scalars(db.select(MediaAsset).order_by(MediaAsset.title.asc())).all()


def get_media(media_id: int) -> MediaAsset:
    return db.get_or_404(MediaAsset, media_id)


def selected_media(form) -> list[MediaAsset]:
    media_ids = []
    for raw_media_id in form.getlist("media_ids"):
        try:
            media_ids.append(int(raw_media_id))
        except ValueError:
            continue

    if not media_ids:
        return []

    return db.session.scalars(db.select(MediaAsset).where(MediaAsset.id.in_(media_ids))).all()


def save_upload(file: FileStorage) -> tuple[str, str, str]:
    original_filename = secure_filename(file.filename or "")
    extension = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else "bin"
    stored_filename = f"{uuid4().hex}.{extension}"
    upload_path = Path(current_app.config["MEDIA_UPLOAD_FOLDER"]) / stored_filename
    file.save(upload_path)
    return stored_filename, original_filename, file.mimetype


def delete_upload(filename: str | None) -> None:
    if not filename:
        return

    upload_path = Path(current_app.config["MEDIA_UPLOAD_FOLDER"]) / filename
    try:
        upload_path.unlink()
    except FileNotFoundError:
        pass


def apply_media_data(media: MediaAsset, form_data: dict[str, object], displays) -> None:
    media.media_type = str(form_data["media_type"])
    media.title = str(form_data["title"])
    media.body = form_data["body"] if media.media_type in {"TEXT", "HTML", "NEON_SIGN"} else None
    media.source_url = form_data["source_url"] if media.media_type == "YOUTUBE" else None
    media.neon_text_color = (
        str(form_data["neon_text_color"]) if media.media_type == "NEON_SIGN" else None
    )
    media.neon_frame_color = (
        str(form_data["neon_frame_color"]) if media.media_type == "NEON_SIGN" else None
    )
    media.neon_background_color = (
        str(form_data["neon_background_color"]) if media.media_type == "NEON_SIGN" else None
    )
    media.vcard_name = form_data["vcard_name"] if media.media_type == "VCARD" else None
    media.vcard_phone = form_data["vcard_phone"] if media.media_type == "VCARD" else None
    media.vcard_email = form_data["vcard_email"] if media.media_type == "VCARD" else None
    media.vcard_address = form_data["vcard_address"] if media.media_type == "VCARD" else None
    media.vcard_url = form_data["vcard_url"] if media.media_type == "VCARD" else None
    media.vcard_top_text = form_data["vcard_top_text"] if media.media_type == "VCARD" else None
    media.vcard_bottom_text = form_data["vcard_bottom_text"] if media.media_type == "VCARD" else None
    media.notes = form_data["notes"]
    media.displays = displays


def escape_vcard_value(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def vcard_payload(media: MediaAsset) -> str:
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"FN:{escape_vcard_value(media.vcard_name or media.title)}",
    ]
    if media.vcard_phone:
        lines.append(f"TEL;TYPE=CELL:{escape_vcard_value(media.vcard_phone)}")
    if media.vcard_email:
        lines.append(f"EMAIL:{escape_vcard_value(media.vcard_email)}")
    if media.vcard_address:
        lines.append(f"ADR;TYPE=WORK:;;{escape_vcard_value(media.vcard_address)};;;;")
    if media.vcard_url:
        lines.append(f"URL:{escape_vcard_value(media.vcard_url)}")
    lines.append("END:VCARD")
    return "\n".join(lines)


def clear_file_for_non_upload_type(media: MediaAsset) -> None:
    if media.media_type not in {"IMAGE", "VIDEO"} and media.file_path:
        delete_upload(media.file_path)
        media.file_path = None
        media.original_filename = None
        media.mime_type = None


def delete_slider_uploads(media: MediaAsset) -> None:
    for slide in media.slider_slides:
        delete_upload(slide.background_file_path)
        delete_upload(slide.foreground_file_path)


def clear_slider_for_non_slider_type(media: MediaAsset) -> None:
    if media.media_type == "SLIDER":
        return
    delete_slider_uploads(media)
    media.slider_slides.clear()


def apply_slider_slides(media: MediaAsset, slide_data: list[dict[str, object]]) -> None:
    existing_slides = list(media.slider_slides)

    for index, data in enumerate(slide_data):
        slide = existing_slides[index] if index < len(existing_slides) else MediaSlide()
        if slide not in media.slider_slides:
            media.slider_slides.append(slide)

        slide.sort_order = int(data["sort_order"])
        slide.text = data["text"]
        slide.text_position = str(data["text_position"])
        slide.text_font_family = str(data["text_font_family"])
        slide.text_font_size = int(data["text_font_size"])
        slide.text_animation = str(data["text_animation"])
        slide.foreground_size = int(data["foreground_size"])
        slide.foreground_position = str(data["foreground_position"])
        slide.foreground_animation = str(data["foreground_animation"])
        slide.duration_seconds = int(data["duration_seconds"])

        background_upload = data.get("background_upload")
        if background_upload and background_upload.filename:
            delete_upload(slide.background_file_path)
            (
                slide.background_file_path,
                slide.background_original_filename,
                _,
            ) = save_upload(background_upload)

        foreground_upload = data.get("foreground_upload")
        if foreground_upload and foreground_upload.filename:
            delete_upload(slide.foreground_file_path)
            (
                slide.foreground_file_path,
                slide.foreground_original_filename,
                _,
            ) = save_upload(foreground_upload)

    for slide in existing_slides[len(slide_data) :]:
        delete_upload(slide.background_file_path)
        delete_upload(slide.foreground_file_path)
        media.slider_slides.remove(slide)
