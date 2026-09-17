from datetime import datetime, timezone
from app.database import db

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    owner_name = db.Column(db.String(100), nullable=True)
    deadline = db.Column(db.DateTime, nullable=True, index=True)
    status = db.Column(db.String(50), nullable=False, default='Pending') # Pending, In Progress, Completed, Blocked, Overdue
    source_quote = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    blockers = db.relationship('Blocker', backref='task', lazy=True, cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='task', lazy=True, cascade="all, delete-orphan")

    @property
    def computed_status(self):
        now = datetime.now(timezone.utc)
        if self.deadline:
            deadline_utc = self.deadline if self.deadline.tzinfo else self.deadline.replace(tzinfo=timezone.utc)
            if deadline_utc < now and self.status != 'Completed':
                return 'Overdue'
        return self.status

    def to_dict(self):
        return {
            "id": self.id,
            "meeting_id": self.meeting_id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "owner_name": self.owner_name or "Unassigned",
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "status": self.computed_status,
            "source_quote": self.source_quote,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
