"""Business logic for budget and balance calculations."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from bson.decimal128 import Decimal128
from motor.motor_asyncio import AsyncIOMotorDatabase

from shared.models import TransactionType

logger = logging.getLogger(__name__)

# Load config once
_CONFIG_PATH = Path(__file__).parent / "config.yaml"
with _CONFIG_PATH.open("r", encoding="utf-8") as f:
    _CONFIG = yaml.safe_load(f)

DEFAULT_ALERT_THRESHOLD = float(
    _CONFIG.get("budget", {}).get("default_alert_threshold", 0.8)
)


async def get_total_balance(db: AsyncIOMotorDatabase[Any], user_id: int) -> Decimal:
    """Calculate the total balance for a given user.

    The balance is defined as sum(Income) - sum(Expense).

    Args:
        db: The motor database client.
        user_id: The Telegram user ID to calculate the balance for.

    Returns:
        The total balance as a precise Decimal.
    """
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$type", "total": {"$sum": "$amount"}}},
    ]

    cursor = db["transactions"].aggregate(pipeline)

    income = Decimal("0.0")
    expense = Decimal("0.0")

    async for doc in cursor:
        type_ = doc["_id"]
        # MongoDB returns Decimal128 for amounts, convert to Python Decimal
        amount_val = doc["total"]
        if isinstance(amount_val, Decimal128):
            amount = amount_val.to_decimal()
        else:
            amount = Decimal(str(amount_val))

        if type_ == TransactionType.INCOME.value:
            income += amount
        elif type_ == TransactionType.EXPENSE.value:
            expense += amount

    return income - expense


async def check_budget_alerts(
    db: AsyncIOMotorDatabase[Any], category: str, user_id: int
) -> str:
    """Check if the spending in a category exceeds the budget threshold.

    Calculates the expenses for the current month in the given category and
    compares it against the budget threshold.

    Args:
        db: The motor database client.
        category: The category to check (e.g. "comida").
        user_id: The Telegram user ID to check.

    Returns:
        "OK", "WARNING", or "EXCEEDED" based on the threshold.
    """
    # 1. Fetch budget limit for the category
    budget_doc = await db["budgets"].find_one({"category": category})
    if not budget_doc:
        return "OK"  # No budget set for this category

    monthly_limit_val = budget_doc.get("monthly_limit")
    if not monthly_limit_val:
        return "OK"

    if isinstance(monthly_limit_val, Decimal128):
        monthly_limit = monthly_limit_val.to_decimal()
    else:
        monthly_limit = Decimal(str(monthly_limit_val))

    threshold = float(budget_doc.get("alert_threshold") or DEFAULT_ALERT_THRESHOLD)

    # 2. Calculate expenses for the current month
    now = datetime.now(UTC)
    start_of_month = datetime(now.year, now.month, 1, tzinfo=UTC)

    pipeline = [
        {
            "$match": {
                "user_id": user_id,
                "category": category,
                "type": TransactionType.EXPENSE.value,
                "created_at": {"$gte": start_of_month},
            }
        },
        {"$group": {"_id": None, "total_spent": {"$sum": "$amount"}}},
    ]

    cursor = db["transactions"].aggregate(pipeline)
    total_spent = Decimal("0.0")

    async for doc in cursor:
        spent_val = doc.get("total_spent", Decimal128("0.0"))
        if isinstance(spent_val, Decimal128):
            total_spent += spent_val.to_decimal()
        else:
            total_spent += Decimal(str(spent_val))

    # 3. Check against threshold
    threshold_amount = monthly_limit * Decimal(str(threshold))

    if total_spent > monthly_limit:
        return "EXCEEDED"
    if total_spent >= threshold_amount:
        return "WARNING"

    return "OK"
