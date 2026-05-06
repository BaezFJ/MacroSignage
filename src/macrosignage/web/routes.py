from flask import Blueprint, render_template

web_bp = Blueprint("web", __name__, template_folder="templates")


@web_bp.route("/")
def index():
    return render_template("web/index.html")