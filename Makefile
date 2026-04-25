.PHONY: setup lint format test dev down logs

setup:
	uv sync
	uv run pre-commit install
	uv run pre-commit install --hook-type commit-msg

lint:
	uv run ruff check .
	uv run ty check .

format:
	uv run ruff format .

test:
	uv run pytest

dev:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f
