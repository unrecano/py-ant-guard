"""Shared Pydantic models for AntGuard.

These are pure data-validation models. They carry no ODM logic —
serialization to/from MongoDB documents is handled explicitly in each
service's repository layer.
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from decimal import Decimal

from bson import ObjectId
from pydantic import BaseModel, Field


class TransactionType(enum.StrEnum):
    """Valid transaction types for the AntGuard bot."""

    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class Transaction(BaseModel):
    """Represents a single financial transaction recorded by the bot."""

    id: ObjectId | None = Field(default=None, alias="_id")
    amount: Decimal
    category: str
    type: TransactionType
    user_id: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}


class Budget(BaseModel):
    """Represents a monthly budget limit for a given spending category."""

    id: ObjectId | None = Field(default=None, alias="_id")
    category: str
    monthly_limit: Decimal
    alert_threshold: float = 0.8

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}
