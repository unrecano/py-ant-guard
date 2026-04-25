# AntGuard - Agent Instructions

This document provides context, rules, and guidelines for AI agents interacting with the AntGuard repository.

## 1. Environment & Tooling Constraints

- **Dependency Management**: You MUST use `uv` for package management (`uv add`, `uv sync`). Do not use `pip` directly.
- **Task Runner**: Use the provided `Makefile` for standard tasks:
  - `make setup`: Initializes the environment and pre-commit hooks.
  - `make lint`: Validates the codebase using `ruff` and `ty`.
  - `make test`: Runs unit tests via `pytest`.
  - `make dev`: Orchestrates local Docker containers.
- **Quality Standards**: 
  - All code MUST be strictly typed and pass `ty check .`.
  - All code MUST be formatted and linted using `ruff` (rules `E`, `F`, `B`, `I`, `UP`).
- **Commits**: You MUST strictly adhere to the **Conventional Commits** specification (e.g., `feat:`, `fix:`, `chore:`). The repository contains a pre-commit hook that will reject malformed commit messages.

## 2. Architectural Guidelines

- **Microservices Structure**: The project is split into decoupled services (`src/bot`, `src/dashboard`) that communicate via a shared database.
- **Shared Models**: Database and Pydantic models MUST reside in `src/shared` to avoid duplication. The models are mapped using **Beanie ODM**.
- **Financial Precision**: You MUST use `Decimal128` (from `bson.decimal128` and `decimal.Decimal`) for all currency/monetary amounts to prevent float rounding errors.

## 3. Bot Development Rules

- **No Heavy Frameworks**: Do NOT use SDKs like `python-telegram-bot`, `aiogram`, or `telethon`. The Telegram bot is a custom, lightweight, asynchronous client built directly on top of `httpx`.
- **NLP / Categorization**: Do NOT use external LLMs or AI APIs (like OpenAI) for categorization logic. The bot uses a deterministic, fast regex engine combined with a mapping dictionary to parse user inputs (e.g., `/g 5.50 snacks`).
- **Security**: The bot is **Single-Tenant**. Every incoming message MUST be validated against the `AUTHORIZED_USER_ID` environment variable. Messages from unauthorized users must be silently ignored.

## 4. Dashboard Development Rules

- **Framework**: Built with `streamlit`.
- **Authentication**: The dashboard is protected by a simple login screen. You must use `st.secrets` or environment variables (`DASHBOARD_PASSWORD`) to validate the session before rendering financial data.

## 5. Dockerization

- The application is deployed using Docker Compose with a unified multi-stage `Dockerfile`.
- When modifying dependencies or entry points, ensure the `Dockerfile` and `docker-compose.yml` remain compatible.
- The default development orchestration is executed via `make dev`.
