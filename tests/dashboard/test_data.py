from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast
from unittest.mock import MagicMock, patch

import pandas as pd

from dashboard.data import filter_data, get_financial_data
from shared.models import Transaction, TransactionType


def test_filter_data() -> None:
    """Test the filtering of transactions by date range."""
    df = pd.DataFrame(
        [
            {"created_at": datetime(2023, 1, 1, tzinfo=UTC), "amount": 10},
            {"created_at": datetime(2023, 1, 15, tzinfo=UTC), "amount": 20},
            {"created_at": datetime(2023, 2, 1, tzinfo=UTC), "amount": 30},
        ]
    )
    df["created_at"] = pd.to_datetime(df["created_at"])

    start = datetime(2023, 1, 1, tzinfo=UTC)
    end = datetime(2023, 1, 31, tzinfo=UTC)

    filtered = filter_data(df, start, end)
    assert len(filtered) == 2
    assert filtered["amount"].sum() == 30


@patch("dashboard.data._fetch_data_async")
def test_get_financial_data_empty(mock_fetch: MagicMock) -> None:
    """Test get_financial_data when database returns no records."""
    mock_fetch.return_value = ([], [])

    df_tx, df_bg = cast(Any, get_financial_data).__wrapped__()

    assert df_tx.empty
    assert "amount" in df_tx.columns
    assert df_bg.empty
    assert "monthly_limit" in df_bg.columns


@patch("dashboard.data._fetch_data_async")
def test_get_financial_data_with_data(mock_fetch: MagicMock) -> None:
    """Test get_financial_data with actual mocked records."""
    tx = Transaction(
        amount=Decimal("50.0"),
        category="Food",
        type=TransactionType.EXPENSE,
        user_id=123,
    )
    mock_fetch.return_value = ([tx], [])

    df_tx, df_bg = cast(Any, get_financial_data).__wrapped__()

    assert not df_tx.empty
    assert df_tx.iloc[0]["amount"] == Decimal("50.0")
    assert df_tx.iloc[0]["category"] == "Food"
