from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from src.adapters.storage import load_json
from src.orchestrators.gameweek_orchestrator import run_gameweek_orchestration
from src.schemas.expert_analysis import ExpertVideoAnalysis
from src.schemas.final_report import AggregatedFPLReport, FinalGameweekReport
from src.schemas.video_job import VideoAnalysisJob
from src.services.aggregation_service import build_aggregated_fpl_report
from src.services.report_service import ReportService
from src.services.synthesis_service import build_fallback_final_report, synthesize_final_report


class PipelineServiceError(Exception):
    """Raised when the gameweek pipeline cannot complete successfully."""


@dataclass(slots=True)
class PipelineRunResult:
    run_path: Path
    input_jobs: list[VideoAnalysisJob]
    expert_outputs: list[ExpertVideoAnalysis]
    aggregate_report: AggregatedFPLReport
    final_report: FinalGameweekReport
    failed_jobs: list[tuple[VideoAnalysisJob, str]]
    synthesis_enabled: bool


def _read_jobs_payload(input_file: str | Path) -> list[object]:
    try:
        payload = load_json(input_file)
    except FileNotFoundError as exc:
        raise PipelineServiceError(f"Input file was not found: {input_file}") from exc
    except json.JSONDecodeError as exc:
        raise PipelineServiceError(f"Input file is not valid JSON: {input_file}") from exc

    if not isinstance(payload, list):
        raise PipelineServiceError("Input file must contain a JSON array of video analysis jobs.")
    return payload


def load_video_jobs(input_file: str | Path, *, gameweek: int) -> list[VideoAnalysisJob]:
    try:
        jobs = [
            VideoAnalysisJob.model_validate(item)
            for item in _read_jobs_payload(input_file)
        ]
    except ValidationError as exc:
        raise PipelineServiceError(f"Input file contains an invalid video job: {exc}") from exc

    if not jobs:
        raise PipelineServiceError("Input file does not contain any video analysis jobs.")

    mismatched_jobs = [job.expert_name for job in jobs if job.gameweek != gameweek]
    if mismatched_jobs:
        raise PipelineServiceError(
            "Input jobs must match the requested gameweek "
            f"{gameweek}. Mismatched jobs: {', '.join(mismatched_jobs)}."
        )

    return jobs


async def run_pipeline(
    *,
    gameweek: int,
    input_file: str | Path,
    output_dir: str | Path,
    synthesis_enabled: bool = True,
    report_service: ReportService | None = None,
) -> PipelineRunResult:
    jobs = load_video_jobs(input_file, gameweek=gameweek)
    orchestration = await run_gameweek_orchestration(jobs)

    expert_outputs = [
        result.analysis
        for result in orchestration.results
        if result.success and result.analysis is not None
    ]
    failed_jobs = [
        (result.job, result.error or "Unknown pipeline error")
        for result in orchestration.results
        if not result.success
    ]

    if not expert_outputs:
        failure_details = "; ".join(f"{job.expert_name}: {error}" for job, error in failed_jobs)
        raise PipelineServiceError(
            "Pipeline did not produce any expert analyses."
            + (f" Failures: {failure_details}." if failure_details else "")
        )

    aggregate_report = build_aggregated_fpl_report(expert_outputs)
    final_report = (
        await synthesize_final_report(aggregate_report)
        if synthesis_enabled
        else build_fallback_final_report(aggregate_report)
    )

    run_path = (report_service or ReportService()).persist_run(
        input_jobs=jobs,
        expert_outputs=expert_outputs,
        aggregate_report=aggregate_report,
        final_report=final_report,
        run_dir=output_dir,
    )

    return PipelineRunResult(
        run_path=run_path,
        input_jobs=jobs,
        expert_outputs=expert_outputs,
        aggregate_report=aggregate_report,
        final_report=final_report,
        failed_jobs=failed_jobs,
        synthesis_enabled=synthesis_enabled,
    )


def run_pipeline_sync(
    *,
    gameweek: int,
    input_file: str | Path,
    output_dir: str | Path,
    synthesis_enabled: bool = True,
    report_service: ReportService | None = None,
) -> PipelineRunResult:
    return asyncio.run(
        run_pipeline(
            gameweek=gameweek,
            input_file=input_file,
            output_dir=output_dir,
            synthesis_enabled=synthesis_enabled,
            report_service=report_service,
        )
    )
