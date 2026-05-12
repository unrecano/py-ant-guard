from __future__ import annotations

import asyncio
import os
from datetime import date, datetime

import pandas as pd
import streamlit as st
from pydantic import TypeAdapter

from shared.database import init_db
from shared.models import Budget, Transaction


async def _fetch_data_async() -> tuple[list[Transaction], list[Budget]]:
    """Fetch transactions and budgets from MongoDB asynchronously.

    Returns:
        A tuple containing a list of Transaction models and a list of Budget models.
    """
    mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/ant_guard")
    db = await init_db(mongo_uri)

    transactions_cursor = db["transactions"].find()
    transactions_raw = await transactions_cursor.to_list(length=10000)

    budgets_cursor = db["budgets"].find()
    budgets_raw = await budgets_cursor.to_list(length=1000)

    # Convert raw BSON/dicts to Pydantic models
    transaction_adapter = TypeAdapter(list[Transaction])
    budget_adapter = TypeAdapter(list[Budget])

    transactions = transaction_adapter.validate_python(transactions_raw)
    budgets = budget_adapter.validate_python(budgets_raw)

    return transactions, budgets


@st.cache_data(ttl=600)
def get_financial_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch financial data and return as Pandas DataFrames.

    This function bridges the sync Streamlit environment with the async Motor client.

    Returns:
        A tuple of (transactions_df, budgets_df).
    """
    transactions, budgets = asyncio.run(_fetch_data_async())

    # Create DataFrames
    df_tx = pd.DataFrame([t.model_dump() for t in transactions])
    df_bg = pd.DataFrame([b.model_dump() for b in budgets])

    # Ensure empty DataFrames have correct columns if no data
    if df_tx.empty:
        df_tx = pd.DataFrame(columns=["amount", "category", "type", "created_at"])

    if df_bg.empty:
        df_bg = pd.DataFrame(columns=["category", "monthly_limit", "alert_threshold"])

    # Convert created_at to datetime objects if present
    if "created_at" in df_tx.columns:
        df_tx["created_at"] = pd.to_datetime(df_tx["created_at"])

    return df_tx, df_bg


def filter_data(
    df: pd.DataFrame, start_date: date | datetime, end_date: date | datetime
) -> pd.DataFrame:
    """Filter the transactions DataFrame by date range.

    Args:
        df: The transactions DataFrame.
        start_date: Start of the range.
        end_date: End of the range.

    Returns:
        Filtered DataFrame.
    """
    if df.empty:
        return df

    # Normalize to date for comparison if they are datetimes
    s_date = start_date.date() if isinstance(start_date, datetime) else start_date
    e_date = end_date.date() if isinstance(end_date, datetime) else end_date

    mask = (df["created_at"].dt.date >= s_date) & (df["created_at"].dt.date <= e_date)
    return df.loc[mask]
