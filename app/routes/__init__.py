from app.routes.auth import auth_bp
from app.routes.main import main_bp
from app.routes.meetings import meetings_bp
from app.routes.tasks import tasks_bp
from app.routes.notifications import notifications_bp

__all__ = [
    'auth_bp',
    'main_bp',
    'meetings_bp',
    'tasks_bp',
    'notifications_bp'
]
