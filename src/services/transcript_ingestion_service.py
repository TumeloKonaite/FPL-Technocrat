from __future__ import annotations

from dataclasses import dataclass

from src.adapters.youtube import get_latest_videos_for_all_experts
from src.config.expert_sources import EXPERT_CHANNELS
from src.schemas.video_job import VideoAnalysisJob
from src.services.transcript_service import get_clean_transcript
from src.services.video_selection_service import filter_relevant_videos


@dataclass(slots=True)
class YouTubeIngestionResult:
    configured_experts: int
    discovered_videos: list[dict[str, str]]
    input_jobs: list[VideoAnalysisJob]
    transcript_failures: list[dict[str, str]]

    @property
    def videos_discovered(self) -> int:
        return len(self.discovered_videos)

    @property
    def videos_selected(self) -> int:
        return len(self.input_jobs)

    @property
    def jobs_created(self) -> int:
        return len(self.input_jobs)


def ingest_youtube_video_jobs(
    *,
    gameweek: int,
    per_expert_limit: int = 2,
) -> YouTubeIngestionResult:
    discovered_videos = get_latest_videos_for_all_experts(limit_per_expert=per_expert_limit)

    transcript_candidates: list[dict[str, str]] = []
    transcript_failures: list[dict[str, str]] = []
    for video in discovered_videos:
        video_id = video.get("video_id")
        if not isinstance(video_id, str) or not video_id:
            transcript_failures.append(
                {
                    "expert_name": str(video.get("expert_name", "")),
                    "video_title": str(video.get("title", "")),
                    "video_url": str(video.get("video_url", "")),
                    "video_id": "",
                    "error": "missing video id",
                    "status": "invalid",
                }
            )
            continue

        transcript_payload = get_clean_transcript(video_id)
        if transcript_payload.get("status") != "available":
            transcript_failures.append(
                {
                    "expert_name": str(video.get("expert_name", "")),
                    "video_title": str(video.get("title", "")),
                    "video_url": str(video.get("video_url", "")),
                    "video_id": video_id,
                    "error": str(transcript_payload.get("error", transcript_payload.get("status", "unavailable"))),
                    "status": str(transcript_payload.get("status", "unavailable")),
                }
            )
            continue

        transcript_text = transcript_payload.get("transcript", "")
        if not isinstance(transcript_text, str) or not transcript_text.strip():
            transcript_failures.append(
                {
                    "expert_name": str(video.get("expert_name", "")),
                    "video_title": str(video.get("title", "")),
                    "video_url": str(video.get("video_url", "")),
                    "video_id": video_id,
                    "error": "empty transcript",
                    "status": "empty",
                }
            )
            continue

        transcript_candidates.append({**video, "transcript": transcript_text})

    relevant_videos = filter_relevant_videos(transcript_candidates, gameweek=gameweek)

    input_jobs = [
        VideoAnalysisJob(
            expert_name=video["expert_name"],
            video_title=video["title"],
            published_at=video["published_at"],
            gameweek=gameweek,
            transcript=video["transcript"],
            video_url=video.get("video_url"),
        )
        for video in relevant_videos
    ]

    return YouTubeIngestionResult(
        configured_experts=len(EXPERT_CHANNELS),
        discovered_videos=discovered_videos,
        input_jobs=input_jobs,
        transcript_failures=transcript_failures,
    )


def build_video_jobs_from_youtube(
    *,
    gameweek: int,
    per_expert_limit: int = 2,
) -> list[VideoAnalysisJob]:
    return ingest_youtube_video_jobs(
        gameweek=gameweek,
        per_expert_limit=per_expert_limit,
    ).input_jobs
