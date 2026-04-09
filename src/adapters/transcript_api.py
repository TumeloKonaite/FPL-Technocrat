from __future__ import annotations


class TranscriptFetchError(RuntimeError):
    """Raised when transcript retrieval fails."""


def fetch_transcript(video_id: str) -> str:
    """Fetch a raw transcript string from the configured transcript source."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        transcript = YouTubeTranscriptApi().fetch(video_id)
        combined_transcript = " ".join(
            " ".join(snippet.text.split())
            for snippet in transcript.snippets
        )
        return combined_transcript.strip()
    except Exception as exc:
        raise TranscriptFetchError(
            f"Could not fetch transcript for video '{video_id}': {exc}"
        ) from exc
