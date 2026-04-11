from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.ui.report_loader import (
    find_latest_run_dir,
    load_report_bundle,
    parse_streamlit_args,
    resolve_report_paths,
)


def _write_report(run_dir: Path, gameweek: int) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "final_report.json").write_text(
        (
            "{\n"
            f'  "gameweek": {gameweek},\n'
            '  "overview": "Overview",\n'
            '  "transfers": [],\n'
            '  "captaincy": [],\n'
            '  "chip_strategy": [],\n'
            '  "fixture_notes": [],\n'
            '  "disagreements": [],\n'
            '  "conditional_advice": [],\n'
            '  "wait_for_news": [],\n'
            '  "expert_team_reveals": [],\n'
            '  "conclusion": "Conclusion"\n'
            "}\n"
        ),
        encoding="utf-8",
    )


def test_parse_streamlit_args_supports_optional_input_and_runs_dir() -> None:
    args = parse_streamlit_args(["--input", "runs/gw32/final_report.json", "--runs-dir", "custom-runs"])

    assert args.input_path == "runs/gw32/final_report.json"
    assert args.runs_dir == "custom-runs"


def test_find_latest_run_dir_uses_latest_final_report_timestamp(tmp_path) -> None:
    older = tmp_path / "runs" / "gw31"
    newer = tmp_path / "runs" / "gw32"
    _write_report(older, gameweek=31)
    _write_report(newer, gameweek=32)

    older_report = older / "final_report.json"
    newer_report = newer / "final_report.json"
    os.utime(older_report, (1_700_000_000, 1_700_000_000))
    os.utime(newer_report, (1_700_000_100, 1_700_000_100))

    assert find_latest_run_dir(tmp_path / "runs") == newer


def test_resolve_report_paths_accepts_run_directory(tmp_path) -> None:
    run_dir = tmp_path / "runs" / "gw32"
    _write_report(run_dir, gameweek=32)
    (run_dir / "aggregate_report.json").write_text(
        (
            "{\n"
            '  "gameweek": 32,\n'
            '  "expert_count": 0,\n'
            '  "player_consensus": [],\n'
            '  "captaincy_consensus": [],\n'
            '  "transfer_consensus": [],\n'
            '  "fixture_insights": [],\n'
            '  "chip_strategy_consensus": [],\n'
            '  "disagreements": {"players": [], "captaincy": [], "strategy": []},\n'
            '  "conditional_advice": [],\n'
            '  "wait_for_news": [],\n'
            '  "expert_team_reveals": []\n'
            "}\n"
        ),
        encoding="utf-8",
    )

    resolved_run_dir, final_report_path, aggregate_report_path = resolve_report_paths(run_dir)

    assert resolved_run_dir == run_dir
    assert final_report_path == run_dir / "final_report.json"
    assert aggregate_report_path == run_dir / "aggregate_report.json"


def test_load_report_bundle_validates_realistic_payloads(tmp_path) -> None:
    run_dir = tmp_path / "runs" / "gw32"
    _write_report(run_dir, gameweek=32)
    (run_dir / "aggregate_report.json").write_text(
        (
            "{\n"
            '  "gameweek": 32,\n'
            '  "expert_count": 2,\n'
            '  "player_consensus": [],\n'
            '  "captaincy_consensus": [],\n'
            '  "transfer_consensus": [],\n'
            '  "fixture_insights": [],\n'
            '  "chip_strategy_consensus": [],\n'
            '  "disagreements": {"players": [], "captaincy": [], "strategy": []},\n'
            '  "conditional_advice": [],\n'
            '  "wait_for_news": [],\n'
            '  "expert_team_reveals": []\n'
            "}\n"
        ),
        encoding="utf-8",
    )

    bundle = load_report_bundle(run_dir)

    assert bundle.run_dir == run_dir
    assert bundle.final_report.gameweek == 32
    assert bundle.aggregate_report is not None
    assert bundle.aggregate_report.expert_count == 2


def test_find_latest_run_dir_raises_when_no_reports_exist(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        find_latest_run_dir(tmp_path / "runs")
