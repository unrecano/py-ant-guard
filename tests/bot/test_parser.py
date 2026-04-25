from __future__ import annotations

from decimal import Decimal

from bot.parser import ParsedCommand, parse_message
from shared.models import TransactionType


def test_parse_expense_happy_path() -> None:
    """Test standard expense parsing."""
    result = parse_message("/g 5.50 snacks")
    assert result is not None
    assert isinstance(result, ParsedCommand)
    assert result.amount == Decimal("5.50")
    assert result.category == "snacks"
    assert result.transaction_type == TransactionType.EXPENSE
    assert result.description is None


def test_parse_income_happy_path() -> None:
    """Test standard income parsing."""
    result = parse_message("/i 1500 salary")
    assert result is not None
    assert result.amount == Decimal("1500")
    assert result.category == "other"
    assert result.transaction_type == TransactionType.INCOME
    assert result.description == "salary"


def test_parse_with_comma_decimal() -> None:
    """Test decimal with comma instead of dot."""
    result = parse_message("/g 3,50 café")
    assert result is not None
    assert result.amount == Decimal("3.50")
    assert result.category == "snacks"
    assert result.transaction_type == TransactionType.EXPENSE
    assert result.description is None


def test_parse_multiple_spaces() -> None:
    """Test parsing handles extra spaces correctly."""
    result = parse_message("/g 10  bus ")
    assert result is not None
    assert result.amount == Decimal("10.00")
    assert result.category == "transport"
    assert result.transaction_type == TransactionType.EXPENSE
    assert result.description is None


def test_parse_with_description() -> None:
    """Test parsing with a mapped category and a description."""
    result = parse_message("/g 12.5 uber to airport")
    assert result is not None
    assert result.amount == Decimal("12.5")
    assert result.category == "transport"
    assert result.transaction_type == TransactionType.EXPENSE
    assert result.description == "to airport"


def test_parse_invalid_command() -> None:
    """Test parsing an invalid command string."""
    result = parse_message("hello bot")
    assert result is None


def test_parse_invalid_amount() -> None:
    """Test parsing when amount is not numeric."""
    result = parse_message("/g invalid coffee")
    assert result is None


def test_parse_missing_amount() -> None:
    """Test parsing when amount is missing."""
    result = parse_message("/g")
    assert result is None


def test_parse_no_category() -> None:
    """Test parsing when only amount is provided."""
    result = parse_message("/g 50")
    assert result is not None
    assert result.amount == Decimal("50")
    assert result.category == "other"
    assert result.transaction_type == TransactionType.EXPENSE
    assert result.description is None
