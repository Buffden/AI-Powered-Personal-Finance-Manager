import streamlit as st
import pandas as pd
import altair as alt
from openai import OpenAI
import json
from backend.utils.config import Config
from frontend.components.AccountSelector import show_account_selector

def show_insights():
    st.title("📊 Spending Insights – AI Finance Manager")

    selected_accounts = show_account_selector()

    if not selected_accounts:
        st.warning("⚠️ Please select at least one account to view insights.")
        st.stop()

    if 'transactions' not in st.session_state:
        st.warning("No transaction data found. Go to 'Home' and connect your bank first.")
        st.stop()

    # Filter relevant transactions
    transactions = [
        tx for tx in st.session_state['transactions']
        if (tx.get('account_id') in selected_accounts or tx.get('source') == 'manual_upload')
    ]

    if not transactions:
        st.warning("No transactions found for selected accounts.")
        st.stop()

    # 🔁 Map account_id → institution name (bank)
    bank_name_map = {}
    if "linked_banks" in st.session_state:
        for bank in st.session_state["linked_banks"].values():
            institution_name = bank.get("institution_name", "Unknown Bank")
            for account in bank.get("accounts", []):
                bank_name_map[account["account_id"]] = institution_name

    # 📄 Create DataFrame
    df = pd.DataFrame(transactions)

    def parse_date(date_str):
        if isinstance(date_str, str):
            try:
                return pd.to_datetime(date_str)
            except:
                try:
                    return pd.to_datetime(date_str, format="%a, %d %b %Y %H:%M:%S GMT")
                except:
                    return pd.NaT
        return pd.NaT

    df["date"] = df["date"].apply(parse_date)
    df = df.dropna(subset=["date"]).sort_values("date", ascending=False)

    # Add bank name for Plaid transactions
    df["bank_name"] = df["account_id"].apply(lambda x: bank_name_map.get(x, "Unknown Bank"))

    # Normalize category format
    df["category"] = df["category"].apply(
        lambda x: x[0] if isinstance(x, list) and x else x if isinstance(x, str) else "Uncategorized"
    )

    # Format source label with bank name
    def format_source(row):
        if row.get("source") == "manual_upload":
            return "📷 Receipt"
        elif row.get("source") == "plaid":
            return f"🏦 {row.get('bank_name', 'Bank')}"
        else:
            return "🏦 Bank"

    df["formatted_source"] = df.apply(format_source, axis=1)

    # -------------------- Visualization --------------------

    # 1. Category-wise Spending
    st.subheader("🧾 Spending by Category")
    category_totals = df.groupby("category")["amount"].sum().reset_index().sort_values("amount", ascending=False)

    st.altair_chart(
        alt.Chart(category_totals).mark_bar().encode(
            x=alt.X("category", sort="-y", title="Category"),
            y=alt.Y("amount", title="Amount ($)"),
            tooltip=[
                alt.Tooltip("category", title="Category"),
                alt.Tooltip("amount", title="Amount", format="$.2f")
            ]
        ).properties(width=700),
        use_container_width=True
    )

    # 2. Time-based Spending
    st.subheader("📅 Spending Over Time")
    daily_spending = df.groupby("date")["amount"].sum().reset_index()

    st.altair_chart(
        alt.Chart(daily_spending).mark_line(point=True).encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("amount:Q", title="Amount ($)"),
            tooltip=[
                alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
                alt.Tooltip("amount:Q", title="Amount", format="$.2f")
            ]
        ).properties(width=700, height=400).interactive(),
        use_container_width=True
    )

    # 3. Raw Transaction Table
    st.subheader("📄 Transaction Table")
    display_df = df[["date", "name", "amount", "category", "formatted_source"]].copy()
    display_df.rename(columns={"formatted_source": "source"}, inplace=True)
    display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
    display_df["amount"] = display_df["amount"].map("${:,.2f}".format)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "date": "Date",
            "name": "Merchant",
            "amount": "Amount",
            "category": "Category",
            "source": "Source"
        }
    )

    # 4. AI Spending Trend Analysis
    st.subheader("🧠 Analyze My Spending Trends")
    if st.button("📊 Get AI Insights"):
        with st.spinner("Analyzing your charts..."):
            client = OpenAI()

            category_data = (
                df.groupby("category")["amount"].sum().reset_index().to_dict(orient="records")
            )

            date_df = (
                df.groupby("date")["amount"].sum().reset_index().sort_values("date")
            )
            date_df["date"] = date_df["date"].dt.strftime("%Y-%m-%d")
            date_data = date_df.to_dict(orient="records")

            prompt = f"""
You are a personal finance assistant. Analyze this user's spending patterns from two charts:

1. Category-wise totals:
{json.dumps(category_data, indent=2)}

2. Daily spending trends:
{json.dumps(date_data, indent=2)}

Tell the user:
- Which categories had unusually high or low spending.
- If any categories increased or decreased significantly.
- Any spikes, dips, or trends over time (e.g., mid-month spending surge).
Return natural-language bullet points. Be concise but insightful.
"""

            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful financial advisor analyzing spending trends."},
                        {"role": "user", "content": prompt}
                    ]
                )
                insights = response.choices[0].message.content
                st.markdown("### 🔍 AI-Generated Insights:")
                st.markdown(insights)
            except Exception as e:
                st.error(f"AI analysis failed: {str(e)}")
