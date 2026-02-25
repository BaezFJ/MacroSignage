__version__ = "0.1.0"

from flask import Flask


def macro_signage_app():
    app = Flask(__name__)

    @app.route('/')
    def hello_world():
        return 'Hello World!'

    return app
