from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy

csrf = CSRFProtect()
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
