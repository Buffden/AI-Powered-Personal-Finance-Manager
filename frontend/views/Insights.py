import streamlit as st
import pandas as pd
import altair as alt
from openai import OpenAI
import json
from backend.utils.config import Config
from components.AccountSelector import show_account_selector

def show_insights():
    st.title("📊 Spending Insights – AI Finance Manager")

    selected_accounts = show_account_selector()

    if not selected_accounts:
        st.warning("⚠️ Please select at least one account to view insights.")
        st.stop()

    if 'transactions' not in st.session_state:
        st.warning("No transaction data found. Go to 'Home' and connect your bank first.")
        st.stop()

    transactions = [
        tx for tx in st.session_state['transactions']
        if tx.get('account_id') in selected_accounts
    ]

    if not transactions:
        st.warning("No transactions found for selected accounts.")
        st.stop()

    df = pd.DataFrame(transactions)
    df["date"] = pd.to_datetime(df["date"])
    df["category"] = df["category"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

    # 1. Spending by Category
    st.subheader("🧾 Spending by Category")
    category_totals = df.groupby("category")["amount"].sum().reset_index()

    chart = alt.Chart(category_totals).mark_bar().encode(
        x=alt.X("category", sort="-y"),
        y="amount",
        tooltip=["category", "amount"]
    ).properties(width=700)

    st.altair_chart(chart)

    # 2. Spending Over Time
    st.subheader("📅 Spending Over Time")
    daily_spending = df.groupby("date")["amount"].sum().reset_index()

    line_chart = alt.Chart(daily_spending).mark_line(point=True).encode(
        x="date:T",
        y="amount:Q",
        tooltip=["date", "amount"]
    ).properties(width=700)

    st.altair_chart(line_chart)

    # 3. Raw Transaction Table
    st.subheader("📄 Transaction Table")
    st.dataframe(df[["date", "name", "amount", "category"]], use_container_width=True)

    # 4. AI-Powered Trend Analysis
    st.subheader("🧠 Analyze My Spending Trends")
    if st.button("📊 Get AI Insights"):
        with st.spinner("Analyzing your charts..."):
            client = OpenAI()

            # Group category totals
            category_data = (
                df.groupby("category")["amount"]
                .sum()
                .reset_index()
                .to_dict(orient="records")
            )

            # Group and stringify date-wise totals
            date_df = (
                df.groupby("date")["amount"]
                .sum()
                .reset_index()
                .sort_values("date")
            )
            date_df["date"] = date_df["date"].dt.strftime("%Y-%m-%d")  # 🔧 Convert to string
            date_data = date_df.to_dict(orient="records")

            # Prompt to OpenAI
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