from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models.meeting import Meeting
from app.models.task import Task
from app.models.notification import Notification

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    now = datetime.now(timezone.utc)
    seven_days = now + timedelta(days=7)

    recent_meetings = Meeting.query.filter_by(user_id=current_user.id)\
        .order_by(Meeting.created_at.desc()).limit(5).all()

    all_user_tasks = Task.query.filter_by(user_id=current_user.id).all()

    total_tasks = len(all_user_tasks)
    completed_tasks = sum(1 for t in all_user_tasks if t.computed_status == 'Completed')
    pending_tasks = sum(1 for t in all_user_tasks if t.computed_status in ['Pending', 'In Progress'])
    overdue_tasks = sum(1 for t in all_user_tasks if t.computed_status == 'Overdue')
    blocked_tasks = sum(1 for t in all_user_tasks if t.computed_status == 'Blocked')

    upcoming_tasks = [
        t for t in all_user_tasks 
        if t.deadline and now <= (t.deadline if t.deadline.tzinfo else t.deadline.replace(tzinfo=timezone.utc)) <= seven_days
        and t.computed_status != 'Completed'
    ]

    unread_notifications_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    return render_template(
        'dashboard.html',
        recent_meetings=recent_meetings,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        overdue_tasks=overdue_tasks,
        blocked_tasks=blocked_tasks,
        upcoming_tasks=upcoming_tasks,
        unread_notifications_count=unread_notifications_count
    )
