from __future__ import annotations

from src.adapters.transcript_api import WebshareProxySettings
from src.services.transcript_ingestion_service import build_video_jobs_from_youtube, ingest_youtube_video_jobs


def test_build_video_jobs_from_youtube_skips_missing_error_and_irrelevant_videos(monkeypatch) -> None:
    fixtures = {
        "FPL Harry": [
            {
                "video_id": "keep-1",
                "title": "FPL GW32 Preview",
                "video_url": "https://youtube.com/watch?v=keep-1",
                "published_at": "2026-04-09T12:00:00Z",
                "expert_name": "FPL Harry",
            },
            {
                "video_id": "drop-1",
                "title": "EAFC 26 Career Mode",
                "video_url": "https://youtube.com/watch?v=drop-1",
                "published_at": "2026-04-09T15:00:00Z",
                "expert_name": "FPL Harry",
            },
        ],
        "FPL Focal": [
            {
                "video_id": "missing-1",
                "title": "FPL GW32 Team Reveal",
                "video_url": "https://youtube.com/watch?v=missing-1",
                "published_at": "2026-04-09T13:00:00Z",
                "expert_name": "FPL Focal",
            }
        ],
        "FPL Raptor": [
            {
                "video_id": "error-1",
                "title": "FPL GW32 Captaincy",
                "video_url": "https://youtube.com/watch?v=error-1",
                "published_at": "2026-04-09T14:00:00Z",
                "expert_name": "FPL Raptor",
            }
        ],
    }
    monkeypatch.setattr(
        "src.services.transcript_ingestion_service.get_latest_videos_for_expert",
        lambda expert_name, channel_url, limit: fixtures.get(expert_name, [])[:limit],
    )

    monkeypatch.setattr(
        "src.services.transcript_ingestion_service.get_clean_transcript",
        lambda video_id, *, proxy_settings=None: {
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


def test_ingest_youtube_video_jobs_returns_discovery_and_failure_metadata(monkeypatch) -> None:
    fixtures = {
        "FPL Harry": [
            {
                "video_id": "keep-1",
                "title": "FPL GW32 Preview",
                "video_url": "https://youtube.com/watch?v=keep-1",
                "published_at": "2026-04-09T12:00:00Z",
                "expert_name": "FPL Harry",
            }
        ],
        "FPL Focal": [
            {
                "video_id": "missing-1",
                "title": "FPL GW32 Team Reveal",
                "video_url": "https://youtube.com/watch?v=missing-1",
                "published_at": "2026-04-09T13:00:00Z",
                "expert_name": "FPL Focal",
            }
        ],
    }
    monkeypatch.setattr(
        "src.services.transcript_ingestion_service.get_latest_videos_for_expert",
        lambda expert_name, channel_url, limit: fixtures.get(expert_name, [])[:limit],
    )
    monkeypatch.setattr(
        "src.services.transcript_ingestion_service.get_clean_transcript",
        lambda video_id, *, proxy_settings=None: {
            "keep-1": {"video_id": "keep-1", "transcript": "FPL GW32 preview transcript", "status": "available"},
            "missing-1": {"video_id": "missing-1", "transcript": "", "status": "missing"},
        }[video_id],
    )

    result = ingest_youtube_video_jobs(gameweek=32, per_expert_limit=2)

    assert result.videos_discovered == 2
    assert result.videos_selected == 1
    assert result.jobs_created == 1
    assert len(result.input_jobs) == 1
    assert len(result.discovered_videos) == 2
    assert result.transcript_failures == [
        {
            "expert_name": "FPL Focal",
            "video_title": "FPL GW32 Team Reveal",
            "video_url": "https://youtube.com/watch?v=missing-1",
            "video_id": "missing-1",
            "error": "missing",
            "status": "missing",
        }
    ]


def test_build_video_jobs_from_youtube_passes_per_expert_limit_to_discovery(monkeypatch) -> None:
    captured: dict[str, str | int] = {}

    def _fake_discovery(expert_name: str, channel_url: str, limit: int) -> list[dict[str, str]]:
        captured["expert_name"] = expert_name
        captured["channel_url"] = channel_url
        captured["limit_per_expert"] = limit
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
        "src.services.transcript_ingestion_service.get_latest_videos_for_expert",
        _fake_discovery,
    )
    monkeypatch.setattr(
        "src.services.transcript_ingestion_service.get_clean_transcript",
        lambda video_id, *, proxy_settings=None: {
            "video_id": video_id,
            "transcript": "Gameweek 32 captaincy preview",
            "status": "available",
        },
    )

    jobs = build_video_jobs_from_youtube(
        gameweek=32,
        per_expert_limit=4,
        expert_name="FPL Harry",
        expert_count=1,
    )

    assert captured == {
        "expert_name": "FPL Harry",
        "channel_url": "https://www.youtube.com/@FPLHarry/videos",
        "limit_per_expert": 4,
    }
    assert len(jobs) == 1
    assert jobs[0].video_title == "GW32 Best Picks"


def test_ingest_youtube_video_jobs_passes_proxy_settings_to_transcript_fetch(monkeypatch) -> None:
    proxy_settings = WebshareProxySettings(
        enabled=True,
        proxy_username="proxy-user",
        proxy_password="proxy-pass",
    )
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "src.services.transcript_ingestion_service.get_latest_videos_for_expert",
        lambda expert_name, channel_url, limit: [
            {
                "video_id": "keep-1",
                "title": "FPL GW32 Preview",
                "video_url": "https://youtube.com/watch?v=keep-1",
                "published_at": "2026-04-09T12:00:00Z",
                "expert_name": expert_name,
            }
        ],
    )

    def _fake_get_clean_transcript(video_id: str, *, proxy_settings=None) -> dict[str, str]:
        captured["video_id"] = video_id
        captured["proxy_settings"] = proxy_settings
        return {
            "video_id": video_id,
            "transcript": "FPL GW32 preview transcript",
            "status": "available",
        }

    monkeypatch.setattr(
        "src.services.transcript_ingestion_service.get_clean_transcript",
        _fake_get_clean_transcript,
    )

    result = ingest_youtube_video_jobs(
        gameweek=32,
        per_expert_limit=1,
        expert_name="FPL Harry",
        expert_count=1,
        proxy_settings=proxy_settings,
    )

    assert len(result.input_jobs) == 1
    assert captured == {
        "video_id": "keep-1",
        "proxy_settings": proxy_settings,
    }
