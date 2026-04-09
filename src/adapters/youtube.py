from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class YouTubeTranscriptFetchError(RuntimeError):
    """Raised when the YouTube transcript provider cannot return a transcript."""


def _build_video_url(video_id: str, entry: dict[str, Any]) -> str:
    webpage_url = entry.get("webpage_url")
    if isinstance(webpage_url, str) and webpage_url:
        return webpage_url

    url = entry.get("url")
    if isinstance(url, str) and url.startswith("http"):
        return url

    return f"https://www.youtube.com/watch?v={video_id}"


def _normalize_published_at(entry: dict[str, Any]) -> str:
    timestamp = entry.get("timestamp") or entry.get("release_timestamp")
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    upload_date = entry.get("upload_date")
    if isinstance(upload_date, str):
        try:
            return datetime.strptime(upload_date, "%Y%m%d").strftime("%Y-%m-%dT00:00:00Z")
        except ValueError:
            return ""

    return ""


def _normalize_video_entry(entry: dict[str, Any], expert_name: str) -> dict[str, str] | None:
    video_id = entry.get("id")
    title = entry.get("title")
    if not isinstance(video_id, str) or not video_id:
        return None
    if not isinstance(title, str) or not title.strip():
        return None

    return {
        "video_id": video_id,
        "title": title.strip(),
        "video_url": _build_video_url(video_id, entry),
        "published_at": _normalize_published_at(entry),
        "expert_name": expert_name,
    }


def _extract_channel_entries(channel_url: str, limit: int) -> list[dict[str, Any]]:
    from yt_dlp import YoutubeDL

    ydl_opts = {
        "extract_flat": True,
        "ignoreerrors": True,
        "playlistend": limit,
        "quiet": True,
        "skip_download": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)

    if not isinstance(info, dict):
        return []

    entries = info.get("entries")
    if not isinstance(entries, list):
        return []

    return [entry for entry in entries if isinstance(entry, dict)]


def get_latest_videos_for_expert(
    expert_name: str,
    channel_url: str,
    limit: int = 3,
) -> list[dict[str, str]]:
    if limit <= 0:
        return []

    entries = _extract_channel_entries(channel_url, limit)
    videos: list[dict[str, str]] = []
    for entry in entries:
        normalized = _normalize_video_entry(entry, expert_name)
        if normalized is not None:
            videos.append(normalized)

    return videos[:limit]


def get_latest_videos_for_all_experts(limit_per_expert: int = 3) -> list[dict[str, str]]:
    from src.config.expert_sources import EXPERT_CHANNELS

    videos: list[dict[str, str]] = []
    for expert in EXPERT_CHANNELS:
        expert_name = expert.get("name")
        channel_url = expert.get("url")
        if not isinstance(expert_name, str) or not isinstance(channel_url, str):
            continue
        videos.extend(
            get_latest_videos_for_expert(
                expert_name=expert_name,
                channel_url=channel_url,
                limit=limit_per_expert,
            )
        )

    return videos


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

    except Exception as exc:
        raise YouTubeTranscriptFetchError(
            f"Could not fetch YouTube transcript for video '{video_id}': {exc}"
        ) from exc
