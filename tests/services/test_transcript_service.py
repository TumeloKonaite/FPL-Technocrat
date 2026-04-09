from pathlib import Path

from src.services.transcript_service import get_clean_transcript
from src.utils.text_cleaning import clean_transcript


def test_clean_transcript_normalizes_whitespace() -> None:
    raw_text = "  Hello   world\n\nthis\t is   a test  "

    assert clean_transcript(raw_text) == "Hello world this is a test"


def test_get_clean_transcript_returns_available_payload(monkeypatch) -> None:
    fixture_path = Path("tests/fixtures/sample_transcript_1.txt")
    raw_text = fixture_path.read_text(encoding="utf-8")

    monkeypatch.setattr(
        "src.services.transcript_service.fetch_transcript",
        lambda video_id: raw_text,
    )

    payload = get_clean_transcript("abc123")

    assert payload == {
        "video_id": "abc123",
        "transcript": "Hello and welcome to the FPL roundup for gameweek 12.",
        "status": "available",
    }


def test_get_clean_transcript_returns_missing_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.services.transcript_service.fetch_transcript",
        lambda video_id: "",
    )

    payload = get_clean_transcript("missing-video")

    assert payload == {
        "video_id": "missing-video",
        "transcript": "",
        "status": "missing",
    }
