.PHONY: setup setup-hooks update-hooks lint format test dev down logs

setup:
	uv sync
	@make setup-hooks

setup-hooks:
	uv run pre-commit install
	uv run pre-commit install --hook-type commit-msg
	uv run pre-commit install --hook-type pre-push

update-hooks:
	uv run pre-commit autoupdate

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
