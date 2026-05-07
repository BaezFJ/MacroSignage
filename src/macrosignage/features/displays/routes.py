import json
import time

from flask import (
    abort,
    Blueprint,
    Response,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    stream_with_context,
    url_for,
)

from macrosignage.extensions import csrf, db

from ..admin.services import get_signage_settings
from ..admin.services import get_content_version
from ..media.forms import MEDIA_TYPES, font_choice_map, google_fonts_stylesheet_url, youtube_video_id
from ..media.services import list_active_fonts, vcard_payload
from .forms import DISPLAY_ORIENTATIONS, DISPLAY_STATUSES, display_form_data
from .models import Display
from .services import (
    apply_display_data,
    claim_display_registration,
    create_display_registration,
    disable_player_token,
    display_registration_for_claim_code,
    display_registration_for_key,
    display_for_player_token,
    display_has_player_access,
    display_playlist,
    enable_player_token,
    get_display,
    get_display_for_player,
    list_displays as query_displays,
    player_token_is_valid,
    qr_code_svg,
    remember_player_token_use,
    registration_is_expired,
    rotate_player_token,
    schedule_next_refresh_at,
)

displays_bp = Blueprint("admin_displays", __name__, url_prefix="/admin/displays")
display_player_bp = Blueprint("display_player", __name__, template_folder="templates", url_prefix="/displays")
PLAYER_ACCESS_SESSION_KEY = "display_player_access"
DISPLAY_REGISTRATION_SESSION_KEY = "display_registration_key"


def display_detail_context(display: Display, new_player_token: str | None = None) -> dict[str, object]:
    context = {
        "title": display.name,
        "display": display,
        "display_statuses": DISPLAY_STATUSES,
        "display_orientations": DISPLAY_ORIENTATIONS,
    }
    if new_player_token:
        context["new_player_token"] = new_player_token
        context["new_player_pairing_url"] = url_for(
            "display_player.show_display_player",
            display_id=display.id,
        )
    return context


def player_access_for_display(display: Display) -> str | None:
    player_access = session.get(PLAYER_ACCESS_SESSION_KEY)
    if not isinstance(player_access, dict):
        return None
    value = player_access.get(str(display.id))
    return value if isinstance(value, str) else None


def remember_player_access(display: Display) -> None:
    player_access = session.get(PLAYER_ACCESS_SESSION_KEY)
    if not isinstance(player_access, dict):
        player_access = {}
    player_access[str(display.id)] = display.player_access_key
    session[PLAYER_ACCESS_SESSION_KEY] = player_access


def player_unauthorized_reason(display: Display, submitted_token: str) -> str:
    if display.player_token_hash and not display.player_token_enabled:
        return "Display access disabled"
    if submitted_token:
        return "Invalid display token"
    return "Display access required"


def render_player_unauthorized(display: Display, submitted_token: str = ""):
    return render_template(
        "displays/unauthorized.html",
        title=f"{display.name} Access Required",
        display=display,
        reason=player_unauthorized_reason(display, submitted_token),
        pair_action=url_for("display_player.pair_display_player", display_id=display.id),
    ), 401


def get_claimable_registration(claim_code: str):
    registration = display_registration_for_claim_code(claim_code)
    if registration is None or registration.is_claimed or registration_is_expired(registration):
        abort(404)
    return registration


@displays_bp.get("/")
def list_displays():
    search_query = request.args.get("q", "").strip()
    selected_status = request.args.get("status", "").strip()
    status_filter = selected_status if selected_status in DISPLAY_STATUSES else ""

    return render_template(
        "admin/displays/list.html",
        title="Displays",
        displays=query_displays(search_query, status_filter),
        display_statuses=DISPLAY_STATUSES,
        search_query=search_query,
        selected_status=selected_status,
    )


@displays_bp.route("/new", methods=["GET", "POST"])
def create_display():
    display = Display(status="OFFLINE", orientation="LANDSCAPE", resolution_width=1920, resolution_height=1080)
    errors: dict[str, str] = {}

    if request.method == "POST":
        form_data, errors = display_form_data(request.form)
        apply_display_data(display, form_data)

        if not errors:
            db.session.add(display)
            db.session.commit()
            flash(f"{display.name} was created.", "success")
            return redirect(url_for("admin_displays.get_display_view", display_id=display.id))

    return render_template(
        "admin/displays/form.html",
        title="New Display",
        display=display,
        errors=errors,
        display_statuses=DISPLAY_STATUSES,
        display_orientations=DISPLAY_ORIENTATIONS,
        form_action=url_for("admin_displays.create_display"),
        submit_label="Create display",
    ), (422 if errors else 200)


@displays_bp.get("/scan")
def scan_display_qr():
    return render_template(
        "admin/displays/scan.html",
        title="Scan Display QR Code",
    )


@displays_bp.route("/claim/<claim_code>", methods=["GET", "POST"])
def claim_display_by_qr(claim_code: str):
    registration = get_claimable_registration(claim_code)
    display = Display(
        name="",
        status="OFFLINE",
        orientation="LANDSCAPE",
        resolution_width=1920,
        resolution_height=1080,
    )
    errors: dict[str, str] = {}

    if request.method == "POST":
        form_data, errors = display_form_data(request.form)
        apply_display_data(display, form_data)

        if not errors:
            db.session.add(display)
            rotate_player_token(display)
            claim_display_registration(registration, display)
            db.session.commit()
            flash(f"{display.name} was added and paired by QR code.", "success")
            return redirect(url_for("admin_displays.get_display_view", display_id=display.id))

    return render_template(
        "admin/displays/claim.html",
        title="Add Display by QR Code",
        display=display,
        errors=errors,
        display_statuses=DISPLAY_STATUSES,
        display_orientations=DISPLAY_ORIENTATIONS,
        form_action=url_for("admin_displays.claim_display_by_qr", claim_code=claim_code),
        submit_label="Add and pair display",
        registration=registration,
    ), (422 if errors else 200)


@displays_bp.get("/<int:display_id>")
def get_display_view(display_id: int):
    display = get_display(display_id)
    return render_template("admin/displays/detail.html", **display_detail_context(display))


@displays_bp.route("/<int:display_id>/edit", methods=["GET", "POST"])
def edit_display(display_id: int):
    display = get_display(display_id)
    errors: dict[str, str] = {}

    if request.method == "POST":
        form_data, errors = display_form_data(request.form)
        apply_display_data(display, form_data)

        if not errors:
            db.session.commit()
            flash(f"{display.name} was updated.", "success")
            return redirect(url_for("admin_displays.get_display_view", display_id=display.id))

    return render_template(
        "admin/displays/form.html",
        title=f"Edit {display.name}",
        display=display,
        errors=errors,
        display_statuses=DISPLAY_STATUSES,
        display_orientations=DISPLAY_ORIENTATIONS,
        form_action=url_for("admin_displays.edit_display", display_id=display.id),
        submit_label="Save changes",
    ), (422 if errors else 200)


@displays_bp.post("/<int:display_id>/delete")
def delete_display(display_id: int):
    display = get_display(display_id)
    flash(f"{display.name} was deleted.", "success")
    db.session.delete(display)
    db.session.commit()
    return redirect(url_for("admin_displays.list_displays"))


@displays_bp.post("/<int:display_id>/player-token/rotate")
def rotate_display_player_token(display_id: int):
    display = get_display(display_id)
    token = rotate_player_token(display)
    db.session.commit()
    return render_template("admin/displays/detail.html", **display_detail_context(display, token))


@displays_bp.post("/<int:display_id>/player-token/enable")
def enable_display_player_token(display_id: int):
    display = get_display(display_id)
    if enable_player_token(display):
        db.session.commit()
        flash(f"Player access for {display.name} was enabled.", "success")
    else:
        flash("Generate a player token before enabling player access.", "warning")
    return redirect(url_for("admin_displays.get_display_view", display_id=display.id))


@displays_bp.post("/<int:display_id>/player-token/disable")
def disable_display_player_token(display_id: int):
    display = get_display(display_id)
    disable_player_token(display)
    db.session.commit()
    flash(f"Player access for {display.name} was disabled.", "success")
    return redirect(url_for("admin_displays.get_display_view", display_id=display.id))


@display_player_bp.get("/uploads/<path:filename>")
def player_media_file(filename: str):
    return send_from_directory(current_app.config["MEDIA_UPLOAD_FOLDER"], filename)


@display_player_bp.get("/register")
def register_display_player():
    registration, claim_code, registration_key = create_display_registration()
    db.session.commit()
    session[DISPLAY_REGISTRATION_SESSION_KEY] = registration_key
    claim_url = url_for("admin_displays.claim_display_by_qr", claim_code=claim_code, _external=True)
    return render_template(
        "displays/register.html",
        title="Register Display",
        claim_url=claim_url,
        claim_qr_svg=qr_code_svg(claim_url),
        expires_at=registration.expires_at,
        status_url=url_for("display_player.display_registration_status"),
    )


@display_player_bp.get("/register/status")
def display_registration_status():
    registration_key = session.get(DISPLAY_REGISTRATION_SESSION_KEY)
    registration = display_registration_for_key(registration_key if isinstance(registration_key, str) else "")
    if registration is None or registration_is_expired(registration):
        session.pop(DISPLAY_REGISTRATION_SESSION_KEY, None)
        return jsonify({"status": "expired"}), 410

    if not registration.is_claimed or registration.display is None:
        return jsonify({"status": "pending", "expiresAt": registration.expires_at.isoformat()})

    remember_player_token_use(registration.display)
    db.session.commit()
    remember_player_access(registration.display)
    session.pop(DISPLAY_REGISTRATION_SESSION_KEY, None)
    return jsonify(
        {
            "status": "claimed",
            "playUrl": url_for("display_player.show_display_player", display_id=registration.display.id),
        }
    )


@display_player_bp.post("/<int:display_id>/pair")
@csrf.exempt
def pair_display_player(display_id: int):
    display = get_display_for_player(display_id)
    submitted_token = request.form.get("token", "").strip()
    if not player_token_is_valid(display, submitted_token):
        return render_player_unauthorized(display, submitted_token)

    remember_player_token_use(display)
    db.session.commit()
    remember_player_access(display)
    return redirect(url_for("display_player.show_display_player", display_id=display.id))


@display_player_bp.post("/pair")
@csrf.exempt
def pair_display_player_by_token():
    submitted_token = request.form.get("token", "").strip()
    display = display_for_player_token(submitted_token)
    if display is None:
        return render_template(
            "displays/pair_failed.html",
            title="Display Access Required",
            reason="Invalid display token",
        ), 401

    remember_player_token_use(display)
    db.session.commit()
    remember_player_access(display)
    return redirect(url_for("display_player.show_display_player", display_id=display.id))


@display_player_bp.get("/<int:display_id>/play")
def show_display_player(display_id: int):
    display = get_display_for_player(display_id)
    if display_has_player_access(display, player_access_for_display(display)):
        pass
    else:
        return render_player_unauthorized(display)

    if display.status == "MAINTENANCE":
        return render_template(
            "displays/maintenance.html",
            title=f"{display.name} Maintenance",
            display=display,
        )
    if display.status == "OFFLINE":
        return render_template(
            "displays/offline.html",
            title=f"{display.name} Offline",
            display=display,
        )

    playlist, default_duration = display_playlist(display)
    next_schedule_refresh_at = schedule_next_refresh_at(display)
    font_choices = font_choice_map(list_active_fonts())
    for media in playlist:
        if media.media_type == "SLIDER":
            for slide in media.slider_slides:
                font_choices.setdefault(slide.text_font_family, slide.text_font_family)
        elif media.media_type == "NEON_SIGN" and media.neon_font_family:
            font_choices.setdefault(media.neon_font_family, media.neon_font_family)
    return render_template(
        "displays/player.html",
        title=display.name,
        display=display,
        logo_settings=get_signage_settings(),
        playlist=playlist,
        default_duration=default_duration,
        next_schedule_refresh_at=next_schedule_refresh_at,
        google_font_families=font_choices,
        google_fonts_url=google_fonts_stylesheet_url(font_choices),
        media_types=MEDIA_TYPES,
        youtube_video_id=youtube_video_id,
        qr_code_svg=qr_code_svg,
        vcard_payload=vcard_payload,
    )


@display_player_bp.get("/<int:display_id>/events")
def display_events(display_id: int):
    display = get_display_for_player(display_id)
    if not display_has_player_access(display, player_access_for_display(display)):
        return render_player_unauthorized(display)

    @stream_with_context
    def event_stream():
        last_version = None
        while True:
            content_version = get_content_version()
            if content_version.version != last_version:
                last_version = content_version.version
                payload = {
                    "type": "content.updated",
                    "displayId": display.id,
                    "contentVersion": content_version.version,
                }
                yield f"event: content.updated\ndata: {json.dumps(payload)}\n\n"
            time.sleep(5)

    return Response(event_stream(), mimetype="text/event-stream")
