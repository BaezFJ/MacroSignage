__version__ = "0.1.0"

from flask import Flask, render_template


def create_app():

    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template("pages/index.html", title="Macro Signage")

    return app
