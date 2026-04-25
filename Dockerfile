# Stage 1: Builder
FROM python:3.12-slim-bookworm AS builder

# Install uv from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# --frozen ensures we use the exact versions in uv.lock
# --no-dev excludes development dependencies
RUN uv sync --frozen --no-dev

# Copy the rest of the application
COPY src/ ./src/

# Stage 2: Runtime
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Copy the virtual environment and application code from the builder stage
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

# Expose Streamlit port
EXPOSE 8501

# Command will be overridden by docker-compose for each specific service
CMD ["python", "-m", "src.bot.main"]
