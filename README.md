# FPL-Technocrat

FPL-Technocrat runs a YouTube-first automated weekly workflow for Fantasy Premier League reporting. It discovers recent videos from configured expert channels, filters the relevant ones, fetches transcripts, builds validated analysis jobs, aggregates consensus across experts, and writes a complete run folder to disk.

## Purpose

Use this project when you want a repeatable weekly workflow for:

- discovering the latest videos from trusted FPL experts
- filtering and ingesting usable transcript inputs for one gameweek
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

## Automated Flow

Each run follows the same pipeline:

```text
Configured expert channels
    ↓
Discover latest videos
    ↓
Filter relevant videos
    ↓
Fetch transcripts
    ↓
Build VideoAnalysisJobs
    ↓
Run expert analysis
    ↓
Aggregate consensus/disagreements
    ↓
Write artifacts + final report
```

## Run The CLI

```bash
uv run python -m app.main \
  --gameweek 32 \
  --output-dir runs/gw32-example \
  --per-expert-limit 2 \
  --no-synthesis
```

To enable final synthesis, drop `--no-synthesis`. The default per-expert discovery limit is `2`.

## Outputs

Each run writes a folder under the requested output path with these artifacts:

- `discovered_videos.json`: normalized latest-video metadata collected from configured channels
- `input_jobs.json`: validated jobs built from relevant videos with usable transcripts
- `expert_outputs.json`: structured output for successfully analyzed jobs
- `aggregate_report.json`: deterministic consensus and disagreement data
- `final_report.json`: final weekly report, either synthesized or fallback
- `manifest.json`: artifact map plus ingestion, dedupe, transcript, and orchestration counts/failures

The manifest records fields such as:

- `input_mode`
- `configured_experts`
- `videos_discovered`
- `videos_selected`
- `jobs_created`
- `transcript_failures`
- `failed_jobs`

## Weekly Workflow Notes

- Duplicate video URLs are deduplicated before orchestration.
- If no URL is available, duplicate transcript content from the same expert is deduplicated conservatively.
- Transcript failures are recorded in `manifest.json` and do not block a run if at least one usable job is created.
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
uv run pytest tests/services/test_transcript_ingestion_service.py
uv run pytest tests/services/test_normalization.py
uv run pytest tests/services/test_edge_cases.py
uv run pytest tests/services/test_partial_failures.py
```

## Troubleshooting

- `Pipeline could not create any usable video analysis jobs from YouTube sources`: discovery returned no relevant videos or no transcript could be used.
- `Pipeline did not produce any expert analyses`: every job either failed or produced an unusable transcript.
- Transcript fetch errors: transient provider failures are retried with bounded backoff; exhausted retries are returned as readable errors.
- Empty report sections: this is expected when transcripts do not mention captaincy, chips, transfers, or fixture notes clearly enough.

## Key Code Paths

- CLI entry: [`app/cli/run_gameweek_report.py`](/home/l/projects/fpl_agent/app/cli/run_gameweek_report.py)
- Pipeline orchestration: [`src/services/pipeline_service.py`](/home/l/projects/fpl_agent/src/services/pipeline_service.py)
- YouTube ingestion: [`src/services/transcript_ingestion_service.py`](/home/l/projects/fpl_agent/src/services/transcript_ingestion_service.py)
- Aggregation and consensus: [`src/services/aggregation_service.py`](/home/l/projects/fpl_agent/src/services/aggregation_service.py)
- Normalization rules: [`src/services/normalization.py`](/home/l/projects/fpl_agent/src/services/normalization.py)
- Final synthesis fallback: [`src/services/synthesis_service.py`](/home/l/projects/fpl_agent/src/services/synthesis_service.py)
