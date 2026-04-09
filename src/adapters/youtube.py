def fetch_youtube_transcript(video_id: str) -> str:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)

        combined_transcript = " ".join(
            " ".join(snippet.text.split())
            for snippet in transcript.snippets
        )

        return combined_transcript.strip()

    except Exception:
        return ""
