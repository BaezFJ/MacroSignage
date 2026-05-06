from __future__ import annotations

from functools import wraps

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from macrosignage.extensions import db, login_manager

from .forms import (
    USER_ROLES,
    login_form_data,
    password_reset_form_data,
    password_reset_request_form_data,
    user_form_data,
)
from .models import User
from .services import (
    apply_user_data,
    authenticate_user,
    count_admin_users,
    count_users,
    create_password_reset_token,
    find_user_by_reset_token,
    get_user,
    list_users as query_users,
    reset_user_password,
    user_data_conflict_errors,
    user_conflict_errors,
)

auth_bp = Blueprint("auth", __name__, template_folder="templates", url_prefix="/auth")
users_bp = Blueprint("admin_users", __name__, url_prefix="/admin/users")


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def safe_next_url(value: str | None) -> str:
    if value and value.startswith("/") and not value.startswith("//"):
        return value
    return url_for("admin.get_dashboard")


@auth_bp.route("/setup", methods=["GET", "POST"])
def get_setup():
    if count_users() > 0:
        return redirect(url_for("auth.get_login"))

    user = User(role="ADMIN", active=True)
    errors: dict[str, str] = {}

    if request.method == "POST":
        form_data, errors = user_form_data(request.form, require_password=True)
        form_data["role"] = "ADMIN"
        form_data["active"] = True
        apply_user_data(user, form_data)
        user_conflict_errors(user, errors)

        if not errors:
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Admin account created.", "success")
            return redirect(url_for("admin.get_dashboard"))

    return render_template(
        "auth/setup.html",
        title="Create Admin Account",
        user=user,
        errors=errors,
    ), (422 if errors else 200)


@auth_bp.route("/login", methods=["GET", "POST"])
def get_login():
    if current_user.is_authenticated:
        return redirect(safe_next_url(request.args.get("next")))

    form_data = {"identifier": ""}
    errors: dict[str, str] = {}

    if request.method == "POST":
        form_data, errors = login_form_data(request.form)
        if not errors:
            user = authenticate_user(form_data["identifier"], form_data["password"])
            if user is None:
                errors["password"] = "Invalid username, email, or password."
            else:
                login_user(user)
                flash("Signed in.", "success")
                return redirect(safe_next_url(request.args.get("next")))

    return render_template(
        "auth/login.html",
        title="Login",
        form_data=form_data,
        errors=errors,
        setup_available=count_users() == 0,
    ), (422 if errors else 200)


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Signed out.", "info")
    return redirect(url_for("auth.get_login"))


@auth_bp.route("/password-reset", methods=["GET", "POST"])
def request_password_reset():
    form_data = {"email": ""}
    errors: dict[str, str] = {}
    reset_url = None

    if request.method == "POST":
        form_data, errors = password_reset_request_form_data(request.form)
        if not errors:
            user = User.query.filter(db.func.lower(User.email) == form_data["email"].lower()).first()
            if user and user.active:
                token = create_password_reset_token(user)
                if current_app.config.get("AUTH_SHOW_RESET_LINKS") or current_app.debug:
                    reset_url = url_for("auth.reset_password", token=token, _external=True)
            flash("If that email matches an active account, a reset link has been prepared.", "info")

    return render_template(
        "auth/password_reset_request.html",
        title="Reset Password",
        form_data=form_data,
        errors=errors,
        reset_url=reset_url,
    ), (422 if errors else 200)


@auth_bp.route("/password-reset/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    user = find_user_by_reset_token(token)
    if user is None:
        flash("Password reset link is invalid or expired.", "warning")
        return redirect(url_for("auth.request_password_reset"))

    errors: dict[str, str] = {}

    if request.method == "POST":
        form_data, errors = password_reset_form_data(request.form)
        if not errors:
            reset_user_password(user, form_data["password"])
            flash("Password updated. Sign in with your new password.", "success")
            return redirect(url_for("auth.get_login"))

    return render_template(
        "auth/password_reset_form.html",
        title="Set New Password",
        errors=errors,
        token=token,
    ), (422 if errors else 200)


@users_bp.get("/")
@admin_required
def list_users():
    search_query = request.args.get("q", "").strip()
    selected_role = request.args.get("role", "").strip()
    role_filter = selected_role if selected_role in USER_ROLES else ""

    return render_template(
        "admin/users/list.html",
        title="Users",
        users=query_users(search_query, role_filter),
        user_roles=USER_ROLES,
        search_query=search_query,
        selected_role=selected_role,
    )


@users_bp.route("/new", methods=["GET", "POST"])
@admin_required
def create_user():
    user = User(role="VIEWER", active=True)
    errors: dict[str, str] = {}

    if request.method == "POST":
        form_data, errors = user_form_data(request.form, require_password=True)
        apply_user_data(user, form_data)
        user_conflict_errors(user, errors)

        if not errors:
            db.session.add(user)
            db.session.commit()
            flash(f"{user.username} was created.", "success")
            return redirect(url_for("admin_users.get_user_view", user_id=user.id))

    return render_template(
        "admin/users/form.html",
        title="New User",
        user=user,
        errors=errors,
        user_roles=USER_ROLES,
        form_action=url_for("admin_users.create_user"),
        submit_label="Create user",
        password_required=True,
    ), (422 if errors else 200)


@users_bp.get("/<int:user_id>")
@admin_required
def get_user_view(user_id: int):
    user = get_user(user_id)
    return render_template(
        "admin/users/detail.html",
        title=user.username,
        user=user,
        user_roles=USER_ROLES,
    )


@users_bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_user(user_id: int):
    user = get_user(user_id)
    errors: dict[str, str] = {}

    if request.method == "POST":
        form_data, errors = user_form_data(request.form, require_password=False)
        removing_final_admin = user.is_admin and user.active and (
            form_data["role"] != "ADMIN" or not bool(form_data["active"])
        )
        user_data_conflict_errors(
            user_id=user.id,
            username=str(form_data["username"]),
            email=str(form_data["email"]),
            errors=errors,
        )
        if removing_final_admin and count_admin_users(exclude_user_id=user.id) == 0:
            errors["role"] = "At least one active admin account is required."

        if not errors:
            apply_user_data(user, form_data)
            db.session.commit()
            flash(f"{user.username} was updated.", "success")
            return redirect(url_for("admin_users.get_user_view", user_id=user.id))

    return render_template(
        "admin/users/form.html",
        title=f"Edit {user.username}",
        user=user,
        errors=errors,
        user_roles=USER_ROLES,
        form_action=url_for("admin_users.edit_user", user_id=user.id),
        submit_label="Save changes",
        password_required=False,
    ), (422 if errors else 200)


@users_bp.post("/<int:user_id>/delete")
@admin_required
def delete_user(user_id: int):
    user = get_user(user_id)
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "warning")
        return redirect(url_for("admin_users.get_user_view", user_id=user.id))
    if user.is_admin and user.active and count_admin_users(exclude_user_id=user.id) == 0:
        flash("At least one active admin account is required.", "warning")
        return redirect(url_for("admin_users.get_user_view", user_id=user.id))

    flash(f"{user.username} was deleted.", "success")
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("admin_users.list_users"))
