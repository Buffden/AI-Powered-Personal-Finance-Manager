import streamlit as st
from backend.utils.budget import BudgetTracker
from backend.utils.notifications import generate_notifications
import matplotlib.pyplot as plt
import numpy as np
import datetime
from dateutil import parser as date_parser

st.set_page_config(page_title="Budget Tracker", layout="centered")
st.title("📊 Budget Tracker - Monthly Overspending")

# Ensure transactions exist
if 'transactions' not in st.session_state:
    st.warning("No transactions found. Please fetch transactions from the Home page first.")
else:
    transactions = st.session_state['transactions']

    # Initialize budget tracker
    if 'budget_tracker' not in st.session_state:
        st.session_state['budget_tracker'] = BudgetTracker()

    budget_tracker = st.session_state['budget_tracker']

    # 📅 Extract unique months from transactions
    all_months = sorted(set(
        date_parser.parse(tx['date']).strftime("%Y-%m") for tx in transactions
    ))

    selected_month = st.selectbox("Select Month", all_months, index=len(all_months) - 1)
    st.subheader(f"Set Budget Limits for {selected_month}")

    # Unique categories
    categories = list(set(tx.get('category', ['Uncategorized'])[0] for tx in transactions))

    # Set or reuse limits per category for selected month
    for category in categories:
        limit_key = f"{selected_month}_{category}"

        if limit_key not in st.session_state:
            existing_limit = budget_tracker.monthly_limits[selected_month].get(category, 0.0)
            st.session_state[limit_key] = existing_limit

        limit = st.number_input(
            f"{category} Limit ($)",
            min_value=0.0,
            step=10.0,
            key=limit_key
        )

        budget_tracker.set_monthly_limit(selected_month, category, limit)

    # 🔍 Analyze button
    if st.button("📈 Analyze Spending"):
        # Filter transactions for selected month
        filtered_tx = [
            tx for tx in transactions
            if date_parser.parse(tx['date']).strftime("%Y-%m") == selected_month
        ]

        budget_tracker.track_monthly_expenses(filtered_tx)
        overspending = budget_tracker.get_overspending_summary(selected_month)
        summary = budget_tracker.get_monthly_summary(selected_month)

        # Store notifications
        if overspending:
            if 'notifications' not in st.session_state:
                st.session_state['notifications'] = []
            new_notes = generate_notifications(overspending, selected_month)
            st.session_state['notifications'].extend(new_notes)

        # Prepare chart data
        categories = [item['category'] for item in summary]
        spent = [item['spent'] for item in summary]
        limits = [item['limit'] for item in summary]
        x = np.arange(len(categories))
        width = 0.35

        fig, ax = plt.subplots(figsize=(12, 6))

        bar_colors = ['crimson' if spent[i] > limits[i] else 'royalblue' for i in range(len(categories))]

        bars_spent = ax.bar(x - width/2, spent, width, label='Spent', color=bar_colors)
        bars_limit = ax.bar(x + width/2, limits, width, label='Limit', color='lightgray')

        for i in range(len(categories)):
            if spent[i] > limits[i]:
                ax.text(
                    x[i], spent[i] + max(spent) * 0.02,
                    f"Over by ${spent[i] - limits[i]:.2f}",
                    ha='center', color='red', fontsize=10, fontweight='bold'
                )

        ax.set_xlabel("Category", fontsize=12)
        ax.set_ylabel("Amount ($)", fontsize=12)
        ax.set_title(f"📊 Budget vs Spending — {selected_month}", fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=15)
        ax.legend(title="Legend", loc="upper right", frameon=True)

        st.pyplot(fig)
