import re
from urllib.parse import parse_qs, urlencode, urlparse

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from .models import DEFAULT_GOOGLE_FONT_FAMILIES

MEDIA_TYPES = {
    "IMAGE": "Image",
    "TEXT": "Text",
    "VIDEO": "Video",
    "HTML": "HTML",
    "YOUTUBE": "YouTube video",
    "SLIDER": "Slider",
    "NEON_SIGN": "Neon Sign",
    "VCARD": "vCard",
}

SLIDER_TEXT_POSITIONS = {
    "TOP_LEFT": "Top left",
    "TOP_CENTER": "Top center",
    "TOP_RIGHT": "Top right",
    "CENTER_LEFT": "Center left",
    "CENTER": "Center",
    "CENTER_RIGHT": "Center right",
    "BOTTOM_LEFT": "Bottom left",
    "BOTTOM_CENTER": "Bottom center",
    "BOTTOM_RIGHT": "Bottom right",
}

SLIDER_FOREGROUND_POSITIONS = SLIDER_TEXT_POSITIONS

SLIDER_ANIMATIONS = {
    "NONE": "None",
    "fadeIn": "Fade in",
    "fadeInDown": "Fade in down",
    "fadeInLeft": "Fade in left",
    "fadeInRight": "Fade in right",
    "fadeInUp": "Fade in up",
    "zoomIn": "Zoom in",
    "zoomInDown": "Zoom in down",
    "zoomInLeft": "Zoom in left",
    "zoomInRight": "Zoom in right",
    "bounceIn": "Bounce in",
    "bounceInDown": "Bounce in down",
    "bounceInLeft": "Bounce in left",
    "bounceInRight": "Bounce in right",
    "slideInDown": "Slide in down",
    "slideInLeft": "Slide in left",
    "slideInRight": "Slide in right",
    "slideInUp": "Slide in up",
}

GOOGLE_FONT_FAMILIES = {family: family for family in DEFAULT_GOOGLE_FONT_FAMILIES}

MAX_SLIDER_SLIDES = 12
DEFAULT_SLIDER_ANIMATION = "NONE"
DEFAULT_SLIDER_DURATION = 10
DEFAULT_SLIDER_FOREGROUND_SIZE = 50
DEFAULT_SLIDER_FOREGROUND_POSITION = "CENTER"
MIN_SLIDER_FOREGROUND_SIZE = 10
MAX_SLIDER_FOREGROUND_SIZE = 100
DEFAULT_SLIDER_FONT_FAMILY = "Inter"
DEFAULT_SLIDER_FONT_SIZE = 72
MIN_SLIDER_FONT_SIZE = 16
MAX_SLIDER_FONT_SIZE = 240
FONT_FAMILY_PATTERN = re.compile(r"^[A-Za-z0-9 .:&'_-]+$")
HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
DEFAULT_NEON_TEXT_COLOR = "#ff4fd8"
DEFAULT_NEON_FRAME_COLOR = "#37ff79"
DEFAULT_NEON_BACKGROUND_COLOR = "#1b1210"
DEFAULT_NEON_FONT_FAMILY = "Inter"
DEFAULT_NEON_FONT_SIZE = 120
MIN_NEON_FONT_SIZE = 24
MAX_NEON_FONT_SIZE = 260
DEFAULT_NEON_FRAME_THICKNESS = 8
MIN_NEON_FRAME_THICKNESS = 2
MAX_NEON_FRAME_THICKNESS = 48

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
VIDEO_EXTENSIONS = {"mp4", "webm", "ogg", "mov"}
IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
VIDEO_MIME_TYPES = {"video/mp4", "video/webm", "video/ogg", "video/quicktime"}


def font_choice_map(fonts=None) -> dict[str, str]:
    if fonts is None:
        return GOOGLE_FONT_FAMILIES
    if isinstance(fonts, dict):
        return fonts
    return {font.family: font.display_name for font in fonts}


def google_fonts_stylesheet_url(font_families) -> str:
    families = list(font_families) or list(DEFAULT_GOOGLE_FONT_FAMILIES)
    params = [("family", f"{family}:wght@400;600;700;800") for family in families]
    return f"https://fonts.googleapis.com/css2?{urlencode(params)}&display=swap"


def normalize_display_text(value: str) -> str:
    return value.strip().replace("\\n", "\n")


def font_form_data(form) -> tuple[dict[str, object], dict[str, str]]:
    errors: dict[str, str] = {}
    family = form.get("family", "").strip()
    display_name = form.get("display_name", "").strip()
    active = form.get("active") == "on"

    if not family:
        errors["family"] = "Font family is required."
    elif len(family) > 80:
        errors["family"] = "Font family cannot exceed 80 characters."
    elif not FONT_FAMILY_PATTERN.match(family):
        errors["family"] = "Use the Google Fonts family name without URL syntax."

    if not display_name:
        display_name = family
    elif len(display_name) > 120:
        errors["display_name"] = "Display name cannot exceed 120 characters."

    return (
        {
            "family": family,
            "display_name": display_name,
            "active": active,
            "provider": "GOOGLE",
        },
        errors,
    )


def youtube_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")

    if host == "youtu.be":
        return parsed.path.strip("/") or None
    if host in {"youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        if parsed.path.startswith("/embed/") or parsed.path.startswith("/shorts/"):
            return parsed.path.split("/", 2)[2] or None

    return None


def validate_upload(file: FileStorage, media_type: str, errors: dict[str, str]) -> None:
    if not file or not file.filename:
        errors["file"] = "Upload a file for this media type."
        return

    filename = secure_filename(file.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if media_type == "IMAGE":
        if extension not in IMAGE_EXTENSIONS or file.mimetype not in IMAGE_MIME_TYPES:
            errors["file"] = "Upload a JPG, PNG, GIF, or WebP image."
    elif media_type == "VIDEO":
        if extension not in VIDEO_EXTENSIONS or file.mimetype not in VIDEO_MIME_TYPES:
            errors["file"] = "Upload an MP4, WebM, OGG, or MOV video."


def validate_slider_image(file: FileStorage, field: str, errors: dict[str, str]) -> None:
    filename = secure_filename(file.filename or "")
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in IMAGE_EXTENSIONS or file.mimetype not in IMAGE_MIME_TYPES:
        errors[field] = "Upload a JPG, PNG, GIF, or WebP image."


def parse_positive_int(value: str, field_label: str) -> tuple[int | None, str | None]:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None, f"{field_label} must be a whole number."

    if parsed <= 0:
        return None, f"{field_label} must be greater than zero."
    return parsed, None


def parse_hex_color(value: str, default: str, field_label: str) -> tuple[str, str | None]:
    color = (value or default).strip()
    if HEX_COLOR_PATTERN.match(color):
        return color.lower(), None
    return default, f"{field_label} must be a 6-digit hex color."


def slider_form_data(form, files, media=None, fonts=None) -> tuple[list[dict[str, object]], dict[str, str]]:
    errors: dict[str, str] = {}
    available_fonts = font_choice_map(fonts)
    slide_count, count_error = parse_positive_int(form.get("slider_slide_count", "1"), "Slide count")
    if count_error:
        errors["slider_slide_count"] = count_error
        slide_count = 1
    elif slide_count > MAX_SLIDER_SLIDES:
        errors["slider_slide_count"] = f"Slide count cannot exceed {MAX_SLIDER_SLIDES}."
        slide_count = MAX_SLIDER_SLIDES

    existing_slides = list(media.slider_slides) if media is not None and media.media_type == "SLIDER" else []
    slides: list[dict[str, object]] = []
    for index in range(slide_count or 1):
        background_field = f"slider_background_{index}"
        foreground_field = f"slider_foreground_{index}"
        foreground_size_field = f"slider_foreground_size_{index}"
        foreground_position_field = f"slider_foreground_position_{index}"
        foreground_animation_field = f"slider_foreground_animation_{index}"
        duration_field = f"slider_duration_{index}"
        font_size_field = f"slider_font_size_{index}"
        text_animation_field = f"slider_text_animation_{index}"
        position = form.get(f"slider_text_position_{index}", "CENTER").strip()
        foreground_position = form.get(foreground_position_field, DEFAULT_SLIDER_FOREGROUND_POSITION).strip()
        foreground_animation = form.get(foreground_animation_field, DEFAULT_SLIDER_ANIMATION).strip()
        text_animation = form.get(text_animation_field, DEFAULT_SLIDER_ANIMATION).strip()
        font_family = form.get(f"slider_font_family_{index}", DEFAULT_SLIDER_FONT_FAMILY).strip()
        duration, duration_error = parse_positive_int(
            form.get(duration_field, str(DEFAULT_SLIDER_DURATION)),
            f"Slide {index + 1} duration",
        )
        font_size, font_size_error = parse_positive_int(
            form.get(font_size_field, str(DEFAULT_SLIDER_FONT_SIZE)),
            f"Slide {index + 1} font size",
        )
        foreground_size, foreground_size_error = parse_positive_int(
            form.get(foreground_size_field, str(DEFAULT_SLIDER_FOREGROUND_SIZE)),
            f"Slide {index + 1} foreground size",
        )
        background_upload = files.get(background_field)
        foreground_upload = files.get(foreground_field)
        existing_slide = existing_slides[index] if index < len(existing_slides) else None

        if position not in SLIDER_TEXT_POSITIONS:
            errors[f"slider_text_position_{index}"] = "Choose a valid text position."
        if foreground_position not in SLIDER_FOREGROUND_POSITIONS:
            errors[foreground_position_field] = "Choose a valid foreground position."
        if foreground_animation not in SLIDER_ANIMATIONS:
            errors[foreground_animation_field] = "Choose a valid foreground animation."
        if text_animation not in SLIDER_ANIMATIONS:
            errors[text_animation_field] = "Choose a valid text animation."
        if font_family not in available_fonts:
            errors[f"slider_font_family_{index}"] = "Choose a valid font family."
        if duration_error:
            errors[duration_field] = duration_error
        elif duration and duration > 3600:
            errors[duration_field] = "Slide duration cannot exceed 1 hour."
        if font_size_error:
            errors[font_size_field] = font_size_error
        elif font_size and not MIN_SLIDER_FONT_SIZE <= font_size <= MAX_SLIDER_FONT_SIZE:
            errors[font_size_field] = (
                f"Font size must be between {MIN_SLIDER_FONT_SIZE} and {MAX_SLIDER_FONT_SIZE} pixels."
            )
        if foreground_size_error:
            errors[foreground_size_field] = foreground_size_error
        elif foreground_size and not MIN_SLIDER_FOREGROUND_SIZE <= foreground_size <= MAX_SLIDER_FOREGROUND_SIZE:
            errors[foreground_size_field] = (
                f"Foreground size must be between {MIN_SLIDER_FOREGROUND_SIZE}% and {MAX_SLIDER_FOREGROUND_SIZE}%."
            )

        if background_upload and background_upload.filename:
            validate_slider_image(background_upload, background_field, errors)
        elif existing_slide is None or not existing_slide.background_file_path:
            errors[background_field] = "Upload a background image."

        if foreground_upload and foreground_upload.filename:
            validate_slider_image(foreground_upload, foreground_field, errors)

        slides.append(
            {
                "sort_order": index,
                "text": normalize_display_text(form.get(f"slider_text_{index}", "")) or None,
                "text_position": position,
                "text_font_family": font_family,
                "text_font_size": font_size or DEFAULT_SLIDER_FONT_SIZE,
                "text_animation": text_animation,
                "foreground_size": foreground_size or DEFAULT_SLIDER_FOREGROUND_SIZE,
                "foreground_position": foreground_position,
                "foreground_animation": foreground_animation,
                "duration_seconds": duration or DEFAULT_SLIDER_DURATION,
                "background_upload": background_upload,
                "foreground_upload": foreground_upload,
            }
        )

    return slides, errors


def media_form_data(form, files, media=None, fonts=None) -> tuple[dict[str, object], dict[str, str]]:
    errors: dict[str, str] = {}
    available_fonts = font_choice_map(fonts)
    title = form.get("title", "").strip()
    media_type = form.get("media_type", "IMAGE").strip()
    raw_body = form.get("body", "").strip()
    source_url = form.get("source_url", "").strip()
    neon_font_family = form.get("neon_font_family", DEFAULT_NEON_FONT_FAMILY).strip()
    vcard_name = form.get("vcard_name", "").strip()
    vcard_phone = form.get("vcard_phone", "").strip()
    vcard_email = form.get("vcard_email", "").strip()
    vcard_address = form.get("vcard_address", "").strip()
    vcard_url = form.get("vcard_url", "").strip()
    vcard_top_text = normalize_display_text(form.get("vcard_top_text", ""))
    vcard_bottom_text = normalize_display_text(form.get("vcard_bottom_text", ""))
    notes = form.get("notes", "").strip()
    upload = files.get("file")
    slider_slides: list[dict[str, object]] = []
    neon_text_color, neon_text_color_error = parse_hex_color(
        form.get("neon_text_color", DEFAULT_NEON_TEXT_COLOR),
        DEFAULT_NEON_TEXT_COLOR,
        "Neon text color",
    )
    neon_frame_color, neon_frame_color_error = parse_hex_color(
        form.get("neon_frame_color", DEFAULT_NEON_FRAME_COLOR),
        DEFAULT_NEON_FRAME_COLOR,
        "Neon frame color",
    )
    neon_background_color, neon_background_color_error = parse_hex_color(
        form.get("neon_background_color", DEFAULT_NEON_BACKGROUND_COLOR),
        DEFAULT_NEON_BACKGROUND_COLOR,
        "Neon background color",
    )
    neon_font_size, neon_font_size_error = parse_positive_int(
        form.get("neon_font_size", str(DEFAULT_NEON_FONT_SIZE)),
        "Font size",
    )
    neon_frame_thickness, neon_frame_thickness_error = parse_positive_int(
        form.get("neon_frame_thickness", str(DEFAULT_NEON_FRAME_THICKNESS)),
        "Frame thickness",
    )

    if not title:
        errors["title"] = "Media title is required."
    if media_type not in MEDIA_TYPES:
        errors["media_type"] = "Choose a valid media type."
    body = normalize_display_text(raw_body) if media_type in {"TEXT", "NEON_SIGN"} else raw_body

    if media_type in {"IMAGE", "VIDEO"}:
        if upload and upload.filename:
            validate_upload(upload, media_type, errors)
        elif media is not None and media.media_type != media_type:
            errors["file"] = "Upload a replacement file when changing between file media types."
        elif media is None or not media.file_path:
            errors["file"] = "Upload a file for this media type."
    elif media_type in {"TEXT", "HTML", "NEON_SIGN"}:
        if not body:
            errors["body"] = "Content is required for this media type."
    elif media_type == "YOUTUBE":
        if not source_url:
            errors["source_url"] = "YouTube URL is required."
        elif youtube_video_id(source_url) is None:
            errors["source_url"] = "Enter a valid YouTube watch, shorts, embed, or youtu.be URL."
    elif media_type == "VCARD":
        if not vcard_name:
            errors["vcard_name"] = "Contact name is required."
        if not any([vcard_phone, vcard_email, vcard_address, vcard_url]):
            errors["vcard_contact"] = "Enter at least one phone, email, address, or URL."
    elif media_type == "SLIDER":
        slider_slides, slider_errors = slider_form_data(form, files, media, fonts)
        errors.update(slider_errors)
    if media_type == "NEON_SIGN":
        if neon_text_color_error:
            errors["neon_text_color"] = neon_text_color_error
        if neon_frame_color_error:
            errors["neon_frame_color"] = neon_frame_color_error
        if neon_background_color_error:
            errors["neon_background_color"] = neon_background_color_error
        if neon_font_family not in available_fonts:
            errors["neon_font_family"] = "Choose a valid font style."
        if neon_font_size_error:
            errors["neon_font_size"] = neon_font_size_error
        elif neon_font_size and not MIN_NEON_FONT_SIZE <= neon_font_size <= MAX_NEON_FONT_SIZE:
            errors["neon_font_size"] = (
                f"Font size must be between {MIN_NEON_FONT_SIZE} and {MAX_NEON_FONT_SIZE} pixels."
            )
        if neon_frame_thickness_error:
            errors["neon_frame_thickness"] = neon_frame_thickness_error
        elif neon_frame_thickness and not MIN_NEON_FRAME_THICKNESS <= neon_frame_thickness <= MAX_NEON_FRAME_THICKNESS:
            errors["neon_frame_thickness"] = (
                "Frame thickness must be between "
                f"{MIN_NEON_FRAME_THICKNESS} and {MAX_NEON_FRAME_THICKNESS} pixels."
            )

    return (
        {
            "title": title,
            "media_type": media_type,
            "body": body or None,
            "source_url": source_url or None,
            "notes": notes or None,
            "slider_slides": slider_slides,
            "neon_text_color": neon_text_color,
            "neon_frame_color": neon_frame_color,
            "neon_background_color": neon_background_color,
            "neon_font_family": neon_font_family,
            "neon_font_size": neon_font_size or DEFAULT_NEON_FONT_SIZE,
            "neon_frame_thickness": neon_frame_thickness or DEFAULT_NEON_FRAME_THICKNESS,
            "vcard_name": vcard_name or None,
            "vcard_phone": vcard_phone or None,
            "vcard_email": vcard_email or None,
            "vcard_address": vcard_address or None,
            "vcard_url": vcard_url or None,
            "vcard_top_text": vcard_top_text or None,
            "vcard_bottom_text": vcard_bottom_text or None,
        },
        errors,
    )
