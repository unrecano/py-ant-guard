"""Unit tests for guardian logic."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson.decimal128 import Decimal128

from guardian.logic import check_budget_alerts, get_total_balance
from shared.models import TransactionType


async def _async_gen(items: list[dict[str, object]]):
    for item in items:
        yield item


@pytest.mark.asyncio
async def test_get_total_balance_happy_path():
    """Test get_total_balance with income and expense."""
    db_mock = MagicMock()

    # Mock aggregate cursor
    cursor_mock = _async_gen(
        [
            {"_id": TransactionType.INCOME.value, "total": Decimal128("1000.00")},
            {"_id": TransactionType.EXPENSE.value, "total": Decimal128("200.00")},
        ]
    )
    db_mock["transactions"].aggregate.return_value = cursor_mock

    balance = await get_total_balance(db_mock, user_id=123)

    assert balance == Decimal("800.00")
    db_mock["transactions"].aggregate.assert_called_once()


@pytest.mark.asyncio
async def test_get_total_balance_empty():
    """Test get_total_balance with no transactions."""
    db_mock = MagicMock()
    db_mock["transactions"].aggregate.return_value = _async_gen([])

    balance = await get_total_balance(db_mock, user_id=123)

    assert balance == Decimal("0.0")


@pytest.mark.asyncio
async def test_check_budget_alerts_warning():
    """Test check_budget_alerts triggers WARNING at 80%."""
    db_mock = MagicMock()

    # Mock find_one for budget
    db_mock["budgets"].find_one = AsyncMock(
        return_value={
            "category": "comida",
            "monthly_limit": Decimal128("100.00"),
            "alert_threshold": 0.8,
        }
    )

    # Mock aggregate for expenses
    db_mock["transactions"].aggregate.return_value = _async_gen(
        [{"_id": None, "total_spent": Decimal128("81.00")}]
    )

    status = await check_budget_alerts(db_mock, category="comida", user_id=123)

    assert status == "WARNING"


@pytest.mark.asyncio
async def test_check_budget_alerts_ok():
    """Test check_budget_alerts returns OK when under threshold."""
    db_mock = MagicMock()

    db_mock["budgets"].find_one = AsyncMock(
        return_value={
            "category": "comida",
            "monthly_limit": Decimal128("100.00"),
            "alert_threshold": 0.8,
        }
    )

    db_mock["transactions"].aggregate.return_value = _async_gen(
        [{"_id": None, "total_spent": Decimal128("50.00")}]
    )

    status = await check_budget_alerts(db_mock, category="comida", user_id=123)

    assert status == "OK"


@pytest.mark.asyncio
async def test_check_budget_alerts_exceeded():
    """Test check_budget_alerts returns EXCEEDED when over limit."""
    db_mock = MagicMock()

    db_mock["budgets"].find_one = AsyncMock(
        return_value={
            "category": "comida",
            "monthly_limit": Decimal128("100.00"),
            "alert_threshold": 0.8,
        }
    )

    db_mock["transactions"].aggregate.return_value = _async_gen(
        [{"_id": None, "total_spent": Decimal128("105.00")}]
    )

    status = await check_budget_alerts(db_mock, category="comida", user_id=123)

    assert status == "EXCEEDED"


@pytest.mark.asyncio
async def test_check_budget_alerts_no_budget():
    """Test check_budget_alerts returns OK when no budget exists."""
    db_mock = MagicMock()
    db_mock["budgets"].find_one = AsyncMock(return_value=None)

    status = await check_budget_alerts(db_mock, category="comida", user_id=123)

    assert status == "OK"
