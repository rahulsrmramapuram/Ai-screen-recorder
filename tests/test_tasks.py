from datetime import datetime, timedelta, timezone
from app.database import db
from app.models import Meeting, Task

def login_client(client):
    return client.post('/login', data={
        'email': 'testuser@solar.app',
        'password': 'password123'
    }, follow_redirects=True)


def test_task_creation_and_status_update(client, auth_user, app):
    login_client(client)

    with app.app_context():
        m = Meeting(user_id=auth_user, title="Test Meeting", processing_status="completed")
        db.session.add(m)
        db.session.commit()
        meeting_id = m.id

    # Create task via meeting route
    res = client.post(f'/meetings/{meeting_id}/tasks', json={
        'title': 'Build API Unit Tests',
        'owner_name': 'Test User',
        'deadline': '2026-10-01'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    task_id = data['task']['id']

    # Update status via /tasks/<id>/status
    status_res = client.post(f'/tasks/{task_id}/status', json={'status': 'Completed'})
    assert status_res.status_code == 200
    assert status_res.get_json()['task']['status'] == 'Completed'


def test_task_overdue_filter(client, auth_user, app):
    login_client(client)
    now = datetime.now(timezone.utc)

    with app.app_context():
        m = Meeting(user_id=auth_user, title="Filter Test Meeting", processing_status="completed")
        db.session.add(m)
        db.session.commit()

        # Overdue task
        t_overdue = Task(
            meeting_id=m.id,
            user_id=auth_user,
            title="Overdue Task Example",
            deadline=now - timedelta(days=2),
            status="Pending"
        )
        # Completed task
        t_completed = Task(
            meeting_id=m.id,
            user_id=auth_user,
            title="Completed Task Example",
            deadline=now - timedelta(days=1),
            status="Completed"
        )
        db.session.add_all([t_overdue, t_completed])
        db.session.commit()

    # Filter overdue tasks
    res = client.get('/tasks?filter=overdue')
    assert res.status_code == 200
    assert b'Overdue Task Example' in res.data
    assert b'Completed Task Example' not in res.data
