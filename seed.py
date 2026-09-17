import sys
from datetime import datetime, timedelta, timezone
from app import create_app
from app.database import db
from app.models import User, Meeting, Participant, Transcript, Task, Decision, Blocker, Notification

def seed_database():
    app = create_app()
    with app.app_context():
        print("[Seed] Checking existing seed data...")

        demo_user = User.query.filter_by(email="demo@solar.app").first()
        if demo_user:
            print("[Seed] Demo user 'demo@solar.app' already exists. Skipping seed generation.")
            return

        print("[Seed] Creating demo user: demo@solar.app / demo1234")
        demo_user = User(
            email="demo@solar.app",
            full_name="Alex Morgan"
        )
        demo_user.set_password("demo1234")
        db.session.add(demo_user)
        db.session.commit()

        now = datetime.now(timezone.utc)

        # ----------------------------------------------------
        # Meeting 1: Solar Platform Launch Strategy
        # ----------------------------------------------------
        m1 = Meeting(
            user_id=demo_user.id,
            title="Solar Platform Launch Strategy",
            meeting_date=now - timedelta(days=2),
            filename="20260915_product_sync.mp3",
            file_path="uploads/sample_sync.mp3",
            file_type="mp3",
            processing_status="completed"
        )
        db.session.add(m1)
        db.session.commit()

        # Participants
        for name in ["Alex Morgan", "Sarah Chen", "Michael Scott", "David Miller"]:
            db.session.add(Participant(meeting_id=m1.id, name=name))

        # Transcript
        t1_text = (
            "Alex: Good morning team. Let's align on our Solar launch roadmap.\n"
            "Sarah: We decided to deploy the core execution dashboard by next Friday.\n"
            "Alex: Excellent. Sarah, will you complete the mobile layout and CSS styling by tomorrow?\n"
            "Sarah: Yes, I will complete the CSS grid and mobile responsive styles by tomorrow.\n"
            "Michael: I am blocked on backend API development because I need the updated database schema from David before I can finish.\n"
            "Alex: David, please send the PostgreSQL schema documentation to Michael by 5 PM.\n"
            "David: Will do. I'll deliver the schema specs by 5 PM today.\n"
            "Michael: Great. I should also finish the notification background worker by May 28."
        )
        db.session.add(Transcript(meeting_id=m1.id, content=t1_text, language='en'))

        # Decisions
        db.session.add(Decision(meeting_id=m1.id, content="Deploy core execution dashboard by next Friday."))
        db.session.add(Decision(meeting_id=m1.id, content="Use standard session authentication for MVP release."))

        # Tasks
        task1 = Task(
            meeting_id=m1.id,
            user_id=demo_user.id,
            title="Complete CSS Grid & Mobile Responsive Styles",
            description="Finalize dark theme styling and responsive layout for mobile screens.",
            owner_name="Sarah Chen",
            deadline=now + timedelta(days=1),
            status="In Progress",
            source_quote="I will complete the CSS grid and mobile responsive styles by tomorrow."
        )
        task2 = Task(
            meeting_id=m1.id,
            user_id=demo_user.id,
            title="Deliver PostgreSQL Schema Documentation",
            description="Send updated table schemas and foreign key relationship specs to Michael.",
            owner_name="David Miller",
            deadline=now - timedelta(days=1),
            status="Overdue",
            source_quote="I'll deliver the schema specs by 5 PM today."
        )
        task3 = Task(
            meeting_id=m1.id,
            user_id=demo_user.id,
            title="Backend API Execution & Task Endpoints",
            description="Implement task filtering, status updates, and inline editing APIs.",
            owner_name="Michael Scott",
            deadline=now + timedelta(days=3),
            status="Blocked",
            source_quote="I am blocked on backend API development because I need the updated database schema from David."
        )
        task4 = Task(
            meeting_id=m1.id,
            user_id=demo_user.id,
            title="Configure Background Notification Scheduler Thread",
            description="Set up interval background daemon thread for 15-min notification checks.",
            owner_name="Alex Morgan",
            deadline=now + timedelta(days=5),
            status="Completed",
            source_quote="I should also finish the notification background worker by May 28."
        )
        db.session.add_all([task1, task2, task3, task4])
        db.session.commit()

        # Blocker
        b1 = Blocker(
            meeting_id=m1.id,
            task_id=task3.id,
            description="Waiting for updated PostgreSQL database schema from David before completing backend APIs.",
            owner_name="Michael Scott",
            status="unresolved"
        )
        db.session.add(b1)

        # ----------------------------------------------------
        # Meeting 2: Q3 Architecture & Security Sync
        # ----------------------------------------------------
        m2 = Meeting(
            user_id=demo_user.id,
            title="Q3 Architecture & Security Review",
            meeting_date=now - timedelta(days=5),
            filename="20260912_arch_review.txt",
            file_path="uploads/20260912_arch_review.txt",
            file_type="txt",
            processing_status="completed"
        )
        db.session.add(m2)
        db.session.commit()

        # Participants
        for name in ["Alex Morgan", "Elena Rostova", "Marcus Vance"]:
            db.session.add(Participant(meeting_id=m2.id, name=name))

        # Transcript
        t2_text = (
            "Alex: Let's confirm security requirements for file uploads and LLM key management.\n"
            "Elena: We agreed to enforce a strict 50MB file upload limit and validate extensions.\n"
            "Marcus: I will implement Werkzeug password hashing and Flask-WTF CSRF protection by Wednesday.\n"
            "Elena: I will create the Pytest test suite covering authentication, task CRUD, and AI JSON parsing.\n"
            "Alex: Confirmed. All LLM API keys must remain strictly server-side in environment variables."
        )
        db.session.add(Transcript(meeting_id=m2.id, content=t2_text, language='en'))

        # Decisions
        db.session.add(Decision(meeting_id=m2.id, content="Enforce strict 50MB upload limit and CSRF protection on all forms."))
        db.session.add(Decision(meeting_id=m2.id, content="Never expose LLM API keys to frontend client code."))

        # Tasks
        task5 = Task(
            meeting_id=m2.id,
            user_id=demo_user.id,
            title="Implement Werkzeug Password Hashing & CSRF Protection",
            description="Wrap forms with CSRF tokens and secure session management.",
            owner_name="Marcus Vance",
            deadline=now - timedelta(days=2),
            status="Completed",
            source_quote="I will implement Werkzeug password hashing and Flask-WTF CSRF protection by Wednesday."
        )
        task6 = Task(
            meeting_id=m2.id,
            user_id=demo_user.id,
            title="Create Pytest Suite (Auth, Tasks, AI JSON Parsing)",
            description="Write comprehensive automated unit test suite with SQLite in-memory fixtures.",
            owner_name="Elena Rostova",
            deadline=now + timedelta(days=2),
            status="Pending",
            source_quote="I will create the Pytest test suite covering authentication, task CRUD, and AI JSON parsing."
        )
        db.session.add_all([task5, task6])
        db.session.commit()

        # Seed Notifications
        n1 = Notification(
            user_id=demo_user.id,
            task_id=task2.id,
            meeting_id=m1.id,
            message=f"Overdue: {task2.title}",
            notification_type="overdue",
            is_read=False
        )
        n2 = Notification(
            user_id=demo_user.id,
            task_id=task1.id,
            meeting_id=m1.id,
            message=f"Upcoming deadline: {task1.title}",
            notification_type="deadline",
            is_read=False
        )
        n3 = Notification(
            user_id=demo_user.id,
            task_id=task3.id,
            meeting_id=m1.id,
            message=f"Blocker needs attention: Waiting for updated PostgreSQL database schema...",
            notification_type="blocker",
            is_read=False
        )
        db.session.add_all([n1, n2, n3])
        db.session.commit()

        print("[Seed] Seeding completed successfully!")
        print("  Demo Account: demo@solar.app")
        print("  Password:     demo1234")

if __name__ == '__main__':
    seed_database()
