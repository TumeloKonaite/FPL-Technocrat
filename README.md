# FPL-Technocrat

FPL-Technocrat runs a YouTube-first weekly Fantasy Premier League reporting workflow. It discovers recent expert videos, fetches transcripts, extracts structured analysis, aggregates consensus across experts, and writes a reviewable run folder under `runs/`.

## Prerequisites

- Python `3.12`
- [`uv`](https://docs.astral.sh/uv/)
- Docker Desktop or Docker Engine if you want the container workflow

## Quick Start

```bash
cp .env.example .env
make install
make test
make run-ui
```

Open the Streamlit app at `http://localhost:8501`.

## Environment Variables

Copy `.env.example` to `.env` and fill in the values you need.

| Variable | Required | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | Usually yes | Credentials for the `openai-agents` runtime used during expert analysis and final synthesis |
| `OPENAI_BASE_URL` | Optional | Base URL for an OpenAI-compatible provider |
| `OPENAI_DEFAULT_MODEL` | Optional | Default SDK model for agents that do not set `model=...` explicitly |
| `ENABLE_WEBSHARE_PROXY` | Optional | Set to `true` to route transcript fetches through Webshare |
| `WEBSHARE_PROXY_USERNAME` | If proxy enabled | Webshare username |
| `WEBSHARE_PROXY_PASSWORD` | If proxy enabled | Webshare password |

`--no-synthesis` only skips the final report synthesis step. The pipeline still uses `openai-agents` earlier to analyze video transcripts, so real pipeline runs still need provider credentials.

This repo currently sets `model="gpt-4.1"` directly in the agent definitions, so `OPENAI_DEFAULT_MODEL` only matters if you later remove those explicit model settings or add new agents that rely on SDK defaults.

## Local Development

Install dependencies:

```bash
make install
```

Run the full test suite:

```bash
make test
```

Run lint checks:

```bash
make lint
```

## Main Execution Paths

### CLI Pipeline

Source of truth command:

```bash
uv run python -m app.main --gameweek 32 --output-dir runs/gw32-example --per-expert-limit 2 --no-synthesis
```

Equivalent Make target:

```bash
make run-cli GAMEWEEK=32 OUTPUT_DIR=runs/gw32-example
```

Useful overrides:

- `PER_EXPERT_LIMIT=3`
- `EXPERT_NAME="FPL Focal"`
- `EXPERT_COUNT=5`
- `SYNTHESIS=1`

### Streamlit Dashboard

Source of truth command:

```bash
uv run streamlit run app/ui/streamlit_app.py
```

Equivalent Make target:

```bash
make run-ui
```

To load a specific run folder or artifact:

```bash
uv run streamlit run app/ui/streamlit_app.py -- --input runs/gw32
make run-ui INPUT=runs/gw32
```

The UI can also launch a fresh pipeline run from the sidebar and reload the resulting report into the same session.

### Test Suite

Source of truth command:

```bash
uv run pytest
```

Equivalent Make target:

```bash
make test
```

## Docker Workflow

Build the image:

```bash
make docker-build
```

Run the Streamlit UI in Docker:

```bash
make docker-run
```

Then open `http://localhost:8501`.

Notes:

- `docker-compose.yml` is included because it makes local UI startup, `.env` loading, and persistent `runs/` and `data/` directories much easier for contributors.
- The container mounts `./runs` and `./data` into `/app/runs` and `/app/data`, so generated artifacts stay on your host machine.
- If you prefer plain Docker for the CLI, you can override the container command:

```bash
docker run --rm -it --env-file .env \
  -v "$(pwd)/runs:/app/runs" \
  -v "$(pwd)/data:/app/data" \
  fpl-agent:latest \
  uv run python -m app.main --gameweek 32 --output-dir runs/gw32-docker --per-expert-limit 2 --no-synthesis
```

Stop the Compose service with:

```bash
make docker-down
```

## Weekly Workflow

1. Update `.env` if provider credentials or proxy settings changed.
2. Run the weekly pipeline with `make run-cli GAMEWEEK=<n> OUTPUT_DIR=runs/gw<n>`.
3. Review `runs/gw<n>/report.md` and the corresponding JSON artifacts.
4. Open the dashboard with `make run-ui INPUT=runs/gw<n>` for visual review.
5. Re-run with different filters if you want to limit experts or compare outputs.

## Run Artifacts

Each pipeline run writes a folder under `runs/`. The main files are:

- `discovered_videos.json`: normalized video metadata collected from configured YouTube expert channels
- `input_jobs.json`: validated analysis jobs created from relevant videos with usable transcripts
- `expert_outputs.json`: structured output returned for successful expert-analysis jobs
- `aggregate_report.json`: deterministic consensus, disagreement, and summary data
- `final_report.json`: final weekly report consumed by the UI
- `report.md`: human-readable markdown report for review and handoff
- `manifest.json`: counts, failures, and artifact references for the run

`manifest.json` is the first place to check for partial-failure details such as transcript fetch issues, job failures, and item counts through the pipeline.

## How The Pipeline Flows

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

## Troubleshooting

- `Pipeline could not create any usable video analysis jobs from YouTube sources`: discovery returned no relevant videos, or no usable transcript could be fetched.
- `Pipeline did not produce any expert analyses`: every job failed or had an unusable transcript.
- Webshare errors: if `ENABLE_WEBSHARE_PROXY=true`, both proxy credentials must be set.
- Transcript fetch errors are retried with bounded backoff before being recorded in `manifest.json`.
- Successful transcripts are cached under `data/transcripts/`.

## Key Code Paths

- CLI entry: [app/cli/run_gameweek_report.py](/home/l/projects/fpl_agent/app/cli/run_gameweek_report.py)
- Streamlit app: [app/ui/streamlit_app.py](/home/l/projects/fpl_agent/app/ui/streamlit_app.py)
- Streamlit-triggered pipeline runs: [app/ui/pipeline_runner.py](/home/l/projects/fpl_agent/app/ui/pipeline_runner.py)
- Pipeline orchestration: [src/services/pipeline_service.py](/home/l/projects/fpl_agent/src/services/pipeline_service.py)
- YouTube ingestion: [src/services/transcript_ingestion_service.py](/home/l/projects/fpl_agent/src/services/transcript_ingestion_service.py)
- Aggregation and consensus: [src/services/aggregation_service.py](/home/l/projects/fpl_agent/src/services/aggregation_service.py)
- Final synthesis and fallback report generation: [src/services/synthesis_service.py](/home/l/projects/fpl_agent/src/services/synthesis_service.py)
