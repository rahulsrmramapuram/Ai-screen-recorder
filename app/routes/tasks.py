from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from app.database import db
from app.models.task import Task

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('', methods=['GET'])
@tasks_bp.route('/', methods=['GET'])
@login_required
def index():
    filter_type = request.args.get('filter', 'all').lower()
    now = datetime.now(timezone.utc)
    seven_days = now + timedelta(days=7)

    query = Task.query.filter_by(user_id=current_user.id)

    all_tasks = query.order_by(Task.created_at.desc()).all()

    # Filter evaluation
    filtered_tasks = []
    for task in all_tasks:
        c_status = task.computed_status

        if filter_type == 'all':
            filtered_tasks.append(task)
        elif filter_type == 'my_tasks':
            # Match task owner to user full name or email username
            user_first_name = current_user.full_name.split()[0].lower() if current_user.full_name else ""
            if task.owner_name and (user_first_name in task.owner_name.lower() or current_user.email in task.owner_name.lower()):
                filtered_tasks.append(task)
            elif not task.owner_name or task.owner_name == 'Unassigned':
                filtered_tasks.append(task)
        elif filter_type == 'pending':
            if c_status == 'Pending':
                filtered_tasks.append(task)
        elif filter_type == 'in_progress':
            if c_status == 'In Progress':
                filtered_tasks.append(task)
        elif filter_type == 'completed':
            if c_status == 'Completed':
                filtered_tasks.append(task)
        elif filter_type == 'overdue':
            if c_status == 'Overdue':
                filtered_tasks.append(task)
        elif filter_type == 'blocked':
            if c_status == 'Blocked':
                filtered_tasks.append(task)
        elif filter_type == 'upcoming':
            if task.deadline and c_status != 'Completed':
                deadline_utc = task.deadline if task.deadline.tzinfo else task.deadline.replace(tzinfo=timezone.utc)
                if now <= deadline_utc <= seven_days:
                    filtered_tasks.append(task)
        else:
            filtered_tasks.append(task)

    # Counts for tab badges
    counts = {
        "all": len(all_tasks),
        "pending": sum(1 for t in all_tasks if t.computed_status == 'Pending'),
        "in_progress": sum(1 for t in all_tasks if t.computed_status == 'In Progress'),
        "completed": sum(1 for t in all_tasks if t.computed_status == 'Completed'),
        "overdue": sum(1 for t in all_tasks if t.computed_status == 'Overdue'),
        "blocked": sum(1 for t in all_tasks if t.computed_status == 'Blocked'),
        "upcoming": sum(1 for t in all_tasks if t.deadline and t.computed_status != 'Completed' and now <= (t.deadline if t.deadline.tzinfo else t.deadline.replace(tzinfo=timezone.utc)) <= seven_days)
    }

    return render_template('tasks/index.html', tasks=filtered_tasks, current_filter=filter_type, counts=counts)


@tasks_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    data = request.get_json() or request.form
    new_status = data.get('status')

    valid_statuses = ['Pending', 'In Progress', 'Completed', 'Blocked', 'Overdue']
    if new_status in valid_statuses:
        task.status = new_status
        db.session.commit()
        return jsonify({"success": True, "task": task.to_dict()})
    
    return jsonify({"error": "Invalid status"}), 400


@tasks_bp.route('/<int:id>', methods=['PATCH', 'PUT', 'POST'])
@login_required
def update_task(id):
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    data = request.get_json() or request.form

    if 'title' in data:
        task.title = str(data['title']).strip()
    if 'description' in data:
        task.description = str(data['description']).strip()
    if 'owner_name' in data:
        task.owner_name = str(data['owner_name']).strip()
    if 'status' in data:
        valid_statuses = ['Pending', 'In Progress', 'Completed', 'Blocked', 'Overdue']
        if data['status'] in valid_statuses:
            task.status = data['status']
    if 'deadline' in data:
        deadline_val = data['deadline']
        if not deadline_val:
            task.deadline = None
        else:
            try:
                task.deadline = datetime.fromisoformat(str(deadline_val).replace("Z", "+00:00"))
            except Exception:
                try:
                    task.deadline = datetime.strptime(str(deadline_val), "%Y-%m-%d")
                except Exception:
                    pass

    db.session.commit()
    return jsonify({"success": True, "task": task.to_dict()})


@tasks_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_task(id):
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    return jsonify({"success": True})
