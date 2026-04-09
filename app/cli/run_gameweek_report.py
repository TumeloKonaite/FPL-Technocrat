from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from src.services.pipeline_service import PipelineServiceError, run_pipeline_sync


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.main",
        description="Run the FPL gameweek report pipeline from a JSON job file.",
    )
    parser.add_argument("--gameweek", type=int, required=True, help="Gameweek number to run.")
    parser.add_argument(
        "--input-file",
        type=Path,
        required=True,
        help="Path to the JSON file containing video analysis jobs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where run artifacts will be written.",
    )
    parser.add_argument(
        "--no-synthesis",
        action="store_true",
        help="Skip final LLM synthesis and write a deterministic fallback final report instead.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        result = run_pipeline_sync(
            gameweek=args.gameweek,
            input_file=args.input_file,
            output_dir=args.output_dir,
            synthesis_enabled=not args.no_synthesis,
        )
    except PipelineServiceError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: unexpected pipeline failure: {exc}", file=sys.stderr)
        return 1

    success_count = len(result.expert_outputs)
    failure_count = len(result.failed_jobs)
    synthesis_label = "disabled" if args.no_synthesis else "enabled"

    print(
        "Pipeline completed successfully for "
        f"gameweek {args.gameweek}. "
        f"Processed {success_count}/{len(result.input_jobs)} job(s); "
        f"synthesis {synthesis_label}. "
        f"Artifacts written to {result.run_path}."
    )
    if failure_count:
        print(f"Warning: {failure_count} job(s) failed during orchestration.", file=sys.stderr)

    return 0
