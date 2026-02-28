from os import getcwd
from os.path import abspath, dirname, join

from flask import Flask, redirect, url_for, send_from_directory

from .utils import create_instance_config, create_dir
from .blueprints import blueprints
from .extensions import extensions

# Current working directory
cwd = getcwd()
# Current application directory
cad = abspath(dirname(__file__))


def macro_signage_app(instance_path=None):
    """
    Create a new instance of the Macro Signage application.

    Args:
        instance_path: Path to instance.

    Returns:
        Flask application.
    """

    # set the instance path
    if instance_path is None:
        instance_path = join(cwd, 'instance')

    # Create instance config file if it doesn't exist
    create_instance_config(instance_path)
    create_dir(join(instance_path, 'uploads'))

    # Default config file
    application_default_config_file = join(cad, 'config.py')
    # Instance config file
    application_instance_config_file = join(cwd, 'instance', 'config.py')

    app = Flask(__name__,
                template_folder='ui/templates',
                static_folder='ui/static',
                instance_relative_config=True,
                instance_path=instance_path)

    # Load default config
    app.config.from_pyfile(application_default_config_file)
    # Load instance config overriding default config
    app.config.from_pyfile(application_instance_config_file, silent=True)

    @app.route('/uploads/<path:filename>')
    def download_file(filename):
        """
        Download file.
        """
        return send_from_directory(app.config['UPLOAD_PATH'], filename,
                                   as_attachment=True)

    @app.get('/init-db')
    def init_db():
        from macrosignage.extensions import db
        try:
            db.create_all()
        except Exception as e:
            print(e)
        return redirect(url_for('.index'))

    # Register blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    # Register extensions
    for extension in extensions:
        extension.init_app(app)

    with app.app_context():
        from .extensions import db
        db.create_all()

    return app
