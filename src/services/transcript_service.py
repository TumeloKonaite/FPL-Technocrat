from __future__ import annotations

from src.adapters.transcript_api import TranscriptFetchError, fetch_transcript
from src.utils.retry import RetryConfig, RetryError, retry_call
from src.utils.text_cleaning import clean_transcript


def get_clean_transcript(video_id: str) -> dict:
    try:
        raw_text = retry_call(
            lambda: fetch_transcript(video_id),
            retry_on=(TranscriptFetchError,),
            context=f"Transcript fetch for video '{video_id}'",
            config=RetryConfig(max_attempts=3, initial_delay_seconds=0.1),
        )
    except RetryError as exc:
        return {
            "video_id": video_id,
            "transcript": "",
            "status": "error",
            "error": str(exc),
        }

    if not raw_text:
        return {
            "video_id": video_id,
            "transcript": "",
            "status": "missing",
        }

    cleaned = clean_transcript(raw_text)

    return {
        "video_id": video_id,
        "transcript": cleaned,
        "status": "available",
    }
