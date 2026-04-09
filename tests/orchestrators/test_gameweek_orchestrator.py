from __future__ import annotations

import asyncio
import time
from unittest.mock import patch

from src.orchestrators.gameweek_orchestrator import run_gameweek_orchestration
from src.schemas.expert_analysis import ExpertVideoAnalysis
from src.schemas.video_job import VideoAnalysisJob


def _build_job(expert_name: str, video_title: str) -> VideoAnalysisJob:
    return VideoAnalysisJob(
        expert_name=expert_name,
        video_title=video_title,
        published_at="2026-08-15T10:00:00Z",
        gameweek=5,
        transcript="A long enough transcript for orchestration testing.",
        video_url=f"https://youtube.com/watch?v={expert_name.lower().replace(' ', '-')}",
    )


def _build_analysis(job: VideoAnalysisJob) -> ExpertVideoAnalysis:
    return ExpertVideoAnalysis(
        expert_name=job.expert_name,
        video_title=job.video_title,
        gameweek=job.gameweek,
        summary=f"Summary for {job.expert_name}",
        key_takeaways=[f"Takeaway for {job.expert_name}"],
        recommended_players=["Mohamed Salah"],
        avoid_players=[],
        captaincy_picks=["Erling Haaland"],
        chip_strategy=None,
        reasoning=["Form"],
        confidence="high",
    )


def test_run_gameweek_orchestration_runs_jobs_in_parallel() -> None:
    jobs = [
        _build_job("FPL Harry", "GW5 Best Transfers"),
        _build_job("FPL General", "GW5 Captaincy"),
        _build_job("Let us Talk FPL", "GW5 Differentials"),
    ]

    async def fake_analyze(job: VideoAnalysisJob) -> ExpertVideoAnalysis:
        await asyncio.sleep(0.05)
        return _build_analysis(job)

    with patch(
        "src.orchestrators.gameweek_orchestrator.analyze_video_job",
        side_effect=fake_analyze,
    ):
        started_at = time.perf_counter()
        result = asyncio.run(run_gameweek_orchestration(jobs))
        elapsed = time.perf_counter() - started_at

    assert elapsed < 0.12
    assert len(result.results) == 3
    assert all(item.success for item in result.results)
    assert [item.job.expert_name for item in result.results] == [
        "FPL Harry",
        "FPL General",
        "Let us Talk FPL",
    ]


def test_run_gameweek_orchestration_preserves_order_and_identity() -> None:
    jobs = [
        _build_job("FPL Harry", "Video A"),
        _build_job("FPL General", "Video B"),
    ]

    async def fake_analyze(job: VideoAnalysisJob) -> ExpertVideoAnalysis:
        if job.expert_name == "FPL Harry":
            await asyncio.sleep(0.03)
        else:
            await asyncio.sleep(0.01)
        return _build_analysis(job)

    with patch(
        "src.orchestrators.gameweek_orchestrator.analyze_video_job",
        side_effect=fake_analyze,
    ):
        result = asyncio.run(run_gameweek_orchestration(jobs))

    assert [item.job.video_title for item in result.results] == ["Video A", "Video B"]
    assert result.results[0].analysis is not None
    assert result.results[0].analysis.expert_name == "FPL Harry"
    assert result.results[1].analysis is not None
    assert result.results[1].analysis.expert_name == "FPL General"


def test_run_gameweek_orchestration_captures_mixed_success_and_failure() -> None:
    jobs = [
        _build_job("FPL Harry", "Video A"),
        _build_job("FPL General", "Video B"),
        _build_job("Andy", "Video C"),
    ]

    async def fake_analyze(job: VideoAnalysisJob) -> ExpertVideoAnalysis:
        if job.expert_name == "FPL General":
            raise RuntimeError("Transcript fetch failed")
        return _build_analysis(job)

    with patch(
        "src.orchestrators.gameweek_orchestrator.analyze_video_job",
        side_effect=fake_analyze,
    ):
        result = asyncio.run(run_gameweek_orchestration(jobs))

    assert [item.success for item in result.results] == [True, False, True]
    assert result.results[0].analysis is not None
    assert result.results[0].error is None
    assert result.results[1].analysis is None
    assert result.results[1].error == "Transcript fetch failed"
    assert result.results[1].job.expert_name == "FPL General"
    assert result.results[2].analysis is not None
