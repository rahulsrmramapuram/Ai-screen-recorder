import json
import re
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a meeting analysis AI. Extract structured data from this transcript.\n"
    "Return ONLY valid JSON. No markdown. No explanation. No code blocks.\n"
    'Schema: { "decisions": [str], "action_items": [{"title": str, "description": str, "owner": str, "deadline": str|null, "source_quote": str}], "blockers": [{"description": str, "owner": str}], "questions": [str], "key_points": [str] }'
)


def extract_meeting_insights(transcript: str, gemini_api_key: str = "", openai_api_key: str = "") -> dict:
    """
    Structured AI Extraction Pipeline:
    1. Try Google Gemini API (if key present)
    2. Try OpenAI API (if key present)
    3. Fallback to Heuristic Extractor
    """
    if not transcript or not transcript.strip():
        return empty_extraction()

    # 1. Google Gemini API
    if gemini_api_key:
        result = _try_gemini_extraction(transcript, gemini_api_key)
        if result:
            return result

    # 2. OpenAI API
    if openai_api_key:
        result = _try_openai_extraction(transcript, openai_api_key)
        if result:
            return result

    # 3. Fallback Heuristic Extractor
    print("[AI Service] LLM keys unavailable or extraction failed. Running heuristic rule-based extractor.")
    return heuristic_extract(transcript)


def _try_gemini_extraction(transcript: str, api_key: str) -> dict:
    for attempt in range(1, 4):
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"{SYSTEM_PROMPT}\n\nTranscript:\n{transcript}"
            )
            raw_text = response.text if response and hasattr(response, 'text') else ""
            parsed = _clean_and_parse_json(raw_text)
            if parsed and validate_extraction_schema(parsed):
                return parsed
            else:
                logger.warning(f"Gemini attempt {attempt} failed JSON validation. Raw response: {raw_text[:200]}")
        except Exception as e:
            logger.error(f"Gemini API attempt {attempt} error: {e}")
    return None


def _try_openai_extraction(transcript: str, api_key: str) -> dict:
    for attempt in range(1, 4):
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": transcript}
                ],
                temperature=0.1
            )
            raw_text = response.choices[0].message.content if response.choices else ""
            parsed = _clean_and_parse_json(raw_text)
            if parsed and validate_extraction_schema(parsed):
                return parsed
            else:
                logger.warning(f"OpenAI attempt {attempt} failed JSON validation. Raw response: {raw_text[:200]}")
        except Exception as e:
            logger.error(f"OpenAI API attempt {attempt} error: {e}")
    return None


def _clean_and_parse_json(text: str) -> dict:
    if not text:
        return None
    # Strip markdown code blocks ```json ... ```
    cleaned = re.sub(r'```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'```', '', cleaned).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        # Match JSON object pattern
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    return None


def validate_extraction_schema(data: dict) -> bool:
    if not isinstance(data, dict):
        return False
    required_keys = ["decisions", "action_items", "blockers", "questions", "key_points"]
    for key in required_keys:
        if key not in data or not isinstance(data[key], list):
            return False
    return True


def empty_extraction() -> dict:
    return {
        "decisions": [],
        "action_items": [],
        "blockers": [],
        "questions": [],
        "key_points": []
    }


def heuristic_extract(transcript: str) -> dict:
    """
    Rule-based fallback parser using pattern matching & regex.
    Detects:
    - Action items: sentences containing "will", "should", "must", "need to", "going to", "by [date]"
    - Blockers: phrases containing "blocked", "waiting for", "can't proceed", "need X before"
    - Decisions: sentences containing "decided", "agreed", "confirmed", "we will"
    """
    decisions = []
    action_items = []
    blockers = []
    questions = []
    key_points = []

    # Split lines / sentences
    lines = [line.strip() for line in transcript.split('\n') if line.strip()]

    action_triggers = [r'\bwill\b', r'\bshould\b', r'\bmust\b', r'\bneed to\b', r'\bgoing to\b', r'\bby\b\s+\w+']
    blocker_triggers = [r'\bblocked\b', r'\bwaiting for\b', r'\bcan\'t proceed\b', r'\bneed\b\s+.*\s+\bbefore\b']
    decision_triggers = [r'\bdecided\b', r'\bagreed\b', r'\bconfirmed\b', r'\bwe will\b']

    for line in lines:
        line_clean = line.strip()
        speaker = None
        content = line_clean

        # Check speaker format "Name: content"
        if ':' in line_clean and not line_clean.startswith('http'):
            parts = line_clean.split(':', 1)
            if len(parts[0].strip().split()) <= 3:
                speaker = parts[0].strip()
                content = parts[1].strip()

        # Check decisions
        if any(re.search(pat, content, re.IGNORECASE) for pat in decision_triggers):
            decisions.append(content)
            continue

        # Check blockers
        if any(re.search(pat, content, re.IGNORECASE) for pat in blocker_triggers):
            blockers.append({
                "description": content,
                "owner": speaker or "Team"
            })
            continue

        # Check action items
        if any(re.search(pat, content, re.IGNORECASE) for pat in action_triggers):
            # Parse deadline from text if present
            deadline_str = extract_deadline_heuristic(content)
            
            action_items.append({
                "title": content[:100],
                "description": content,
                "owner": speaker or extract_owner_heuristic(content),
                "deadline": deadline_str,
                "source_quote": line_clean
            })
            continue

        # Check questions
        if content.endswith('?'):
            questions.append(content)
            continue

        # General key points
        if len(content) > 15:
            key_points.append(content)

    return {
        "decisions": list(dict.fromkeys(decisions)),
        "action_items": action_items,
        "blockers": blockers,
        "questions": questions[:5],
        "key_points": key_points[:5]
    }


def extract_owner_heuristic(text: str) -> str:
    # Match names or pronouns
    match = re.search(r'([A-Z][a-z]+)\s+(?:will|should|must|is going to|needs to)', text)
    if match:
        return match.group(1)
    return "Unassigned"


def extract_deadline_heuristic(text: str) -> str:
    # Match dates or days e.g. "by May 25", "by tomorrow", "by Friday"
    now = datetime.now(timezone.utc)
    match_by = re.search(r'by\s+(tomorrow|next week|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\w+\s+\d{1,2})', text, re.IGNORECASE)
    if match_by:
        target = match_by.group(1).lower()
        if target == 'tomorrow':
            return (now + timedelta(days=1)).strftime("%Y-%m-%d")
        elif target == 'next week':
            return (now + timedelta(days=7)).strftime("%Y-%m-%d")
        else:
            return (now + timedelta(days=3)).strftime("%Y-%m-%d")
    return None
