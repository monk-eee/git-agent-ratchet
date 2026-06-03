.PHONY: setup test test-cov lint format ratchet seed-baseline clean help

UV ?= uv

help:
	@echo "Common targets:"
	@echo "  make setup          uv sync + pre-commit install"
	@echo "  make test           run pytest"
	@echo "  make test-cov       run pytest with coverage"
	@echo "  make lint           ruff check + ruff format --check"
	@echo "  make format         ruff check --fix + ruff format"
	@echo "  make ratchet        dogfood: run all three ratchets against this repo"
	@echo "  make seed-baseline  create the duplicates baseline from current state"
	@echo "  make clean          remove caches / build artefacts"

setup:
	$(UV) sync --all-extras
	$(UV) run pre-commit install

test:
	$(UV) run pytest -q

test-cov:
	$(UV) run pytest --cov=git_agent_ratchet --cov-report=term-missing --cov-report=xml

lint:
	$(UV) run ruff check .
	$(UV) run ruff format --check .

format:
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

ratchet:
	$(UV) run git-agent-ratchet no-duplicate-helpers --dir git_agent_ratchet --baseline config/ratchets/duplicates.json
	$(UV) run git-agent-ratchet deny-agent-chatter $$(git ls-files '*.py' '*.md' '*.txt' '*.yaml' '*.yml' '*.toml')
	$(UV) run git-agent-ratchet anti-bypass --enforce-files AGENTS.md,.pre-commit-config.yaml,config/ratchets/duplicates.json,.pre-commit-hooks.yaml $$(git diff --cached --name-only)

seed-baseline:
	$(UV) run git-agent-ratchet no-duplicate-helpers --dir git_agent_ratchet --baseline config/ratchets/duplicates.json

clean:
	@if exist .pytest_cache rmdir /S /Q .pytest_cache
	@if exist .ruff_cache rmdir /S /Q .ruff_cache
	@if exist dist rmdir /S /Q dist
	@if exist build rmdir /S /Q build
	@if exist .coverage del /Q .coverage
	@if exist coverage.xml del /Q coverage.xml
