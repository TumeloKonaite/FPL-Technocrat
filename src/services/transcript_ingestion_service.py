from __future__ import annotations

from src.adapters.youtube import get_latest_videos_for_all_experts
from src.schemas.video_job import VideoAnalysisJob
from src.services.transcript_service import get_clean_transcript
from src.services.video_selection_service import filter_relevant_videos


def build_video_jobs_from_youtube(
    *,
    gameweek: int,
    per_expert_limit: int = 2,
) -> list[VideoAnalysisJob]:
    discovered_videos = get_latest_videos_for_all_experts(limit_per_expert=per_expert_limit)

    transcript_candidates: list[dict[str, str]] = []
    for video in discovered_videos:
        video_id = video.get("video_id")
        if not isinstance(video_id, str) or not video_id:
            continue

        transcript_payload = get_clean_transcript(video_id)
        if transcript_payload.get("status") != "available":
            continue

        transcript_text = transcript_payload.get("transcript", "")
        if not isinstance(transcript_text, str) or not transcript_text.strip():
            continue

        transcript_candidates.append({**video, "transcript": transcript_text})

    relevant_videos = filter_relevant_videos(transcript_candidates, gameweek=gameweek)

    return [
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
