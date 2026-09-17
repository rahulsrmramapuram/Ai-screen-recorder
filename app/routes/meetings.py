import os
import threading
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.database import db
from app.models import Meeting, Participant, Transcript, Task, Decision, Blocker
from app.services import transcribe_file, extract_meeting_insights, check_and_generate

meetings_bp = Blueprint('meetings', __name__)


def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def process_meeting_async(app, meeting_id: int):
    """
    Background worker function running in a separate thread.
    Executes transcription, AI extraction, database persistence, and status updates.
    """
    with app.app_context():
        meeting = Meeting.query.get(meeting_id)
        if not meeting:
            print(f"[Async Worker] Meeting {meeting_id} not found.")
            return

        try:
            meeting.processing_status = 'processing'
            db.session.commit()

            # 1. Transcription
            file_path = meeting.file_path or ""
            file_type = meeting.file_type or "txt"
            openai_key = app.config.get("OPENAI_API_KEY", "")

            transcript_text = transcribe_file(file_path, file_type, openai_key)
            if not transcript_text:
                transcript_text = "No audio or text content could be processed from the recording."

            # Save Transcript
            transcript = Transcript(
                meeting_id=meeting.id,
                content=transcript_text,
                language='en'
            )
            db.session.add(transcript)
            db.session.commit()

            # 2. AI Extraction
            gemini_key = app.config.get("GEMINI_API_KEY", "")
            insights = extract_meeting_insights(transcript_text, gemini_key, openai_key)

            # 3. Persist Decisions
            for dec_str in insights.get("decisions", []):
                if dec_str and isinstance(dec_str, str):
                    d = Decision(meeting_id=meeting.id, content=dec_str.strip())
                    db.session.add(d)

            # 4. Persist Tasks
            created_tasks = []
            for item in insights.get("action_items", []):
                if not isinstance(item, dict):
                    continue

                title = item.get("title") or item.get("description") or "Action Item"
                desc = item.get("description") or title
                owner = item.get("owner") or "Unassigned"
                quote = item.get("source_quote") or ""
                deadline_val = item.get("deadline")

                deadline_dt = None
                if deadline_val:
                    try:
                        deadline_dt = datetime.fromisoformat(str(deadline_val).replace("Z", "+00:00"))
                    except Exception:
                        try:
                            deadline_dt = datetime.strptime(str(deadline_val), "%Y-%m-%d")
                        except Exception:
                            deadline_dt = None

                t = Task(
                    meeting_id=meeting.id,
                    user_id=meeting.user_id,
                    title=str(title).strip()[:255],
                    description=str(desc).strip(),
                    owner_name=str(owner).strip()[:100],
                    deadline=deadline_dt,
                    status='Pending',
                    source_quote=str(quote).strip()
                )
                db.session.add(t)
                created_tasks.append(t)

            db.session.flush() # assign task IDs

            # 5. Persist Blockers & Associate with Task
            for block_item in insights.get("blockers", []):
                desc = ""
                owner = None
                if isinstance(block_item, dict):
                    desc = block_item.get("description", "")
                    owner = block_item.get("owner")
                elif isinstance(block_item, str):
                    desc = block_item

                if desc:
                    # Match blocker to created task if description shares words
                    assoc_task_id = None
                    for t in created_tasks:
                        if any(word.lower() in t.title.lower() for word in desc.split() if len(word) > 4):
                            assoc_task_id = t.id
                            t.status = 'Blocked'
                            break

                    b = Blocker(
                        meeting_id=meeting.id,
                        task_id=assoc_task_id,
                        description=str(desc).strip(),
                        owner_name=str(owner).strip()[:100] if owner else "Team",
                        status='unresolved'
                    )
                    db.session.add(b)

            meeting.processing_status = 'completed'
            db.session.commit()

            # Trigger notification evaluation
            check_and_generate(app)
            print(f"[Async Worker] Meeting {meeting_id} processing completed successfully.")

        except Exception as e:
            db.session.rollback()
            meeting.processing_status = 'failed'
            meeting.processing_error = str(e)
            db.session.commit()
            print(f"[Async Worker] Meeting {meeting_id} processing failed: {e}")


@meetings_bp.route('/')
@login_required
def index():
    meetings = Meeting.query.filter_by(user_id=current_user.id)\
        .order_by(Meeting.created_at.desc()).all()
    return render_template('meetings/index.html', meetings=meetings)


@meetings_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        meeting_date_str = request.form.get('meeting_date', '').strip()
        participants_str = request.form.get('participants', '').strip()
        raw_transcript = request.form.get('raw_transcript', '').strip()

        if not title:
            flash('Meeting title is required.', 'danger')
            return render_template('meetings/new.html')

        # Parse date
        meeting_date = datetime.now(timezone.utc)
        if meeting_date_str:
            try:
                meeting_date = datetime.strptime(meeting_date_str, '%Y-%m-%d')
            except ValueError:
                pass

        saved_filename = None
        saved_file_path = None
        file_ext = 'txt'

        file = request.files.get('file')
        if file and file.filename != '':
            if not allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
                flash('Unsupported file extension. Allowed: .mp3, .mp4, .wav, .m4a, .txt, .pdf', 'danger')
                return render_template('meetings/new.html')

            sec_filename = secure_filename(file.filename)
            file_ext = sec_filename.rsplit('.', 1)[1].lower() if '.' in sec_filename else 'txt'
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            saved_filename = f"{timestamp}_{sec_filename}"
            saved_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], saved_filename)
            file.save(saved_file_path)

        elif raw_transcript:
            # Write raw transcript to temporary upload txt file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            saved_filename = f"{timestamp}_transcript.txt"
            saved_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], saved_filename)
            with open(saved_file_path, 'w', encoding='utf-8') as f:
                f.write(raw_transcript)
            file_ext = 'txt'
        else:
            flash('Please upload an audio/video recording or paste a text transcript.', 'danger')
            return render_template('meetings/new.html')

        # Create Meeting
        meeting = Meeting(
            user_id=current_user.id,
            title=title,
            meeting_date=meeting_date,
            filename=saved_filename,
            file_path=saved_file_path,
            file_type=file_ext,
            processing_status='pending'
        )
        db.session.add(meeting)
        db.session.commit()

        # Add Participants
        if participants_str:
            names = [p.strip() for p in participants_str.split(',') if p.strip()]
            for p_name in names:
                part = Participant(meeting_id=meeting.id, name=p_name)
                db.session.add(part)
            db.session.commit()

        # Launch background thread for async processing
        app_obj = current_app._get_current_object()
        thread = threading.Thread(target=process_meeting_async, args=(app_obj, meeting.id))
        thread.start()

        flash('Meeting recording uploaded! AI processing started.', 'info')
        return redirect(url_for('meetings.detail', id=meeting.id))

    return render_template('meetings/new.html')


@meetings_bp.route('/<int:id>')
@login_required
def detail(id):
    meeting = Meeting.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('meetings/detail.html', meeting=meeting)


@meetings_bp.route('/<int:id>/status')
@login_required
def status(id):
    meeting = Meeting.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return jsonify({
        "status": meeting.processing_status,
        "error": meeting.processing_error
    })


@meetings_bp.route('/<int:id>/tasks', methods=['POST'])
@login_required
def create_task(id):
    meeting = Meeting.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    data = request.get_json() or request.form

    title = data.get('title', '').strip()
    if not title:
        return jsonify({"error": "Title is required"}), 400

    owner = data.get('owner_name', 'Unassigned').strip()
    deadline_val = data.get('deadline')
    deadline_dt = None
    if deadline_val:
        try:
            deadline_dt = datetime.fromisoformat(str(deadline_val))
        except Exception:
            pass

    task = Task(
        meeting_id=meeting.id,
        user_id=current_user.id,
        title=title,
        description=data.get('description', ''),
        owner_name=owner,
        deadline=deadline_dt,
        status='Pending',
        source_quote=data.get('source_quote', '')
    )
    db.session.add(task)
    db.session.commit()

    return jsonify({"success": True, "task": task.to_dict()})
