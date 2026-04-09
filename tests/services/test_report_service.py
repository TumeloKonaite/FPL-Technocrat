from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.schemas.expert_analysis import ExpertVideoAnalysis
from src.schemas.final_report import AggregatedFPLReport, FinalGameweekReport
from src.schemas.video_job import VideoAnalysisJob
from src.adapters.storage import load_json, save_json
from src.services.report_service import ReportService, load_run, persist_run


def _build_job(expert_name: str, index: int) -> VideoAnalysisJob:
    return VideoAnalysisJob(
        expert_name=expert_name,
        video_title=f"{expert_name} GW{index}",
        published_at=f"2026-04-0{index}T12:00:00Z",
        gameweek=index,
        transcript=f"Transcript for {expert_name}",
        video_url=f"https://youtube.com/watch?v=video-{index}",
    )


def _build_expert_output(expert_name: str, index: int) -> ExpertVideoAnalysis:
    return ExpertVideoAnalysis(
        expert_name=expert_name,
        video_title=f"{expert_name} GW{index}",
        gameweek=index,
        summary=f"Summary for {expert_name}",
        key_takeaways=[f"Takeaway {index}", "Nested structure check"],
        recommended_players=["Mohamed Salah", "Bukayo Saka"],
        avoid_players=["Ollie Watkins"],
        captaincy_picks=["Erling Haaland"],
        chip_strategy="wildcard",
        reasoning=["Form", "Fixtures"],
        confidence="high",
    )


def _build_aggregate_report() -> AggregatedFPLReport:
    return AggregatedFPLReport(
        gameweek=5,
        expert_count=2,
        player_consensus=[],
        captaincy_consensus=[],
        transfer_consensus=[],
        fixture_insights=[],
        chip_strategy_consensus=[],
        disagreements={"players": [], "captaincy": [], "strategy": []},
        conditional_advice=[],
        wait_for_news=["Bukayo Saka"],
    )


def _build_final_report() -> FinalGameweekReport:
    return FinalGameweekReport(
        gameweek=5,
        overview="Strong week to target premium midfielders.",
        transfers=[],
        captaincy=[],
        chip_strategy=[],
        fixture_notes=["Liverpool have a favorable matchup."],
        disagreements=[],
        conditional_advice=["Wait for press conference updates."],
        wait_for_news=["Bukayo Saka"],
        conclusion="Stay flexible before the deadline.",
    )


@dataclass
class _DebugArtifact:
    created_at: datetime
    location: Path


def test_persist_run_creates_unique_run_folders(tmp_path) -> None:
    input_jobs = [_build_job("Expert A", 5)]
    expert_outputs = [_build_expert_output("Expert A", 5)]
    aggregate_report = _build_aggregate_report()
    final_report = _build_final_report()

    first_run_path = persist_run(
        input_jobs=input_jobs,
        expert_outputs=expert_outputs,
        aggregate_report=aggregate_report,
        final_report=final_report,
        base_dir=tmp_path / "runs",
    )
    second_run_path = persist_run(
        input_jobs=input_jobs,
        expert_outputs=expert_outputs,
        aggregate_report=aggregate_report,
        final_report=final_report,
        base_dir=tmp_path / "runs",
    )

    assert first_run_path.parent == tmp_path / "runs"
    assert second_run_path.parent == tmp_path / "runs"
    assert first_run_path.exists()
    assert second_run_path.exists()
    assert first_run_path != second_run_path


def test_report_service_class_persists_runs(tmp_path) -> None:
    service = ReportService(base_dir=tmp_path / "runs")

    run_path = service.persist_run(
        input_jobs=[_build_job("Expert A", 5)],
        expert_outputs=[_build_expert_output("Expert A", 5)],
        aggregate_report=_build_aggregate_report(),
        final_report=_build_final_report(),
    )
    loaded = service.load_run(run_path)

    assert run_path.exists()
    assert loaded["run_path"] == run_path
    assert loaded["manifest"]["run_id"] == run_path.name


def test_persisted_json_is_stable_and_can_be_reloaded(tmp_path) -> None:
    input_jobs = [_build_job("Expert A", 5), _build_job("Expert B", 5)]
    expert_outputs = [_build_expert_output("Expert A", 5), _build_expert_output("Expert B", 5)]
    aggregate_report = _build_aggregate_report()
    final_report = _build_final_report()

    run_path = persist_run(
        input_jobs=input_jobs,
        expert_outputs=expert_outputs,
        aggregate_report=aggregate_report,
        final_report=final_report,
        base_dir=tmp_path / "runs",
    )

    input_jobs_path = run_path / "input_jobs.json"
    input_jobs_contents = input_jobs_path.read_text(encoding="utf-8")
    reloaded = load_run(run_path)

    assert input_jobs_contents.startswith("[\n  {")
    assert '"expert_name": "Expert A"' in input_jobs_contents
    assert input_jobs_contents.endswith("\n")
    assert json.loads(input_jobs_contents) == [job.model_dump() for job in input_jobs]
    assert reloaded["input_jobs"] == [job.model_dump() for job in input_jobs]
    assert reloaded["expert_outputs"] == [item.model_dump() for item in expert_outputs]
    assert reloaded["aggregate_report"] == aggregate_report.model_dump()
    assert reloaded["final_report"] == final_report.model_dump()


def test_save_json_handles_nested_datetimes_paths_and_dataclasses(tmp_path) -> None:
    json_path = tmp_path / "artifact.json"
    payload = {
        "debug": _DebugArtifact(
            created_at=datetime(2026, 4, 9, 18, 30, 12, tzinfo=timezone.utc),
            location=tmp_path / "runs" / "sample",
        ),
    }

    save_json(json_path, payload)
    loaded = load_json(json_path)

    assert loaded == {
        "debug": {
            "created_at": "2026-04-09T18:30:12Z",
            "location": str(tmp_path / "runs" / "sample"),
        }
    }


def test_manifest_is_self_describing_and_points_to_existing_artifacts(tmp_path) -> None:
    input_jobs = [_build_job("Expert A", 5), _build_job("Expert B", 5)]
    expert_outputs = [_build_expert_output("Expert A", 5), _build_expert_output("Expert B", 5)]
    aggregate_report = _build_aggregate_report()
    final_report = _build_final_report()

    run_path = persist_run(
        input_jobs=input_jobs,
        expert_outputs=expert_outputs,
        aggregate_report=aggregate_report,
        final_report=final_report,
        base_dir=tmp_path / "runs",
    )

    manifest = json.loads((run_path / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["run_id"] == run_path.name
    assert manifest["created_at"].endswith("Z")
    assert manifest["counts"] == {
        "input_jobs": 2,
        "expert_outputs": 2,
    }
    assert manifest["artifacts"] == {
        "aggregate_report": "aggregate_report.json",
        "expert_outputs": "expert_outputs.json",
        "final_report": "final_report.json",
        "input_jobs": "input_jobs.json",
    }

    for filename in manifest["artifacts"].values():
        assert (run_path / filename).exists()
