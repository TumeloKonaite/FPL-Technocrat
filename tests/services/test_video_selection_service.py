from __future__ import annotations

from src.services.video_selection_service import filter_relevant_videos, is_relevant_video


def test_is_relevant_video_accepts_matching_gameweek_reference() -> None:
    assert is_relevant_video(
        gameweek=32,
        title="FPL GW32 Deadline Stream",
        transcript="",
    )


def test_is_relevant_video_accepts_fpl_context_from_transcript() -> None:
    assert is_relevant_video(
        gameweek=32,
        title="My latest thoughts",
        transcript="This FPL preview covers captaincy and transfer plans for the week.",
    )


def test_is_relevant_video_rejects_irrelevant_upload() -> None:
    assert not is_relevant_video(
        gameweek=32,
        title="EAFC 26 Career Mode Reaction",
        transcript="A fun stream highlights package.",
    )


def test_filter_relevant_videos_keeps_only_relevant_candidates() -> None:
    selected = filter_relevant_videos(
        [
            {"video_id": "keep-1", "title": "GW32 Best Picks", "transcript": ""},
            {"video_id": "drop-1", "title": "Weekend vlog", "transcript": ""},
            {"video_id": "keep-2", "title": "Q&A", "transcript": "FPL wildcard draft and captaincy preview."},
        ],
        gameweek=32,
    )

    assert [item["video_id"] for item in selected] == ["keep-1", "keep-2"]
