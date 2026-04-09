from __future__ import annotations

import asyncio
import json
from unittest.mock import patch

import pytest

from src.schemas.aggregate_report import DisagreementReport
from src.schemas.expert_analysis import ExpertVideoAnalysis
from src.schemas.final_report import AggregatedFPLReport, FinalGameweekReport
from src.schemas.video_job import VideoAnalysisJob
from src.services.pipeline_service import PipelineServiceError, load_video_jobs, run_pipeline


def _build_job(*, expert_name: str = "Expert A", gameweek: int = 32) -> VideoAnalysisJob:
    return VideoAnalysisJob(
        expert_name=expert_name,
        video_title=f"{expert_name} GW{gameweek}",
        published_at="2026-04-09T12:00:00Z",
        gameweek=gameweek,
        transcript="Transcript",
        video_url=f"https://youtube.com/watch?v={expert_name.lower().replace(' ', '-')}",
    )


def _build_analysis(job: VideoAnalysisJob) -> ExpertVideoAnalysis:
    return ExpertVideoAnalysis(
        expert_name=job.expert_name,
        video_title=job.video_title,
        gameweek=job.gameweek,
        summary="Summary",
        key_takeaways=["Takeaway"],
        recommended_players=["Bukayo Saka"],
        avoid_players=[],
        captaincy_picks=["Mohamed Salah"],
        chip_strategy=None,
        reasoning=["Fixtures"],
        confidence="high",
    )


def _build_aggregate_report(gameweek: int = 32) -> AggregatedFPLReport:
    return AggregatedFPLReport(
        gameweek=gameweek,
        expert_count=1,
        player_consensus=[],
        captaincy_consensus=[],
        transfer_consensus=[],
        fixture_insights=[],
        chip_strategy_consensus=[],
        disagreements=DisagreementReport(),
        conditional_advice=[],
        wait_for_news=[],
    )


def _build_final_report(gameweek: int = 32) -> FinalGameweekReport:
    return FinalGameweekReport(
        gameweek=gameweek,
        overview="Overview",
        transfers=[],
        captaincy=[],
        chip_strategy=[],
        fixture_notes=[],
        disagreements=[],
        conditional_advice=[],
        wait_for_news=[],
        conclusion="Conclusion",
    )


def test_load_video_jobs_rejects_mismatched_gameweek(tmp_path) -> None:
    input_file = tmp_path / "jobs.json"
    input_file.write_text(json.dumps([_build_job(gameweek=31).model_dump()]), encoding="utf-8")

    with pytest.raises(PipelineServiceError, match="Input jobs must match the requested gameweek 32"):
        load_video_jobs(input_file, gameweek=32)


def test_run_pipeline_persists_artifacts_to_requested_output_dir(tmp_path) -> None:
    job = _build_job()
    analysis = _build_analysis(job)
    aggregate_report = _build_aggregate_report()
    final_report = _build_final_report()
    input_file = tmp_path / "jobs.json"
    output_dir = tmp_path / "runs" / "gw32"
    input_file.write_text(json.dumps([job.model_dump()]), encoding="utf-8")

    async def fake_orchestration(jobs: list[VideoAnalysisJob]):
        class _Result:
            def __init__(self) -> None:
                self.results = [
                    type(
                        "RunResult",
                        (),
                        {"success": True, "analysis": analysis, "job": jobs[0], "error": None},
                    )()
                ]

        return _Result()

    with patch(
        "src.services.pipeline_service.run_gameweek_orchestration",
        side_effect=fake_orchestration,
    ), patch(
        "src.services.pipeline_service.build_aggregated_fpl_report",
        return_value=aggregate_report,
    ), patch(
        "src.services.pipeline_service.synthesize_final_report",
        return_value=final_report,
    ):
        result = asyncio.run(
            run_pipeline(
                gameweek=32,
                input_file=input_file,
                output_dir=output_dir,
            )
        )

    assert result.run_path == output_dir
    assert (output_dir / "manifest.json").exists()
    assert json.loads((output_dir / "expert_outputs.json").read_text(encoding="utf-8")) == [
        analysis.model_dump()
    ]
    assert result.duplicate_sources == []


def test_run_pipeline_uses_fallback_report_when_synthesis_is_disabled(tmp_path) -> None:
    job = _build_job()
    analysis = _build_analysis(job)
    aggregate_report = _build_aggregate_report()
    fallback_report = _build_final_report()
    input_file = tmp_path / "jobs.json"
    output_dir = tmp_path / "runs" / "gw32"
    input_file.write_text(json.dumps([job.model_dump()]), encoding="utf-8")

    async def fake_orchestration(jobs: list[VideoAnalysisJob]):
        class _Result:
            def __init__(self) -> None:
                self.results = [
                    type(
                        "RunResult",
                        (),
                        {"success": True, "analysis": analysis, "job": jobs[0], "error": None},
                    )()
                ]

        return _Result()

    with patch(
        "src.services.pipeline_service.run_gameweek_orchestration",
        side_effect=fake_orchestration,
    ), patch(
        "src.services.pipeline_service.build_aggregated_fpl_report",
        return_value=aggregate_report,
    ), patch(
        "src.services.pipeline_service.build_fallback_final_report",
        return_value=fallback_report,
    ) as mocked_fallback, patch(
        "src.services.pipeline_service.synthesize_final_report",
    ) as mocked_synthesis:
        result = asyncio.run(
            run_pipeline(
                gameweek=32,
                input_file=input_file,
                output_dir=output_dir,
                synthesis_enabled=False,
            )
        )

    assert result.final_report == fallback_report
    mocked_fallback.assert_called_once_with(aggregate_report)
    mocked_synthesis.assert_not_called()
