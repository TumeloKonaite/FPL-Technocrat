from __future__ import annotations

import asyncio
from collections.abc import Sequence

from src.schemas.expert_analysis import ExpertVideoAnalysis
from src.schemas.orchestration import GameweekOrchestrationResult, VideoAnalysisRunResult
from src.schemas.video_job import VideoAnalysisJob
from src.services.expert_analysis_service import analyze_video_job


def _build_run_result(
    job: VideoAnalysisJob,
    outcome: ExpertVideoAnalysis | Exception,
) -> VideoAnalysisRunResult:
    if isinstance(outcome, Exception):
        return VideoAnalysisRunResult(
            job=job,
            success=False,
            error=str(outcome),
        )

    return VideoAnalysisRunResult(
        job=job,
        success=True,
        analysis=outcome,
    )


async def run_gameweek_orchestration(
    jobs: Sequence[VideoAnalysisJob],
) -> GameweekOrchestrationResult:
    """Run expert video analysis for many jobs concurrently."""
    if not jobs:
        return GameweekOrchestrationResult(results=[])

    outcomes = await asyncio.gather(
        *(analyze_video_job(job) for job in jobs),
        return_exceptions=True,
    )

    results = [
        _build_run_result(job, outcome)
        for job, outcome in zip(jobs, outcomes, strict=True)
    ]
    return GameweekOrchestrationResult(results=results)


async def run_gameweek_analysis(
    jobs: Sequence[VideoAnalysisJob],
) -> GameweekOrchestrationResult:
    """Backward-compatible alias for the gameweek batch orchestrator."""
    return await run_gameweek_orchestration(jobs)
