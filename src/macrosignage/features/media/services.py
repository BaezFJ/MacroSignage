import re
import shutil
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

from flask import current_app
from slugify import slugify
from sqlalchemy import func, or_
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from macrosignage.extensions import db

from .models import DEFAULT_GOOGLE_FONT_FAMILIES, MediaAsset, MediaFont, MediaSlide

FONT_URL_PATTERN = re.compile(r"url\((['\"]?)(https://fonts\.gstatic\.com/[^)'\"\s]+)\1\)")
FONT_STORAGE_ROOT = "fonts"
GOOGLE_FONT_CSS_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


class FontDownloadError(RuntimeError):
    pass


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


def font_storage_slug(family: str) -> str:
    return slugify(family, separator="-") or secure_filename(family).lower() or uuid4().hex


def font_storage_folder(family: str) -> Path:
    return Path(current_app.config["MEDIA_UPLOAD_FOLDER"]) / FONT_STORAGE_ROOT / font_storage_slug(family)


def fetch_font_url(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": GOOGLE_FONT_CSS_USER_AGENT})
    try:
        with urlopen(request, timeout=15) as response:
            return response.read()
    except URLError as exc:
        raise FontDownloadError(str(exc)) from exc


def google_font_stylesheet_for_family(family: str) -> str:
    from .forms import google_fonts_stylesheet_url

    return google_fonts_stylesheet_url([family])


def downloaded_font_filename(url: str, index: int) -> str:
    parsed_name = Path(urlparse(url).path).name
    filename = secure_filename(parsed_name) or f"font-{index}.woff2"
    if "." not in filename:
        filename = f"{filename}.woff2"
    return f"{index}-{filename}"


def download_font_assets(font: MediaFont) -> None:
    target_folder = font_storage_folder(font.family)
    temp_folder = target_folder.with_name(f".{target_folder.name}-{uuid4().hex}")
    css_url = google_font_stylesheet_for_family(font.family)

    try:
        temp_folder.mkdir(parents=True, exist_ok=False)
        css = fetch_font_url(css_url).decode("utf-8")
        replacements: dict[str, str] = {}

        for index, match in enumerate(FONT_URL_PATTERN.finditer(css), start=1):
            remote_url = match.group(2)
            if remote_url in replacements:
                continue
            filename = downloaded_font_filename(remote_url, index)
            (temp_folder / filename).write_bytes(fetch_font_url(remote_url))
            replacements[remote_url] = filename

        if not replacements:
            raise FontDownloadError("Google Fonts returned no font files for this family.")

        for remote_url, filename in replacements.items():
            css = css.replace(remote_url, filename)
        (temp_folder / "font.css").write_text(css, encoding="utf-8")

        if target_folder.exists():
            shutil.rmtree(target_folder)
        temp_folder.rename(target_folder)
    except Exception as exc:
        shutil.rmtree(temp_folder, ignore_errors=True)
        if isinstance(exc, FontDownloadError):
            raise
        raise FontDownloadError(str(exc)) from exc

    font.local_css_path = f"{FONT_STORAGE_ROOT}/{target_folder.name}/font.css"
    font.download_status = "LOCAL"
    font.download_error = None


def delete_font_assets(font: MediaFont) -> None:
    if not font.local_css_path:
        return
    media_root = Path(current_app.config["MEDIA_UPLOAD_FOLDER"]).resolve()
    font_folder = (media_root / Path(font.local_css_path).parent).resolve()
    if media_root not in font_folder.parents or font_folder.name.startswith("."):
        return
    shutil.rmtree(font_folder, ignore_errors=True)


def font_stylesheet_paths(font_families) -> tuple[list[str], list[str]]:
    families = list(dict.fromkeys(font_families))
    if not families:
        return [], []

    fonts = db.session.scalars(db.select(MediaFont).where(MediaFont.family.in_(families))).all()
    fonts_by_family = {font.family: font for font in fonts}
    local_paths: list[str] = []
    remote_families: list[str] = []

    for family in families:
        font = fonts_by_family.get(family)
        if font and font.local_css_path:
            local_paths.append(font.local_css_path)
        else:
            remote_families.append(family)
    return local_paths, remote_families


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
    slide_count = db.session.scalar(db.select(func.count(MediaSlide.id)).where(MediaSlide.text_font_family == family)) or 0
    neon_count = db.session.scalar(
        db.select(func.count(MediaAsset.id)).where(
            MediaAsset.media_type == "NEON_SIGN",
            MediaAsset.neon_font_family == family,
        )
    ) or 0
    return slide_count + neon_count


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
    media.neon_font_family = str(form_data["neon_font_family"]) if media.media_type == "NEON_SIGN" else None
    media.neon_font_size = int(form_data["neon_font_size"]) if media.media_type == "NEON_SIGN" else None
    media.neon_frame_thickness = (
        int(form_data["neon_frame_thickness"]) if media.media_type == "NEON_SIGN" else None
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
