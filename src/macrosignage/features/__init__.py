from .auth.routes import auth_bp, users_bp
from .admin.routes import admin_bp
from .displays.routes import display_player_bp, displays_bp
from .media.routes import media_bp
from .schedules.routes import schedules_bp

features_bp = [auth_bp, admin_bp, displays_bp, media_bp, schedules_bp, users_bp, display_player_bp]
__all__ = ["features_bp"]
