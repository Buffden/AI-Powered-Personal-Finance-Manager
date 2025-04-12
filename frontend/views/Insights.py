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

    # Get all transactions including both bank and receipt transactions
    transactions = [
        tx for tx in st.session_state['transactions']
        if (tx.get('account_id') in selected_accounts or  # Bank transactions
            tx.get('source') == 'manual_upload')          # Receipt transactions
    ]

    if not transactions:
        st.warning("No transactions found for selected accounts.")
        st.stop()

    # Create DataFrame and ensure proper date handling
    df = pd.DataFrame(transactions)
    
    # Convert dates to datetime, handling different formats
    def parse_date(date_str):
        if isinstance(date_str, str):
            try:
                # Try parsing as ISO format first
                return pd.to_datetime(date_str)
            except:
                try:
                    # Try parsing as GMT format
                    return pd.to_datetime(date_str, format="%a, %d %b %Y %H:%M:%S GMT")
                except:
                    # If both fail, return NaT
                    return pd.NaT
        return pd.NaT

    df["date"] = df["date"].apply(parse_date)
    
    # Remove any rows with invalid dates
    df = df.dropna(subset=["date"])
    
    # Sort by date, newest first
    df = df.sort_values("date", ascending=False)
    
    # Standardize category format
    # Use only the first category
    df["category"] = df["category"].apply(
        lambda x: x[0] if isinstance(x, list) and x else x if isinstance(x, str) else "Uncategorized"
    )


    # Add source column for display
    df["source"] = df["source"].fillna("bank")  # Mark missing sources as bank transactions

    # 1. Spending by Category
    st.subheader("🧾 Spending by Category")
    category_totals = df.groupby("category")["amount"].sum().reset_index()
    category_totals = category_totals.sort_values("amount", ascending=False)

    chart = alt.Chart(category_totals).mark_bar().encode(
        x=alt.X("category", sort="-y", title="Category"),
        y=alt.Y("amount", title="Amount ($)"),
        tooltip=[
            alt.Tooltip("category", title="Category"),
            alt.Tooltip("amount", title="Amount", format="$.2f")
        ]
    ).properties(width=700)

    st.altair_chart(chart, use_container_width=True)

    # 2. Spending Over Time
    st.subheader("📅 Spending Over Time")
    daily_spending = df.groupby("date")["amount"].sum().reset_index()

    # Create the line chart with enhanced interactivity
    line_chart = alt.Chart(daily_spending).mark_line(point=True).encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("amount:Q", title="Amount ($)"),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("amount:Q", title="Amount", format="$.2f")
        ]
    ).properties(
        width=700,
        height=400
    ).interactive()  # Make the chart interactive

    st.altair_chart(line_chart, use_container_width=True)

    # 3. Raw Transaction Table with proper sorting
    st.subheader("📄 Transaction Table")
    
    # Format the display data
    display_df = df[["date", "name", "amount", "category", "source"]].copy()
    # Format date to a more readable format
    display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d %H:%M")
    display_df["amount"] = display_df["amount"].map("${:,.2f}".format)
    display_df["source"] = display_df["source"].map({"manual_upload": "📷 Receipt", "bank": "🏦 Bank"})
    
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
            date_df["date"] = date_df["date"].dt.strftime("%Y-%m-%d")
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