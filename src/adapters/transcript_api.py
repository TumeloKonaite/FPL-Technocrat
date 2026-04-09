from src.adapters.youtube import fetch_youtube_transcript


def fetch_transcript(video_id: str) -> str:
    """Fetch a raw transcript string from the configured transcript source."""
    return fetch_youtube_transcript(video_id)
