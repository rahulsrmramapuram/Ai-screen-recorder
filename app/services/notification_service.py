import time
import threading
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


def check_and_generate(app):
    """
    Scans database tasks and blockers to generate notifications:
    - Upcoming deadline: task deadline within 48h and status != 'Completed'
    - Overdue: task deadline past and status != 'Completed'
    - Blocker: unresolved blocker created > 24h ago
    """
    with app.app_context():
        from app.database import db
        from app.models import Task, Blocker, Notification

        now = datetime.now(timezone.utc)
        upcoming_window = now + timedelta(hours=48)
        blocker_cutoff = now - timedelta(hours=24)

        try:
            tasks = Task.query.all()
            for task in tasks:
                if not task.deadline:
                    continue

                deadline_utc = task.deadline if task.deadline.tzinfo else task.deadline.replace(tzinfo=timezone.utc)

                # Overdue check
                if deadline_utc < now and task.status != 'Completed':
                    existing = Notification.query.filter_by(
                        user_id=task.user_id,
                        task_id=task.id,
                        notification_type='overdue'
                    ).first()
                    if not existing:
                        n = Notification(
                            user_id=task.user_id,
                            task_id=task.id,
                            meeting_id=task.meeting_id,
                            message=f"Overdue: {task.title}",
                            notification_type='overdue',
                            is_read=False
                        )
                        db.session.add(n)

                # Upcoming deadline check (within 48 hours)
                elif now <= deadline_utc <= upcoming_window and task.status != 'Completed':
                    existing = Notification.query.filter_by(
                        user_id=task.user_id,
                        task_id=task.id,
                        notification_type='deadline'
                    ).first()
                    if not existing:
                        n = Notification(
                            user_id=task.user_id,
                            task_id=task.id,
                            meeting_id=task.meeting_id,
                            message=f"Upcoming deadline: {task.title}",
                            notification_type='deadline',
                            is_read=False
                        )
                        db.session.add(n)

            # Blocker check (>24h unresolved)
            blockers = Blocker.query.filter_by(status='unresolved').all()
            for blocker in blockers:
                created_utc = blocker.created_at if blocker.created_at.tzinfo else blocker.created_at.replace(tzinfo=timezone.utc)
                if created_utc <= blocker_cutoff:
                    # Get user_id from meeting
                    user_id = blocker.meeting.user_id if blocker.meeting else 1
                    existing = Notification.query.filter_by(
                        user_id=user_id,
                        meeting_id=blocker.meeting_id,
                        notification_type='blocker'
                    ).first()
                    if not existing:
                        n = Notification(
                            user_id=user_id,
                            task_id=blocker.task_id,
                            meeting_id=blocker.meeting_id,
                            message=f"Blocker needs attention: {blocker.description[:60]}...",
                            notification_type='blocker',
                            is_read=False
                        )
                        db.session.add(n)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"[NotificationService] Error generating notifications: {e}")


def start_background_scheduler(app, interval_seconds=900):
    """
    Launches a daemon thread on app startup checking every 15 minutes.
    """
    def run():
        # Small delay on initial startup
        time.sleep(2)
        while True:
            try:
                check_and_generate(app)
            except Exception as e:
                logger.error(f"[NotificationScheduler] Execution failed: {e}")
            time.sleep(interval_seconds)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()


# Pluggable Future Integration Interfaces (Email / Slack)
def send_email_notification(user_email: str, subject: str, message: str) -> bool:
    """Future email integration stub (SMTP / SendGrid)."""
    print(f"[Notifier Stub - Email] Sending to {user_email}: {subject}")
    return True

def send_slack_notification(webhook_url: str, message: str) -> bool:
    """Future Slack webhook stub."""
    print(f"[Notifier Stub - Slack] Sending to Webhook: {message}")
    return True
