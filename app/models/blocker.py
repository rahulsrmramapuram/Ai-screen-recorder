from datetime import datetime, timezone
from app.database import db

class Blocker(db.Model):
    __tablename__ = 'blockers'

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False, index=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True, index=True)
    description = db.Column(db.Text, nullable=False)
    owner_name = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='unresolved') # unresolved, resolved
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "meeting_id": self.meeting_id,
            "task_id": self.task_id,
            "description": self.description,
            "owner_name": self.owner_name,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
