import os
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from app.config import Config
from app.database import db, resolve_database_uri

login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Dynamic database URI resolution with fallback to SQLite
    raw_db_url = app.config.get("SQLALCHEMY_DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/solar")
    app.config["SQLALCHEMY_DATABASE_URI"] = resolve_database_uri(raw_db_url)

    # Ensure uploads directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    csrf.init_app(app)

    # Import models for user loader and db initialization
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.meetings import meetings_bp
    from app.routes.tasks import tasks_bp
    from app.routes.notifications import notifications_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(meetings_bp, url_prefix="/meetings")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(notifications_bp, url_prefix="/notifications")

    # Create tables automatically inside context
    with app.app_context():
        db.create_all()

    # Start notification service background thread if not testing
    if not app.config.get('TESTING'):
        from app.services.notification_service import start_background_scheduler
        start_background_scheduler(app)

    return app
