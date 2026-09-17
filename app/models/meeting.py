from datetime import datetime, timezone
from app.database import db

class Meeting(db.Model):
    __tablename__ = 'meetings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    meeting_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    filename = db.Column(db.String(255), nullable=True)
    file_path = db.Column(db.String(512), nullable=True)
    file_type = db.Column(db.String(50), nullable=True)
    processing_status = db.Column(db.String(50), nullable=False, default='pending') # pending, processing, completed, failed
    processing_error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    participants = db.relationship('Participant', backref='meeting', lazy=True, cascade="all, delete-orphan")
    transcript = db.relationship('Transcript', backref='meeting', uselist=False, cascade="all, delete-orphan")
    tasks = db.relationship('Task', backref='meeting', lazy=True, cascade="all, delete-orphan")
    decisions = db.relationship('Decision', backref='meeting', lazy=True, cascade="all, delete-orphan")
    blockers = db.relationship('Blocker', backref='meeting', lazy=True, cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='meeting', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "meeting_date": self.meeting_date.isoformat() if self.meeting_date else None,
            "filename": self.filename,
            "file_type": self.file_type,
            "processing_status": self.processing_status,
            "processing_error": self.processing_error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "task_count": len(self.tasks),
            "decision_count": len(self.decisions)
        }
