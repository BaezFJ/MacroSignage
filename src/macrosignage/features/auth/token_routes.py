from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from macrosignage.extensions import db

from .api_token_forms import api_token_form_data
from .models import User
from .permissions import admin_required
from .services import create_api_token, delete_api_token, get_api_token, list_api_tokens, reset_api_token, revoke_api_token

tokens_bp = Blueprint("admin_tokens", __name__, url_prefix="/admin/api-tokens")


@tokens_bp.get("/")
@admin_required
def list_tokens():
    return render_template(
        "admin/api_tokens/list.html",
        title="API Tokens",
        tokens=list_api_tokens(),
        users=User.query.filter_by(active=True).order_by(User.username.asc()).all(),
    )


@tokens_bp.post("/")
@admin_required
def create_token():
    form_data, errors = api_token_form_data(request.form)
    if errors:
        return render_template(
            "admin/api_tokens/list.html",
            title="API Tokens",
            tokens=list_api_tokens(),
            users=User.query.filter_by(active=True).order_by(User.username.asc()).all(),
            errors=errors,
            form_data=form_data,
        ), 422

    api_token, plaintext_token = create_api_token(form_data["user"], str(form_data["name"]))
    db.session.commit()
    flash("API token created. Copy it now; it will not be shown again.", "success")
    return render_template(
        "admin/api_tokens/list.html",
        title="API Tokens",
        tokens=list_api_tokens(),
        users=User.query.filter_by(active=True).order_by(User.username.asc()).all(),
        new_token=api_token,
        plaintext_token=plaintext_token,
    )


@tokens_bp.post("/<int:token_id>/revoke")
@admin_required
def revoke_token(token_id: int):
    api_token = get_api_token(token_id)
    revoke_api_token(api_token)
    db.session.commit()
    flash(f"{api_token.name} was revoked.", "success")
    return redirect(url_for("admin_tokens.list_tokens"))


@tokens_bp.post("/<int:token_id>/reset")
@admin_required
def reset_token(token_id: int):
    api_token = get_api_token(token_id)
    plaintext_token = reset_api_token(api_token)
    db.session.commit()
    flash(f"{api_token.name} was reset. Copy the new token now; it will not be shown again.", "warning")
    return render_template(
        "admin/api_tokens/list.html",
        title="API Tokens",
        tokens=list_api_tokens(),
        users=User.query.filter_by(active=True).order_by(User.username.asc()).all(),
        new_token=api_token,
        plaintext_token=plaintext_token,
    )


@tokens_bp.post("/<int:token_id>/delete")
@admin_required
def delete_token(token_id: int):
    api_token = get_api_token(token_id)
    token_name = api_token.name
    delete_api_token(api_token)
    db.session.commit()
    flash(f"{token_name} was deleted.", "success")
    return redirect(url_for("admin_tokens.list_tokens"))
