from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from decimal import Decimal

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add the 'src' directory to sys.path to allow absolute imports
# when running with 'streamlit run src/dashboard/app.py'
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from dashboard.auth import check_password  # noqa: E402
from dashboard.data import filter_data, get_financial_data  # noqa: E402
from shared.models import TransactionType  # noqa: E402

# Page config
st.set_page_config(
    page_title="AntGuard | Financial Storyteller",
    page_icon="🐜",
    layout="wide",
)


def main() -> None:
    """Main entry point for the Streamlit dashboard."""
    if not check_password():
        st.stop()

    st.title("🐜 AntGuard Dashboard")
    st.markdown("### Your financial story, told by ants.")

    # Data Ingestion
    try:
        df_tx, df_bg = get_financial_data()
    except Exception as e:
        st.error(f"Failed to fetch data from database: {e}")
        st.stop()

    # Sidebar Filters
    st.sidebar.header("Filters")
    today = datetime.now(UTC).date()
    start_of_month = today.replace(day=1)

    start_date = st.sidebar.date_input("Start Date", start_of_month)
    end_date = st.sidebar.date_input("End Date", today)

    if start_date > end_date:
        st.sidebar.error("Error: End date must fall after start date.")

    # Filter data
    df_tx_filtered = filter_data(df_tx, start_date, end_date)

    # Categories filter
    categories = sorted(df_tx["category"].unique()) if not df_tx.empty else []
    selected_categories = st.sidebar.multiselect(
        "Categories", categories, default=categories
    )

    if selected_categories:
        df_tx_filtered = df_tx_filtered[
            df_tx_filtered["category"].isin(selected_categories)
        ]

    # Metrics
    income = (
        Decimal(
            df_tx_filtered[df_tx_filtered["type"] == TransactionType.INCOME][
                "amount"
            ].sum()
        )
        if not df_tx_filtered.empty
        else Decimal(0)
    )
    expenses = (
        Decimal(
            df_tx_filtered[df_tx_filtered["type"] == TransactionType.EXPENSE][
                "amount"
            ].sum()
        )
        if not df_tx_filtered.empty
        else Decimal(0)
    )
    balance = income - expenses

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Income", f"${income:,.2f}", delta=None)
    m2.metric("Total Expenses", f"${expenses:,.2f}", delta=None, delta_color="inverse")
    m3.metric("Current Balance", f"${balance:,.2f}", delta=None)

    st.divider()

    # Visualizations
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Budget vs. Actual")
        if df_bg.empty:
            st.info("No budgets defined.")
        else:
            # Aggregate expenses by category for the filtered period
            category_expenses = (
                df_tx_filtered[df_tx_filtered["type"] == TransactionType.EXPENSE]
                .groupby("category")["amount"]
                .sum()
                .reset_index()
            )

            # Merge with budgets
            comparison = df_bg.merge(
                category_expenses, on="category", how="left"
            ).fillna(0)
            comparison.rename(columns={"amount": "spent"}, inplace=True)

            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=comparison["category"],
                    y=comparison["monthly_limit"],
                    name="Limit",
                    marker_color="lightgrey",
                )
            )
            fig.add_trace(
                go.Bar(
                    x=comparison["category"],
                    y=comparison["spent"],
                    name="Spent",
                    marker_color="indianred",
                )
            )
            fig.update_layout(barmode="group", height=400)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Expense Distribution")
        expense_df = df_tx_filtered[df_tx_filtered["type"] == TransactionType.EXPENSE]
        if expense_df.empty:
            st.info("No expense data for this period.")
        else:
            fig = px.pie(
                expense_df,
                values="amount",
                names="category",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Gastos Hormiga Analysis
    st.subheader("🐜 Gastos Hormiga (Petty Expenses)")
    st.markdown("Frequent transactions under **$10**")

    petty_threshold = 10.0
    petty_tx = df_tx_filtered[
        (df_tx_filtered["type"] == TransactionType.EXPENSE)
        & (df_tx_filtered["amount"].astype(float) < petty_threshold)
    ]

    if petty_tx.empty:
        st.success("No 'gastos hormiga' detected in this period. Great job!")
    else:
        # Show total wasted in petty expenses
        total_petty = petty_tx["amount"].sum()
        st.warning(
            f"You spent a total of **${total_petty:,.2f}** in small transactions."
        )

        # Show table
        st.dataframe(
            petty_tx[["created_at", "category", "amount"]].sort_values(
                "created_at", ascending=False
            ),
            use_container_width=True,
            hide_index=True,
        )


if __name__ == "__main__":
    main()
