from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.services.expert_analysis_service import (
    _build_analysis_prompt,
    analyze_video_job,
    analyze_video_jobs,
)
from src.schemas.expert_analysis import ExpertVideoAnalysis
from src.schemas.video_job import VideoAnalysisJob


@pytest.fixture
def sample_job() -> VideoAnalysisJob:
    return VideoAnalysisJob(
        expert_name="FPL Harry",
        video_title="GW5 Best Transfers",
        published_at="2026-08-15T10:00:00Z",
        gameweek=5,
        transcript="""
        This week I really like Salah and Saka.
        I think Haaland remains a strong captain option.
        I would avoid taking unnecessary hits for defenders.
        If you still have your wildcard, you could consider holding for later.
        """.strip(),
    )


@pytest.fixture
def short_job() -> VideoAnalysisJob:
    return VideoAnalysisJob(
        expert_name="FPL General",
        video_title="Quick Thoughts",
        published_at="2026-08-16T10:00:00Z",
        gameweek=5,
        transcript="Good picks this week.",
    )


def test_build_analysis_prompt(sample_job: VideoAnalysisJob) -> None:
    prompt = _build_analysis_prompt(sample_job)

    assert "Expert: FPL Harry" in prompt
    assert "Video title: GW5 Best Transfers" in prompt
    assert "Gameweek: 5" in prompt
    assert "Transcript:" in prompt
    assert "Salah and Saka" in prompt


def test_analyze_video_job_returns_mocked_agent_output(sample_job: VideoAnalysisJob) -> None:
    mocked_output = ExpertVideoAnalysis(
        expert_name="FPL Harry",
        video_title="GW5 Best Transfers",
        gameweek=5,
        summary="Strong midfield picks and Haaland captaincy support.",
        key_takeaways=["Buy Salah", "Buy Saka"],
        recommended_players=["Mohamed Salah", "Bukayo Saka"],
        avoid_players=["Low-upside defenders"],
        captaincy_picks=["Erling Haaland"],
        chip_strategy=None,
        reasoning=["Form", "Captaincy reliability"],
        confidence="high",
    )

    mocked_result = SimpleNamespace(final_output=mocked_output)

    with patch("src.services.expert_analysis_service.Runner.run", new=AsyncMock(return_value=mocked_result)):
        result = asyncio.run(analyze_video_job(sample_job))

    assert isinstance(result, ExpertVideoAnalysis)
    assert result.expert_name == "FPL Harry"
    assert "Mohamed Salah" in result.recommended_players
    assert result.confidence == "high"


def test_analyze_video_job_handles_short_transcript(short_job: VideoAnalysisJob) -> None:
    result = asyncio.run(analyze_video_job(short_job))

    assert isinstance(result, ExpertVideoAnalysis)
    assert result.expert_name == "FPL General"
    assert result.video_title == "Quick Thoughts"
    assert result.gameweek == 5
    assert result.confidence == "low"
    assert result.recommended_players == []
    assert "too short" in result.summary.lower()


def test_analyze_video_jobs_runs_multiple_jobs(sample_job: VideoAnalysisJob) -> None:
    second_job = VideoAnalysisJob(
        expert_name="Let’s Talk FPL",
        video_title="GW5 Captaincy",
        published_at="2026-08-17T10:00:00Z",
        gameweek=5,
        transcript="""
        Palmer is a strong option.
        Haaland is still the safest captain.
        Watkins is a decent differential.
        """.strip(),
    )

    mocked_output_1 = ExpertVideoAnalysis(
        expert_name="FPL Harry",
        video_title="GW5 Best Transfers",
        gameweek=5,
        summary="Mock summary 1",
        key_takeaways=["Takeaway 1"],
        recommended_players=["Mohamed Salah"],
        avoid_players=[],
        captaincy_picks=["Erling Haaland"],
        chip_strategy=None,
        reasoning=["Reason 1"],
        confidence="high",
    )

    mocked_output_2 = ExpertVideoAnalysis(
        expert_name="Let’s Talk FPL",
        video_title="GW5 Captaincy",
        gameweek=5,
        summary="Mock summary 2",
        key_takeaways=["Takeaway 2"],
        recommended_players=["Cole Palmer", "Ollie Watkins"],
        avoid_players=[],
        captaincy_picks=["Erling Haaland"],
        chip_strategy=None,
        reasoning=["Reason 2"],
        confidence="medium",
    )

    mocked_results = [
        SimpleNamespace(final_output=mocked_output_1),
        SimpleNamespace(final_output=mocked_output_2),
    ]

    with patch(
        "src.services.expert_analysis_service.Runner.run",
        new=AsyncMock(side_effect=mocked_results),
    ):
        results = asyncio.run(analyze_video_jobs([sample_job, second_job]))

    assert len(results) == 2
    assert all(isinstance(item, ExpertVideoAnalysis) for item in results)
    assert results[0].expert_name == "FPL Harry"
    assert results[1].expert_name == "Let’s Talk FPL"
