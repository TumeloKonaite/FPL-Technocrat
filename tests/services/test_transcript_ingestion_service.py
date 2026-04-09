from __future__ import annotations

from src.services.transcript_ingestion_service import build_video_jobs_from_youtube


def test_build_video_jobs_from_youtube_skips_missing_error_and_irrelevant_videos(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.services.transcript_ingestion_service.get_latest_videos_for_all_experts",
        lambda limit_per_expert: [
            {
                "video_id": "keep-1",
                "title": "FPL GW32 Preview",
                "video_url": "https://youtube.com/watch?v=keep-1",
                "published_at": "2026-04-09T12:00:00Z",
                "expert_name": "FPL Harry",
            },
            {
                "video_id": "missing-1",
                "title": "FPL GW32 Team Reveal",
                "video_url": "https://youtube.com/watch?v=missing-1",
                "published_at": "2026-04-09T13:00:00Z",
                "expert_name": "FPL Focal",
            },
            {
                "video_id": "error-1",
                "title": "FPL GW32 Captaincy",
                "video_url": "https://youtube.com/watch?v=error-1",
                "published_at": "2026-04-09T14:00:00Z",
                "expert_name": "FPL Raptor",
            },
            {
                "video_id": "drop-1",
                "title": "EAFC 26 Career Mode",
                "video_url": "https://youtube.com/watch?v=drop-1",
                "published_at": "2026-04-09T15:00:00Z",
                "expert_name": "FPL Harry",
            },
        ],
    )

    monkeypatch.setattr(
        "src.services.transcript_ingestion_service.get_clean_transcript",
        lambda video_id: {
            "keep-1": {"video_id": "keep-1", "transcript": "FPL GW32 preview transcript", "status": "available"},
            "missing-1": {"video_id": "missing-1", "transcript": "", "status": "missing"},
            "error-1": {"video_id": "error-1", "transcript": "", "status": "error", "error": "provider down"},
            "drop-1": {"video_id": "drop-1", "transcript": "Career mode episode", "status": "available"},
        }[video_id],
    )

    jobs = build_video_jobs_from_youtube(gameweek=32, per_expert_limit=2)

    assert len(jobs) == 1
    assert jobs[0].expert_name == "FPL Harry"
    assert jobs[0].video_title == "FPL GW32 Preview"
    assert jobs[0].gameweek == 32
    assert jobs[0].transcript == "FPL GW32 preview transcript"
    assert jobs[0].video_url == "https://youtube.com/watch?v=keep-1"


def test_build_video_jobs_from_youtube_passes_per_expert_limit_to_discovery(monkeypatch) -> None:
    captured: dict[str, int] = {}

    def _fake_discovery(limit_per_expert: int) -> list[dict[str, str]]:
        captured["limit_per_expert"] = limit_per_expert
        return [
            {
                "video_id": "abc123",
                "title": "GW32 Best Picks",
                "video_url": "https://youtube.com/watch?v=abc123",
                "published_at": "2026-04-09T12:00:00Z",
                "expert_name": "FPL Harry",
            }
        ]

    monkeypatch.setattr(
        "src.services.transcript_ingestion_service.get_latest_videos_for_all_experts",
        _fake_discovery,
    )
    monkeypatch.setattr(
        "src.services.transcript_ingestion_service.get_clean_transcript",
        lambda video_id: {
            "video_id": video_id,
            "transcript": "Gameweek 32 captaincy preview",
            "status": "available",
        },
    )

    jobs = build_video_jobs_from_youtube(gameweek=32, per_expert_limit=4)

    assert captured == {"limit_per_expert": 4}
    assert len(jobs) == 1
    assert jobs[0].video_title == "GW32 Best Picks"
