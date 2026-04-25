# AntGuard

AntGuard is a high-performance, decoupled microservices ecosystem designed for personal finance and budget management. It features an asynchronous Telegram bot for rapid transaction entry and a Streamlit dashboard for financial visualization.

## Purpose

The primary goal of AntGuard is to provide a frictionless experience for tracking expenses. By using deterministic Regex and dictionary mapping within a Telegram bot, users can log transactions instantly without the latency of external AI services. The architecture prioritizes performance, maintainability, and precision (using `Decimal128` for financial data).

## Technology Stack

- **Language**: Python 3.12+ with strict typing validated by `ty` (Astral's high-performance type checker).
- **Environment & Dependencies**: `uv` for ultra-fast dependency resolution and virtual environment management.
- **Code Quality**: `ruff` acting as the unified linter and formatter.
- **Telegram Client**: Custom asynchronous client built directly on `httpx` (no heavy external SDKs/frameworks).
- **Visualization**: Streamlit, secured with a simple authentication layer.
- **Database & Persistence**: MongoDB Atlas, accessed via **Motor** (`motor.motor_asyncio`) with pure **Pydantic v2** models for data validation and serialization.
- **Orchestration**: Docker and Docker Compose.
- **Automation**: `Makefile` and `pre-commit` hooks (validating formatting, typing, and Conventional Commits).

## Software Architecture

AntGuard follows a decoupled microservices architecture deployed via Docker Compose:

1. **Bot Service**: Processes Telegram messages using an internal Regex engine.
2. **Dashboard Service**: Serves the Streamlit web interface.
3. **Shared Models**: Common Pydantic `BaseModel` subclasses shared between the Bot and the Dashboard. No ODM — Motor is used directly for database access.
4. **MongoDB**: The central database storing all transactions and state.

## Local Setup

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [uv](https://github.com/astral-sh/uv) (Astral's Python package manager)
- `make` utility

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ant_guard
   ```

2. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill in the required values:
   - `TELEGRAM_TOKEN`: Your Telegram Bot API token.
   - `AUTHORIZED_USER_ID`: Your personal Telegram User ID (for single-tenant security).
   - `MONGO_URI`: The MongoDB connection string (defaults to local docker container).
   - `DASHBOARD_PASSWORD`: Password for the Streamlit dashboard.

3. **Initialize the Development Environment:**
   Run the setup target to install dependencies and configure `pre-commit` hooks:
   ```bash
   make setup
   ```

4. **Start the Application:**
   Spin up the Dockerized ecosystem (MongoDB, Bot, and Dashboard):
   ```bash
   make dev
   ```

5. **Access the Services:**
   - The **Bot** will start listening to your Telegram messages.
   - The **Dashboard** is accessible at: `http://localhost:8501`.

## Development Commands

A `Makefile` is provided to standardize the development lifecycle:
- `make setup`: Installs `uv`, syncs the environment, and configures pre-commit hooks.
- `make lint`: Runs `ruff` and `ty` to validate code quality and types.
- `make test`: Runs the `pytest` suite.
- `make dev`: Starts the local Docker Compose services.
- `make down`: Stops the Docker Compose services.
- `make logs`: Tails the logs of the Docker containers.

## CI/CD and Quality Standards

All commits are gated by strict `pre-commit` hooks to ensure high quality:
- `ruff check --fix` and `ruff format`
- `ty check` for static typing
- `conventional-pre-commit` for commit message standard adherence.

Every push will eventually be gated by a `pytest` suite execution.

## Testing & Documentation Standards

### Testing

- **Test functions, not classes**: Every test case is a standalone `def test_*` or `async def test_*` function.
- **Unit tests**: Exercise a single function in isolation — mock all external dependencies (DB, HTTP, env vars).
- **Integration tests**: Require a running service or real database. Place them in `tests/integration/` and mark with `@pytest.mark.integration`.
- **One behavior per test**: Keep each test focused on a single assertion or behavior for self-documenting failures.

### Docstrings

All public functions and methods require a docstring following Google style, with these sections when applicable:

```python
def my_function(param: str) -> int:
    """Short one-line summary.

    Args:
        param: Description of the parameter.

    Returns:
        Description of the return value.

    Raises:
        ValueError: When and why this is raised.
    """
```
