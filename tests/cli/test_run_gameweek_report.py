from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from app.cli.run_gameweek_report import build_parser, main
from src.schemas.aggregate_report import DisagreementReport
from src.schemas.expert_analysis import ExpertVideoAnalysis
from src.schemas.final_report import AggregatedFPLReport, FinalGameweekReport
from src.schemas.video_job import VideoAnalysisJob
from src.services.pipeline_service import PipelineRunResult, PipelineServiceError


def _build_job() -> VideoAnalysisJob:
    return VideoAnalysisJob(
        expert_name="Expert A",
        video_title="GW32 Preview",
        published_at="2026-04-09T12:00:00Z",
        gameweek=32,
        transcript="A transcript long enough for testing.",
        video_url="https://youtube.com/watch?v=expert-a",
    )


def _build_analysis() -> ExpertVideoAnalysis:
    return ExpertVideoAnalysis(
        expert_name="Expert A",
        video_title="GW32 Preview",
        gameweek=32,
        summary="Summary",
        key_takeaways=["Target Arsenal attackers"],
        recommended_players=["Bukayo Saka"],
        avoid_players=["Ollie Watkins"],
        captaincy_picks=["Mohamed Salah"],
        chip_strategy="wildcard",
        reasoning=["Fixtures"],
        confidence="high",
    )


def _build_aggregate_report() -> AggregatedFPLReport:
    return AggregatedFPLReport(
        gameweek=32,
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


def _build_final_report() -> FinalGameweekReport:
    return FinalGameweekReport(
        gameweek=32,
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


def test_argument_parsing_supports_required_inputs_and_no_synthesis_flag() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "--gameweek",
            "32",
            "--input-file",
            "data/gameweek_32_jobs.json",
            "--output-dir",
            "runs/gw32",
            "--no-synthesis",
        ]
    )

    assert args.gameweek == 32
    assert args.input_file == Path("data/gameweek_32_jobs.json")
    assert args.output_dir == Path("runs/gw32")
    assert args.no_synthesis is True


def test_cli_smoke_test_reports_success_and_passes_expected_arguments(capsys, tmp_path) -> None:
    input_file = tmp_path / "jobs.json"
    output_dir = tmp_path / "runs" / "gw32"
    result = PipelineRunResult(
        run_path=output_dir,
        input_jobs=[_build_job()],
        expert_outputs=[_build_analysis()],
        aggregate_report=_build_aggregate_report(),
        final_report=_build_final_report(),
        failed_jobs=[],
        synthesis_enabled=True,
    )

    with patch("app.cli.run_gameweek_report.run_pipeline_sync", return_value=result) as mocked_run:
        exit_code = main(
            [
                "--gameweek",
                "32",
                "--input-file",
                str(input_file),
                "--output-dir",
                str(output_dir),
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Pipeline completed successfully for gameweek 32." in captured.out
    assert str(output_dir) in captured.out
    assert captured.err == ""
    mocked_run.assert_called_once_with(
        gameweek=32,
        input_file=input_file,
        output_dir=output_dir,
        synthesis_enabled=True,
    )


def test_cli_end_to_end_mocked_pipeline_run_persists_outputs(tmp_path) -> None:
    input_file = tmp_path / "gameweek_32_jobs.json"
    output_dir = tmp_path / "runs" / "gw32"
    job = _build_job()
    input_file.write_text(json.dumps([job.model_dump()]), encoding="utf-8")
    analysis = _build_analysis()
    aggregate_report = _build_aggregate_report()
    final_report = _build_final_report()

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
        exit_code = main(
            [
                "--gameweek",
                "32",
                "--input-file",
                str(input_file),
                "--output-dir",
                str(output_dir),
            ]
        )

    assert exit_code == 0
    assert (output_dir / "input_jobs.json").exists()
    assert (output_dir / "expert_outputs.json").exists()
    assert (output_dir / "aggregate_report.json").exists()
    assert (output_dir / "final_report.json").exists()
    assert (output_dir / "manifest.json").exists()


def test_cli_returns_readable_failure_message(capsys, tmp_path) -> None:
    with patch(
        "app.cli.run_gameweek_report.run_pipeline_sync",
        side_effect=PipelineServiceError("Input file was not found."),
    ):
        exit_code = main(
            [
                "--gameweek",
                "32",
                "--input-file",
                str(tmp_path / "missing.json"),
                "--output-dir",
                str(tmp_path / "runs" / "gw32"),
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == "Error: Input file was not found."
