"""Integration tests for guardian logic using Testcontainers."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from bson.decimal128 import Decimal128
from motor.motor_asyncio import AsyncIOMotorClient
from testcontainers.mongodb import MongoDbContainer

from guardian.logic import check_budget_alerts, get_total_balance
from shared.models import TransactionType


@pytest.fixture(scope="module")
def mongo_container():
    """Start a MongoDB container for integration tests."""
    with MongoDbContainer("mongo:7.0") as mongo:
        yield mongo


@pytest.fixture
async def db(mongo_container):
    """Provide a clean Motor database for each test."""
    uri = mongo_container.get_connection_url()
    client = AsyncIOMotorClient(uri)
    db = client.get_database("test_db")

    # Ensure collections are clean
    await db["transactions"].delete_many({})
    await db["budgets"].delete_many({})

    yield db

    # Teardown
    await db["transactions"].delete_many({})
    await db["budgets"].delete_many({})
    client.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_total_balance_integration(db):
    """Test getting total balance with real aggregation pipeline."""
    user_id = 1

    await db["transactions"].insert_many(
        [
            {
                "user_id": user_id,
                "type": TransactionType.INCOME.value,
                "amount": Decimal128("1500.00"),
            },
            {
                "user_id": user_id,
                "type": TransactionType.INCOME.value,
                "amount": Decimal128("200.00"),
            },
            {
                "user_id": user_id,
                "type": TransactionType.EXPENSE.value,
                "amount": Decimal128("450.00"),
            },
            {
                "user_id": 2,
                "type": TransactionType.INCOME.value,
                "amount": Decimal128("999.00"),
            },  # Other user
        ]
    )

    balance = await get_total_balance(db, user_id=user_id)
    assert balance == Decimal("1250.00")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_check_budget_alerts_integration(db):
    """Test budget alerts with real aggregation pipeline."""
    user_id = 1
    category = "comida"

    now = datetime.now(UTC)

    await db["budgets"].insert_one(
        {
            "category": category,
            "monthly_limit": Decimal128("1000.00"),
            "alert_threshold": 0.8,
        }
    )

    # Expenses this month
    await db["transactions"].insert_many(
        [
            {
                "user_id": user_id,
                "type": TransactionType.EXPENSE.value,
                "category": category,
                "amount": Decimal128("500.00"),
                "created_at": now,
            },
            {
                "user_id": user_id,
                "type": TransactionType.EXPENSE.value,
                "category": category,
                "amount": Decimal128("310.00"),
                "created_at": now,
            },
        ]
    )

    # Total = 810 >= 800 (WARNING)
    status = await check_budget_alerts(db, category=category, user_id=user_id)
    assert status == "WARNING"

    # Add more expense to exceed limit
    await db["transactions"].insert_one(
        {
            "user_id": user_id,
            "type": TransactionType.EXPENSE.value,
            "category": category,
            "amount": Decimal128("200.00"),
            "created_at": now,
        }
    )

    status = await check_budget_alerts(db, category=category, user_id=user_id)
    assert status == "EXCEEDED"
