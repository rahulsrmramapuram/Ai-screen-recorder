from datetime import datetime, timezone
from app.database import db

class Transcript(db.Model):
    __tablename__ = 'transcripts'

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False, unique=True, index=True)
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), default='en')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "meeting_id": self.meeting_id,
            "content": self.content,
            "language": self.language,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
