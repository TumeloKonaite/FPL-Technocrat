# FPL-Technocrat

FPL-Technocrat turns a set of expert video transcripts into a structured Fantasy Premier League gameweek report. The pipeline validates input jobs, analyzes each transcript, aggregates consensus across experts, writes run artifacts to disk, and optionally produces a polished final synthesis.

## Purpose

Use this project when you want a repeatable weekly workflow for:

- collecting expert transcript inputs for one gameweek
- extracting structured picks from each source
- aggregating consensus, disagreements, and conditional advice
- saving a run folder another contributor can inspect later

## Install

This project targets Python `3.12+` and uses `uv`.

```bash
uv sync
```

If you prefer plain `pip`, create a virtual environment first and install the package plus dev tools from `pyproject.toml`.

## Environment Setup

Create a `.env` file if your agent or model provider requires environment variables. The exact values depend on the provider configured through `openai-agents`.

Typical setup includes:

- model API credentials
- any provider-specific base URLs

If you only want deterministic aggregation and artifact generation, you can run with `--no-synthesis` and avoid the final synthesis call.

## Input Format

The CLI expects a JSON array of jobs matching [`src/schemas/video_job.py`](/home/l/projects/fpl_agent/src/schemas/video_job.py). Each item needs:

- `expert_name`
- `video_title`
- `published_at`
- `gameweek`
- `transcript`
- optional `video_url`

A ready-to-run example lives at [`examples/example_gameweek_input.json`](/home/l/projects/fpl_agent/examples/example_gameweek_input.json).

## Run The CLI

```bash
uv run python -m app.main \
  --gameweek 32 \
  --input-file examples/example_gameweek_input.json \
  --output-dir runs/gw32-example \
  --no-synthesis
```

To enable final synthesis, drop `--no-synthesis`.

## Outputs

Each run writes a folder under the requested output path with these artifacts:

- `input_jobs.json`: the original requested jobs
- `expert_outputs.json`: structured output for successfully analyzed jobs
- `aggregate_report.json`: deterministic consensus and disagreement data
- `final_report.json`: final weekly report, either synthesized or fallback
- `manifest.json`: artifact map, counts, duplicate-source decisions, and failed jobs

## Weekly Workflow Notes

- Duplicate video URLs are deduplicated before orchestration.
- If no URL is available, duplicate transcript content from the same expert is deduplicated conservatively.
- Aggregation merges player aliases conservatively, so under-merging is preferred over a risky false merge.
- Empty sections stay valid and readable; missing captaincy, chip, transfer, or fixture sections do not crash the pipeline.
- Partial failures are preserved in `manifest.json` and do not block a run if at least one expert analysis succeeds.

## Testing

Run the full suite with:

```bash
uv run pytest
```

Useful focused runs:

```bash
uv run pytest tests/services/test_normalization.py
uv run pytest tests/services/test_edge_cases.py
uv run pytest tests/services/test_partial_failures.py
```

## Troubleshooting

- `Input file was not found`: check the `--input-file` path.
- `Input jobs must match the requested gameweek`: the CLI `--gameweek` must match every job in the JSON input.
- `Pipeline did not produce any expert analyses`: every job either failed or produced an unusable transcript.
- Transcript fetch errors: transient provider failures are retried with bounded backoff; exhausted retries are returned as readable errors.
- Empty report sections: this is expected when transcripts do not mention captaincy, chips, transfers, or fixture notes clearly enough.

## Key Code Paths

- CLI entry: [`app/cli/run_gameweek_report.py`](/home/l/projects/fpl_agent/app/cli/run_gameweek_report.py)
- Pipeline orchestration: [`src/services/pipeline_service.py`](/home/l/projects/fpl_agent/src/services/pipeline_service.py)
- Aggregation and consensus: [`src/services/aggregation_service.py`](/home/l/projects/fpl_agent/src/services/aggregation_service.py)
- Normalization rules: [`src/services/normalization.py`](/home/l/projects/fpl_agent/src/services/normalization.py)
- Final synthesis fallback: [`src/services/synthesis_service.py`](/home/l/projects/fpl_agent/src/services/synthesis_service.py)
