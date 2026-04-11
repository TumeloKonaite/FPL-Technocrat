from __future__ import annotations

from pathlib import Path

from app.ui.pipeline_runner import build_streamlit_output_dir


def test_build_streamlit_output_dir_uses_gameweek_and_runs_base() -> None:
    output_dir = build_streamlit_output_dir(gameweek=32, base_runs_dir="custom-runs")

    assert output_dir.parent == Path("custom-runs")
    assert output_dir.name.startswith("gw32-streamlit-")
