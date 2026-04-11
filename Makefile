SHELL := /bin/bash
.DEFAULT_GOAL := help

UV ?= uv
IMAGE ?= fpl-agent
PORT ?= 8501
GAMEWEEK ?= 32
OUTPUT_DIR ?= runs/gw$(GAMEWEEK)-local
PER_EXPERT_LIMIT ?= 2
EXPERT_NAME ?=
EXPERT_COUNT ?=
INPUT ?=
SYNTHESIS ?= 0

.PHONY: help install test lint run-cli run-ui docker-build docker-run docker-down

help:
	@printf "Available targets:\n"
	@printf "  make install       Install project and dev dependencies with uv\n"
	@printf "  make test          Run the pytest suite\n"
	@printf "  make lint          Run Ruff against the repo\n"
	@printf "  make run-cli       Run the weekly pipeline CLI\n"
	@printf "  make run-ui        Start the Streamlit dashboard\n"
	@printf "  make docker-build  Build the Docker image\n"
	@printf "  make docker-run    Start the Docker Compose UI service\n"
	@printf "  make docker-down   Stop the Docker Compose UI service\n"

install:
	$(UV) sync --frozen --group dev

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check .

run-cli:
	@args=( \
		--gameweek "$(GAMEWEEK)" \
		--output-dir "$(OUTPUT_DIR)" \
		--per-expert-limit "$(PER_EXPERT_LIMIT)" \
	); \
	if [[ -n "$(EXPERT_NAME)" ]]; then args+=(--expert-name "$(EXPERT_NAME)"); fi; \
	if [[ -n "$(EXPERT_COUNT)" ]]; then args+=(--expert-count "$(EXPERT_COUNT)"); fi; \
	if [[ "$(SYNTHESIS)" != "1" && "$(SYNTHESIS)" != "true" && "$(SYNTHESIS)" != "TRUE" && "$(SYNTHESIS)" != "yes" && "$(SYNTHESIS)" != "YES" ]]; then args+=(--no-synthesis); fi; \
	$(UV) run python -m app.main "$${args[@]}"

run-ui:
	@args=(streamlit run app/ui/streamlit_app.py --server.port "$(PORT)"); \
	if [[ -n "$(INPUT)" ]]; then args+=(-- --input "$(INPUT)"); fi; \
	$(UV) run "$${args[@]}"

docker-build:
	docker build -t $(IMAGE) .

docker-run:
	docker compose up --build ui

docker-down:
	docker compose down
