from __future__ import annotations

from src.adapters.youtube import (
    get_latest_videos_for_all_experts,
    get_latest_videos_for_expert,
)


class _FakeYoutubeDL:
    response: dict | None = None

    def __init__(self, options: dict) -> None:
        self.options = options

    def __enter__(self) -> "_FakeYoutubeDL":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def extract_info(self, url: str, download: bool = False) -> dict | None:
        assert download is False
        return self.response


def test_get_latest_videos_for_expert_returns_normalized_structure(monkeypatch) -> None:
    _FakeYoutubeDL.response = {
        "entries": [
            {
                "id": "abc123",
                "title": " GW33 Best Picks ",
                "webpage_url": "https://www.youtube.com/watch?v=abc123",
                "timestamp": 1775736000,
            }
        ]
    }
    monkeypatch.setattr("yt_dlp.YoutubeDL", _FakeYoutubeDL)

    videos = get_latest_videos_for_expert(
        expert_name="FPL Harry",
        channel_url="https://www.youtube.com/@FPLHarry",
        limit=3,
    )

    assert videos == [
        {
            "video_id": "abc123",
            "title": "GW33 Best Picks",
            "video_url": "https://www.youtube.com/watch?v=abc123",
            "published_at": "2026-04-09T12:00:00Z",
            "expert_name": "FPL Harry",
        }
    ]


def test_get_latest_videos_for_expert_handles_empty_results(monkeypatch) -> None:
    _FakeYoutubeDL.response = {"entries": []}
    monkeypatch.setattr("yt_dlp.YoutubeDL", _FakeYoutubeDL)

    videos = get_latest_videos_for_expert(
        expert_name="FPL Harry",
        channel_url="https://www.youtube.com/@FPLHarry",
    )

    assert videos == []


def test_get_latest_videos_for_expert_skips_malformed_entries(monkeypatch) -> None:
    _FakeYoutubeDL.response = {
        "entries": [
            {"title": "Missing id"},
            {"id": "abc123"},
            {"id": "xyz999", "title": "Preview", "upload_date": "20260407"},
        ]
    }
    monkeypatch.setattr("yt_dlp.YoutubeDL", _FakeYoutubeDL)

    videos = get_latest_videos_for_expert(
        expert_name="FPL Focal",
        channel_url="https://www.youtube.com/@FPLFocal",
    )

    assert videos == [
        {
            "video_id": "xyz999",
            "title": "Preview",
            "video_url": "https://www.youtube.com/watch?v=xyz999",
            "published_at": "2026-04-07T00:00:00Z",
            "expert_name": "FPL Focal",
        }
    ]


def test_get_latest_videos_for_all_experts_uses_configured_sources(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.adapters.youtube.get_latest_videos_for_expert",
        lambda expert_name, channel_url, limit: [
            {
                "video_id": f"{expert_name.lower().replace(' ', '-')}-1",
                "title": f"{expert_name} latest",
                "video_url": f"{channel_url}/videos",
                "published_at": "2026-04-09T00:00:00Z",
                "expert_name": expert_name,
            }
        ],
    )

    videos = get_latest_videos_for_all_experts(limit_per_expert=1)

    assert [video["expert_name"] for video in videos] == [
        "FPL Harry",
        "Let's Talk FPL",
        "FPL Focal",
        "FPL Raptor",
        "The FPL Wire",
    ]
