from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

import yaml
from pydantic import BaseModel

from shared.models import TransactionType

# Constant Regex Patterns
EXPENSE_PATTERN = re.compile(r"^/g\s+(\d+(?:[.,]\d+)?)(?:\s+(.*))?$")
INCOME_PATTERN = re.compile(r"^/i\s+(\d+(?:[.,]\d+)?)(?:\s+(.*))?$")

# Category Mapping
CATEGORIES_FILE = Path(__file__).parent / "categories.yaml"
with CATEGORIES_FILE.open("r", encoding="utf-8") as f:
    CATEGORY_MAP: dict[str, str] = yaml.safe_load(f) or {}


class ParsedCommand(BaseModel):
    """Structured output from the NLP command parser."""

    amount: Decimal
    category: str
    transaction_type: TransactionType
    description: str | None = None


def parse_message(text: str) -> ParsedCommand | None:
    """Parses a raw Telegram message into a structured ParsedCommand.

    Args:
        text: The raw text message from Telegram.

    Returns:
        A ParsedCommand object if the text is a valid command, None otherwise.
    """
    text = text.lower().strip()

    is_expense = text.startswith("/g")
    is_income = text.startswith("/i")

    if not is_expense and not is_income:
        return None

    pattern = EXPENSE_PATTERN if is_expense else INCOME_PATTERN
    match = pattern.match(text)

    if not match:
        return None

    amount_str = match.group(1).replace(",", ".")
    try:
        amount = Decimal(amount_str)
    except InvalidOperation:  # Should be rare due to regex, but good for safety
        return None

    rest_of_text = match.group(2)
    category = "other"
    description = None

    if rest_of_text:
        rest_of_text = rest_of_text.strip()
        parts = rest_of_text.split(maxsplit=1)
        if parts:
            first_word = parts[0]
            if first_word in CATEGORY_MAP:
                category = CATEGORY_MAP[first_word]
                description = parts[1] if len(parts) > 1 else None
            else:
                # Unmapped word: default to 'other' and use whole remainder
                category = "other"
                description = rest_of_text

    transaction_type = TransactionType.EXPENSE if is_expense else TransactionType.INCOME

    return ParsedCommand(
        amount=amount,
        category=category,
        transaction_type=transaction_type,
        description=description,
    )
