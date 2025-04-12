import streamlit as st
import requests
from backend.utils.notifications import (
    detect_recurring_transactions,
    generate_bill_reminders,
    filter_important_recurring
)
from datetime import datetime


def show_bill_reminders():
    st.title("🔔 Budget Alerts & Bill Reminders")

    # 💰 Budget overspending alerts
    if 'notifications' in st.session_state and st.session_state['notifications']:
        st.subheader("⚠️ Budget Overspending Alerts")
        for note in st.session_state['notifications']:
            st.warning(note["message"])
    else:
        st.success("✅ No budget alerts!")

    # 📅 Recurring bill reminders
    if 'transactions' in st.session_state and st.session_state['transactions']:
        st.subheader("📅 Upcoming Bills")

        # 🔁 Days-ahead slider
        days_ahead = st.slider("Show recurring bills due in the next X days:", min_value=1, max_value=30, value=5)

        # 🚀 Detect recurring payments and reminders
        # recurring = detect_recurring_transactions(st.session_state['transactions'])
        if 'recurring_static' not in st.session_state:
            recurring_candidates = detect_recurring_transactions(st.session_state['transactions'])
            filtered = filter_important_recurring(recurring_candidates)
            st.session_state['recurring_static'] = filtered

        reminders = generate_bill_reminders(st.session_state['recurring_static'], days_ahead=days_ahead)



        st.subheader(f"🔁 Recurring Payments (due within {days_ahead} days)")
        if reminders:
            for r in reminders:
                st.info(r["message"])
        else:
            st.success(f"✅ No recurring bills due in the next {days_ahead} days.")
    else:
        st.info("No transactions loaded.")