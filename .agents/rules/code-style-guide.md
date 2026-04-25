---
trigger: always_on
description: This document outlines the coding standards, style guidelines, and best practices that AI agents MUST follow when contributing to the AntGuard repository.
---

# AntGuard Code Style Guide

This document outlines the coding standards, style guidelines, and best practices that AI agents MUST follow when contributing to the AntGuard repository. These rules are derived from the project's configuration, existing codebase patterns, and modern Python standards.

## 1. Python Version & Modern Features

- **Target Version**: Python 3.12+
- **Future Annotations**: Every Python file MUST start with `from __future__ import annotations` to enable deferred evaluation of type annotations.
- **Modern Syntax**: Use modern Python syntax, such as the `|` operator for union types instead of `typing.Union` (e.g., `str | None` instead of `Optional[str]`), and built-in generic types (`list[str]`, `dict[str, Any]`) instead of importing from `typing`.
- **Enums**: Use `enum.StrEnum` (available in Python 3.11+) for string-based enumerations rather than inheriting from `(str, enum.Enum)`.
- **Timezones**: Always use `datetime.UTC` instead of `datetime.timezone.utc`.
- **Internal Imports**: Use relative imports (e.g., `from .database import init_db`) for intra-package module references instead of absolute imports (`from src.shared.database import init_db`) to prevent resolution errors in linters and IDEs.

## 2. Linting & Formatting

- **Tooling**: The project uses `ruff` as the unified linter and formatter.
- **Rules**: The following rule sets are enforced and must be respected:
  - `E` (pycodestyle errors)
  - `F` (Pyflakes)
  - `B` (flake8-bugbear)
  - `I` (isort - strict alphabetical import sorting)
  - `UP` (pyupgrade - enforces modern Python idioms)
- **Execution**: Run `make lint` or `make format` to verify and fix issues.

## 3. Strict Static Typing

- **Tooling**: The project uses `ty` (Astral's high-performance type checker) for strict static typing.
- **No Untyped Code**: All functions, methods, parameters, and variables MUST be strictly typed.
- **Type Checking Compliance**: Code MUST pass `ty check .` without errors.
- **Type Casting**: When dealing with external libraries that return types `ty` cannot infer correctly (or in negative test cases), use `typing.cast()` instead of `# type: ignore` whenever possible, as `# type: ignore[arg-type]` may not be honored by `ty`.

## 4. Documentation & Docstrings

- **Standard**: All public functions, classes, and methods MUST have a docstring following the **Google Style**.
- **Required Sections**: When applicable, docstrings MUST include:
  - `Args`: Describe every parameter and its purpose.
  - `Returns`: Describe the return value and its semantic meaning.
  - `Raises`: Document any exceptions the function can intentionally raise.
- **Short Docstrings**: One-liner docstrings are acceptable only for trivially obvious helper functions.

## 5. Data Models & Database

- **Pydantic**: Use pure Pydantic `BaseModel` for all shared data models and data contracts. Do NOT use Object-Document Mappers (ODMs) like Beanie.
- **MongoDB Identifiers**: Map MongoDB's `_id` field explicitly using Pydantic's `Field(alias="_id")` and `bson.ObjectId`.
- **Financial Data**: Use Python's `decimal.Decimal` for all monetary amounts to prevent float rounding errors.
- **Configuration**: Use `model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}` in Pydantic models to properly handle `ObjectId` and dual-name population.

## 6. Testing Practices

- **Framework**: `pytest` is the testing framework of choice. Async tests use `pytest-asyncio` with `asyncio_mode = "auto"`.
- **Structure**: Write tests as standalone functions (`def test_*` or `async def test_*`). Do NOT group tests inside classes.
- **Isolation**: Unit tests MUST exercise a single function in isolation. All external dependencies (Motor clients, Streamlit, external APIs) must be mocked using `unittest.mock`.
- **Single Assertion/Behavior**: Each test function should ideally validate one specific behavior to ensure self-documenting failures.

## 7. Commits

- **Specification**: All commits MUST adhere strictly to the **Conventional Commits** standard (e.g., `feat:`, `fix:`, `refactor:`, `test:`, `chore:`).