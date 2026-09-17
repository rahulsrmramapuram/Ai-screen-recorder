# Solar — AI Meeting → Execution Web Application

Solar is an AI-powered meeting-to-execution platform that transforms raw meeting recordings (audio/video/text) into structured, traceable work items (action items, owners, deadlines, decisions, blockers, and unresolved questions) with execution tracking and automated reminders.

---

## Technical Stack & Architecture

- **Backend**: Python 3.10+, Flask, SQLAlchemy ORM, Flask-Login, Flask-WTF
- **Database**: PostgreSQL (`postgresql://...`) with automatic fallback to SQLite (`sqlite:///solar.db`) if PostgreSQL port 5432 is unreachable.
- **AI Processing Pipeline**: Google Gemini (`GEMINI_API_KEY`) → OpenAI (`OPENAI_API_KEY`) → Heuristic Rule-Based Extractor (offline/fallback mode).
- **Transcription Service**: OpenAI Whisper API → Local SpeechRecognition → Raw Text Passthrough / Audio Parser.
- **Async Execution**: Python `threading.Thread` non-blocking background workers for upload processing.
- **Frontend**: Responsive HTML5, Vanilla JavaScript, Jinja2 templates, Glassmorphism dark aesthetic with Indigo/Violet accents.

---

## Features

1. **Authentication**: Register, login, logout with Werkzeug password hashing and session management.
2. **Executive Dashboard**: High-level metrics for Total Tasks, Completed, Pending, Overdue, and Blockers with upcoming 7-day deadlines.
3. **Meeting Upload & Non-blocking Async Processing**: Instantly uploads audio/video/text and polls background worker progress without blocking the client.
4. **Structured AI Extraction**: Strictly validates JSON output containing decisions, tasks with owners/deadlines/source quotes, blockers, unresolved questions, and key points.
5. **Execution Dashboard (`/tasks`)**: Filterable task execution view (`All`, `My Tasks`, `Pending`, `In Progress`, `Completed`, `Overdue`, `Blocked`, `Upcoming`) with inline status update dropdowns and inline editing.
6. **Blocker & Deadline Reminders**: Automatic background scheduler evaluating task deadlines and unresolved blockers, emitting in-app notification badges.

---

## Getting Started

### 1. Installation

```bash
# Clone the repository and install dependencies
pip install -r requirements.txt

# Copy environment variables configuration
cp .env.example .env
```

### 2. Configure Environment Variables (`.env`)

```ini
SECRET_KEY=dev-secret-key-solar-change-in-production
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/solar
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
MAX_CONTENT_LENGTH=52428800
UPLOAD_FOLDER=uploads/
```

### 3. Seed Database with Sample Data

Run the idempotent seed script to create demo user (`demo@solar.app` / `demo1234`), sample meetings, transcripts, decisions, blockers, and tasks:

```bash
python seed.py
```

### 4. Run Application

```bash
python run.py
```

Open your browser at `http://localhost:5000` and log in with:
- **Email**: `demo@solar.app`
- **Password**: `demo1234`

---

## Running Automated Tests

Run the full Pytest unit test suite covering authentication, task creation/status updates, overdue filters, and AI JSON schema validation:

```bash
pytest tests/ -v
```

---

## API & Route Documentation

| Route | Method | Description |
|-------|--------|-------------|
| `/login` | GET, POST | User authentication |
| `/register` | GET, POST | User registration |
| `/dashboard` | GET | Executive overview & metrics dashboard |
| `/meetings` | GET | Meeting history |
| `/meetings/new` | GET, POST | Upload meeting recording or transcript |
| `/meetings/<id>` | GET | Meeting details, transcript, and extracted tasks |
| `/meetings/<id>/status` | GET | JSON polling endpoint for background worker status |
| `/meetings/<id>/tasks` | POST | Manually add task to a meeting |
| `/tasks` | GET | Execution task dashboard with filter query params (`?filter=overdue`) |
| `/tasks/<id>/status` | POST | Update task status inline via AJAX |
| `/tasks/<id>` | PATCH, DELETE | Update task details or delete task |
| `/notifications` | GET | Notifications list |
| `/notifications/count` | GET | Unread notifications count JSON endpoint |
| `/notifications/<id>/read` | POST | Mark notification as read |
