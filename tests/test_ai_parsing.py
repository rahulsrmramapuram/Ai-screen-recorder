from app.services.ai_service import validate_extraction_schema, heuristic_extract, _clean_and_parse_json

def test_valid_json_schema_validation():
    valid_data = {
        "decisions": ["Deploy to production on Friday"],
        "action_items": [
            {
                "title": "Setup Docker compose",
                "description": "Create production docker configuration",
                "owner": "Alex",
                "deadline": "2026-09-25",
                "source_quote": "Alex will set up docker compose by Friday."
            }
        ],
        "blockers": [
            {
                "description": "Waiting for SSL certificate approval",
                "owner": "Sarah"
            }
        ],
        "questions": ["Who will monitor latency?"],
        "key_points": ["Production environment requires PostgreSQL 15+"]
    }

    assert validate_extraction_schema(valid_data) is True


def test_malformed_json_parsing_and_fallback():
    malformed_raw = "Here is the response: ```json { 'decisions': ['invalid json quotes' ```"
    parsed = _clean_and_parse_json(malformed_raw)
    assert parsed is None or validate_extraction_schema(parsed) is False


def test_heuristic_extractor_detects_items():
    sample_transcript = (
        "Alex: We agreed to launch the MVP on Monday.\n"
        "Sarah: I will complete the UI integration and responsive styling by tomorrow.\n"
        "Michael: I am blocked on backend API development because I need the database schema before I can proceed.\n"
        "David: What is our staging URL?"
    )

    extracted = heuristic_extract(sample_transcript)

    assert len(extracted["decisions"]) >= 1
    assert "launch the MVP" in extracted["decisions"][0]

    assert len(extracted["action_items"]) >= 1
    assert any("UI integration" in item["title"] or "UI integration" in item["description"] for item in extracted["action_items"])

    assert len(extracted["blockers"]) >= 1
    assert any("blocked on backend" in b["description"] for b in extracted["blockers"])

    assert len(extracted["questions"]) >= 1
    assert "staging URL" in extracted["questions"][0]
