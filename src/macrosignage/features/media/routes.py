from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, url_for

from macrosignage.extensions import db

from ..displays.services import list_all_displays, qr_code_svg, selected_displays
from .forms import (
    DEFAULT_SLIDER_ANIMATION,
    DEFAULT_SLIDER_FONT_FAMILY,
    DEFAULT_SLIDER_FONT_SIZE,
    DEFAULT_SLIDER_FOREGROUND_POSITION,
    DEFAULT_SLIDER_FOREGROUND_SIZE,
    DEFAULT_NEON_BACKGROUND_COLOR,
    DEFAULT_NEON_FONT_FAMILY,
    DEFAULT_NEON_FONT_SIZE,
    DEFAULT_NEON_FRAME_COLOR,
    DEFAULT_NEON_FRAME_THICKNESS,
    DEFAULT_NEON_TEXT_COLOR,
    MEDIA_TYPES,
    MAX_SLIDER_SLIDES,
    SLIDER_ANIMATIONS,
    SLIDER_FOREGROUND_POSITIONS,
    SLIDER_TEXT_POSITIONS,
    font_choice_map,
    google_fonts_stylesheet_url,
    media_form_data,
    youtube_video_id,
)
from .models import MediaAsset
from .services import (
    apply_media_data,
    apply_slider_slides,
    clear_file_for_non_upload_type,
    clear_slider_for_non_slider_type,
    delete_slider_uploads,
    delete_upload,
    get_media,
    list_active_fonts,
    list_media as query_media,
    save_upload,
    vcard_payload,
)

media_bp = Blueprint("admin_media", __name__, url_prefix="/admin/media")


def requested_slider_slide_count(default: int = 1) -> int:
    try:
        slide_count = int(request.form.get("slider_slide_count", str(default)))
    except ValueError:
        return default
    return min(max(slide_count, 1), MAX_SLIDER_SLIDES)


def include_existing_slider_fonts(font_choices: dict[str, str], media_items) -> dict[str, str]:
    choices = dict(font_choices)
    for media in media_items:
        if media.media_type == "SLIDER":
            for slide in media.slider_slides:
                choices.setdefault(slide.text_font_family, slide.text_font_family)
        elif media.media_type == "NEON_SIGN" and media.neon_font_family:
            choices.setdefault(media.neon_font_family, media.neon_font_family)
    return choices


@media_bp.get("/uploads/<path:filename>")
def uploaded_media(filename: str):
    return send_from_directory(current_app.config["MEDIA_UPLOAD_FOLDER"], filename)


@media_bp.get("/")
def list_media():
    search_query = request.args.get("q", "").strip()
    selected_type = request.args.get("media_type", "").strip()
    type_filter = selected_type if selected_type in MEDIA_TYPES else ""

    return render_template(
        "admin/media/list.html",
        title="Media Library",
        media_items=query_media(search_query, type_filter),
        media_types=MEDIA_TYPES,
        search_query=search_query,
        selected_type=selected_type,
    )


@media_bp.route("/new", methods=["GET", "POST"])
def create_media():
    media = MediaAsset(media_type="IMAGE")
    errors: dict[str, str] = {}
    displays = list_all_displays()
    slider_slide_count = 1
    fonts = list_active_fonts()
    font_choices = font_choice_map(fonts)

    if request.method == "POST":
        slider_slide_count = requested_slider_slide_count()
        form_data, errors = media_form_data(request.form, request.files, fonts=font_choices)
        if not errors:
            db.session.add(media)
        apply_media_data(media, form_data, selected_displays(request.form) if not errors else [])

        upload = request.files.get("file")
        if not errors and media.media_type in {"IMAGE", "VIDEO"} and upload and upload.filename:
            media.file_path, media.original_filename, media.mime_type = save_upload(upload)
        if not errors and media.media_type == "SLIDER":
            apply_slider_slides(media, form_data["slider_slides"])

        if not errors:
            db.session.commit()
            flash(f"{media.title} was created.", "success")
            return redirect(url_for("admin_media.get_media_view", media_id=media.id))

    return render_template(
        "admin/media/form.html",
        title="New Media",
        media=media,
        errors=errors,
        media_types=MEDIA_TYPES,
        google_font_families=font_choices,
        max_slider_slides=MAX_SLIDER_SLIDES,
        default_slider_font_family=DEFAULT_SLIDER_FONT_FAMILY,
        default_slider_font_size=DEFAULT_SLIDER_FONT_SIZE,
        default_slider_animation=DEFAULT_SLIDER_ANIMATION,
        default_slider_foreground_position=DEFAULT_SLIDER_FOREGROUND_POSITION,
        default_slider_foreground_size=DEFAULT_SLIDER_FOREGROUND_SIZE,
        default_neon_text_color=DEFAULT_NEON_TEXT_COLOR,
        default_neon_frame_color=DEFAULT_NEON_FRAME_COLOR,
        default_neon_background_color=DEFAULT_NEON_BACKGROUND_COLOR,
        default_neon_font_family=DEFAULT_NEON_FONT_FAMILY,
        default_neon_font_size=DEFAULT_NEON_FONT_SIZE,
        default_neon_frame_thickness=DEFAULT_NEON_FRAME_THICKNESS,
        slider_animations=SLIDER_ANIMATIONS,
        slider_foreground_positions=SLIDER_FOREGROUND_POSITIONS,
        slider_text_positions=SLIDER_TEXT_POSITIONS,
        slider_slide_count=slider_slide_count,
        slider_slides=[],
        displays=displays,
        form_action=url_for("admin_media.create_media"),
        submit_label="Create media",
    ), (422 if errors else 200)


@media_bp.get("/<int:media_id>")
def get_media_view(media_id: int):
    media = get_media(media_id)
    video_id = youtube_video_id(media.source_url or "") if media.media_type == "YOUTUBE" else None
    font_choices = include_existing_slider_fonts(font_choice_map(list_active_fonts()), [media])
    return render_template(
        "admin/media/detail.html",
        title=media.title,
        media=media,
        media_types=MEDIA_TYPES,
        youtube_video_id=video_id,
        google_font_families=font_choices,
        google_fonts_url=google_fonts_stylesheet_url(font_choices),
        slider_animations=SLIDER_ANIMATIONS,
        slider_foreground_positions=SLIDER_FOREGROUND_POSITIONS,
        slider_text_positions=SLIDER_TEXT_POSITIONS,
        qr_code_svg=qr_code_svg,
        vcard_payload=vcard_payload,
    )


@media_bp.route("/<int:media_id>/edit", methods=["GET", "POST"])
def edit_media(media_id: int):
    media = get_media(media_id)
    errors: dict[str, str] = {}
    displays = list_all_displays()
    slider_slide_count = len(media.slider_slides) or 1
    fonts = list_active_fonts()
    font_choices = include_existing_slider_fonts(font_choice_map(fonts), [media])

    if request.method == "POST":
        slider_slide_count = requested_slider_slide_count(slider_slide_count)
        old_file_path = media.file_path
        form_data, errors = media_form_data(request.form, request.files, media, font_choices)
        apply_media_data(media, form_data, selected_displays(request.form))

        upload = request.files.get("file")
        if not errors and media.media_type in {"IMAGE", "VIDEO"} and upload and upload.filename:
            media.file_path, media.original_filename, media.mime_type = save_upload(upload)
            delete_upload(old_file_path)
        if not errors and media.media_type == "SLIDER":
            apply_slider_slides(media, form_data["slider_slides"])
        if not errors:
            clear_file_for_non_upload_type(media)
            clear_slider_for_non_slider_type(media)
            db.session.commit()
            flash(f"{media.title} was updated.", "success")
            return redirect(url_for("admin_media.get_media_view", media_id=media.id))

    return render_template(
        "admin/media/form.html",
        title=f"Edit {media.title}",
        media=media,
        errors=errors,
        media_types=MEDIA_TYPES,
        google_font_families=font_choices,
        max_slider_slides=MAX_SLIDER_SLIDES,
        default_slider_font_family=DEFAULT_SLIDER_FONT_FAMILY,
        default_slider_font_size=DEFAULT_SLIDER_FONT_SIZE,
        default_slider_animation=DEFAULT_SLIDER_ANIMATION,
        default_slider_foreground_position=DEFAULT_SLIDER_FOREGROUND_POSITION,
        default_slider_foreground_size=DEFAULT_SLIDER_FOREGROUND_SIZE,
        default_neon_text_color=DEFAULT_NEON_TEXT_COLOR,
        default_neon_frame_color=DEFAULT_NEON_FRAME_COLOR,
        default_neon_background_color=DEFAULT_NEON_BACKGROUND_COLOR,
        default_neon_font_family=DEFAULT_NEON_FONT_FAMILY,
        default_neon_font_size=DEFAULT_NEON_FONT_SIZE,
        default_neon_frame_thickness=DEFAULT_NEON_FRAME_THICKNESS,
        slider_animations=SLIDER_ANIMATIONS,
        slider_foreground_positions=SLIDER_FOREGROUND_POSITIONS,
        slider_text_positions=SLIDER_TEXT_POSITIONS,
        slider_slide_count=slider_slide_count,
        slider_slides=list(media.slider_slides),
        displays=displays,
        form_action=url_for("admin_media.edit_media", media_id=media.id),
        submit_label="Save changes",
    ), (422 if errors else 200)


@media_bp.post("/<int:media_id>/delete")
def delete_media(media_id: int):
    media = get_media(media_id)
    flash(f"{media.title} was deleted.", "success")
    delete_upload(media.file_path)
    delete_slider_uploads(media)
    db.session.delete(media)
    db.session.commit()
    return redirect(url_for("admin_media.list_media"))
