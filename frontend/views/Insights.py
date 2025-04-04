import streamlit as st
import pandas as pd
import altair as alt

def show_insights():
    st.title("📊 Spending Insights – AI Finance Manager")

    # Add Account Selector
    from components.AccountSelector import show_account_selector
    selected_accounts = show_account_selector()

    if not selected_accounts:
        st.warning("⚠️ Please select at least one account to view insights.")
        st.stop()

    # ✅ Fetch transactions from session state
    if 'transactions' not in st.session_state:
        st.warning("No transaction data found. Go to 'Home' and connect your bank first.")
        st.stop()

    # Filter transactions for selected accounts
    transactions = [
        tx for tx in st.session_state['transactions']
        if tx.get('account_id') in selected_accounts
    ]

    if not transactions:
        st.warning("No transactions found for selected accounts.")
        st.stop()

    df = pd.DataFrame(transactions)

    # 🔧 Preprocessing
    df["date"] = pd.to_datetime(df["date"])
    df["category"] = df["category"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

    # 📈 1. Spending by Category
    st.subheader("🧾 Spending by Category")
    category_totals = df.groupby("category")["amount"].sum().reset_index()

    chart = alt.Chart(category_totals).mark_bar().encode(
        x=alt.X("category", sort="-y"),
        y="amount",
        tooltip=["category", "amount"]
    ).properties(width=700)

    st.altair_chart(chart)

    # 📆 2. Spending Over Time
    st.subheader("📅 Spending Over Time")
    daily_spending = df.groupby("date")["amount"].sum().reset_index()

    line_chart = alt.Chart(daily_spending).mark_line(point=True).encode(
        x="date:T",
        y="amount:Q",
        tooltip=["date", "amount"]
    ).properties(width=700)

    st.altair_chart(line_chart)

    # 🧾 Raw Table
    st.subheader("📄 Transaction Table")
    st.dataframe(df[["date", "name", "amount", "category"]], use_container_width=True)
