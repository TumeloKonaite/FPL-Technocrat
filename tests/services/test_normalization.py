from __future__ import annotations

from src.schemas.video_job import VideoAnalysisJob
from src.services.normalization import (
    build_video_job_identity,
    canonical_player_display,
    normalize_player_reference,
)


def test_player_normalization_handles_case_spacing_and_aliases() -> None:
    assert canonical_player_display("  saka ") == "Bukayo Saka"
    assert canonical_player_display("Mo Salah") == "Mohamed Salah"
    assert canonical_player_display("mohamed salah") == "Mohamed Salah"


def test_player_normalization_handles_unicode_apostrophes_and_noise() -> None:
    normalized = normalize_player_reference("  MO SALAH’S  ")

    assert normalized.raw_name == "  MO SALAH’S  "
    assert normalized.normalized_name == "mohamed salah"


def test_player_normalization_keeps_unknown_short_names_conservative() -> None:
    assert normalize_player_reference("Luis").normalized_name == "luis"


def test_video_job_identity_prefers_video_url_and_canonicalizes_it() -> None:
    first = VideoAnalysisJob(
        expert_name="Expert A",
        video_title="GW32 Preview",
        published_at="2026-04-09T12:00:00Z",
        gameweek=32,
        transcript="Transcript A",
        video_url="https://www.youtube.com/watch?v=AbC123xyZ&t=95",
    )
    second = first.model_copy(
        update={"expert_name": "Expert B", "video_url": "https://youtu.be/AbC123xyZ"}
    )

    assert build_video_job_identity(first) == build_video_job_identity(second)
