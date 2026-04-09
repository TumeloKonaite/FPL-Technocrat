from __future__ import annotations

from src.adapters.youtube import YouTubeTranscriptFetchError, fetch_youtube_transcript


class TranscriptFetchError(RuntimeError):
    """Raised when transcript retrieval fails."""


def fetch_transcript(video_id: str) -> str:
    """Fetch a raw transcript string from the configured transcript source."""
    try:
        return fetch_youtube_transcript(video_id)
    except YouTubeTranscriptFetchError as exc:
        raise TranscriptFetchError(str(exc)) from exc
