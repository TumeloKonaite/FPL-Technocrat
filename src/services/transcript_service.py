from src.adapters.transcript_api import fetch_transcript
from src.utils.text_cleaning import clean_transcript


def get_clean_transcript(video_id: str) -> dict:
    raw_text = fetch_transcript(video_id)

    if not raw_text:
        return {
            "video_id": video_id,
            "transcript": "",
            "status": "missing"
        }

    cleaned = clean_transcript(raw_text)

    return {
        "video_id": video_id,
        "transcript": cleaned,
        "status": "available"
    }
