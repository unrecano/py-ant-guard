"""Unit and integration tests for src/shared models and database connector.

Test naming convention:
  - Unit tests: test functions that exercise a single unit in isolation,
    using mocks for external dependencies (no I/O, no network).
  - Integration tests: test functions that require the service or a real
    database to be running (annotated with @pytest.mark.integration or
    placed in tests/integration/).

All tests are plain functions, not class-based, one function per case.
"""

from __future__ import annotations

from decimal import Decimal
from typing import cast
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from pydantic import ValidationError

from shared.models import Budget, Transaction, TransactionType


def test_transaction_valid_construction() -> None:
    """Happy path: Transaction is created with all valid fields."""
    tx = Transaction(
        amount=Decimal("5.50"),
        category="snacks",
        type=TransactionType.EXPENSE,
        user_id=12345,
    )

    assert tx.amount == Decimal("5.50")
    assert tx.category == "snacks"
    assert tx.type == TransactionType.EXPENSE
    assert tx.user_id == 12345
    assert tx.created_at is not None


def test_transaction_amount_is_decimal() -> None:
    """Amount field must be stored as Decimal, not float."""
    tx = Transaction(
        amount=Decimal("5.50"),
        category="food",
        type=TransactionType.INCOME,
        user_id=99,
    )
    assert isinstance(tx.amount, Decimal)


def test_transaction_invalid_amount_raises() -> None:
    """Non-numeric amount must raise Pydantic ValidationError."""
    with pytest.raises(ValidationError):
        Transaction(
            amount=cast(Decimal, "not_a_number"),
            category="food",
            type=TransactionType.EXPENSE,
            user_id=12345,
        )


def test_transaction_invalid_type_enum_raises() -> None:
    """Invalid TransactionType string must raise Pydantic ValidationError."""
    with pytest.raises(ValidationError):
        Transaction(
            amount=Decimal("10.00"),
            category="food",
            type=cast(TransactionType, "INVALID_TYPE"),
            user_id=12345,
        )


def test_transaction_decimal_precision_preserved() -> None:
    """High-precision Decimal must not lose digits during model construction."""
    precise = Decimal("10.00000001")
    tx = Transaction(
        amount=precise,
        category="precision-test",
        type=TransactionType.EXPENSE,
        user_id=1,
    )
    assert tx.amount == precise
    assert str(tx.amount) == "10.00000001"


def test_budget_valid_construction_with_default_threshold() -> None:
    """Happy path: Budget uses 0.8 as default alert_threshold."""
    budget = Budget(category="groceries", monthly_limit=Decimal("500.00"))

    assert budget.category == "groceries"
    assert budget.monthly_limit == Decimal("500.00")
    assert budget.alert_threshold == 0.8


def test_budget_custom_alert_threshold() -> None:
    """Budget alert_threshold can be overridden at construction time."""
    budget = Budget(
        category="entertainment",
        monthly_limit=Decimal("200.00"),
        alert_threshold=0.5,
    )
    assert budget.alert_threshold == 0.5


def test_budget_decimal_precision_preserved() -> None:
    """monthly_limit must retain full Decimal precision."""
    precise = Decimal("999.99999999")
    budget = Budget(category="groceries", monthly_limit=precise)
    assert budget.monthly_limit == precise


@pytest.mark.asyncio
async def test_init_db_returns_default_database() -> None:
    """init_db must return the database obtained from get_default_database."""
    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(return_value=MagicMock())
    mock_client = MagicMock()
    mock_client.get_default_database.return_value = mock_db

    with patch("shared.database.AsyncIOMotorClient", return_value=mock_client):
        with patch("shared.database.ensure_indexes", new_callable=AsyncMock):
            from shared.database import init_db

            result = await init_db("mongodb://localhost:27017/ant_guard")

    assert result is mock_db


@pytest.mark.asyncio
async def test_init_db_calls_ensure_indexes() -> None:
    """init_db must delegate index creation to ensure_indexes."""
    mock_db = MagicMock()
    mock_client = MagicMock()
    mock_client.get_default_database.return_value = mock_db

    with patch("shared.database.AsyncIOMotorClient", return_value=mock_client):
        with patch(
            "shared.database.ensure_indexes", new_callable=AsyncMock
        ) as mock_ensure:
            from shared.database import init_db

            await init_db("mongodb://localhost:27017/ant_guard")

    mock_ensure.assert_awaited_once_with(mock_db)


@pytest.mark.asyncio
async def test_ensure_indexes_creates_expected_indexes() -> None:
    """ensure_indexes must create exactly 3 indexes: 2 on transactions, 1 on budgets."""
    mock_transactions = AsyncMock()
    mock_budgets = AsyncMock()

    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(
        side_effect=lambda name: (
            mock_transactions if name == "transactions" else mock_budgets
        )
    )

    from shared.database import ensure_indexes

    await ensure_indexes(mock_db)

    assert mock_transactions.create_index.await_count == 2
    mock_transactions.create_index.assert_has_awaits(
        [call("category"), call("created_at")], any_order=False
    )
    mock_budgets.create_index.assert_awaited_once_with("category", unique=True)
