import streamlit as st
import requests
from backend.utils.notifications import (
    detect_recurring_transactions,
    generate_bill_reminders,
    auto_email_reminders
)
from datetime import datetime


def fetch_user_email():
    """Fetch email from Plaid backend, fallback if not found."""
    try:
        res = requests.get("http://localhost:5050/api/plaid/get_user_email")
        if res.status_code == 200:
            return res.json().get("email", "fallback_user@example.com")
    except Exception as e:
        print(f"Error fetching email: {e}")
    return "fallback_user@example.com"


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
        days_ahead = st.slider("Show recurring bills due in the next X days:", min_value=1, max_value=90, value=5)

        # 🚀 Detect recurring payments and reminders
        recurring = detect_recurring_transactions(st.session_state['transactions'])
        reminders = generate_bill_reminders(recurring, days_ahead=days_ahead)

        st.subheader(f"🔁 Recurring Payments (due within {days_ahead} days)")
        if reminders:
            for r in reminders:
                st.info(r["message"])
        else:
            st.success(f"✅ No recurring bills due in the next {days_ahead} days.")

        # ✉️ Fetch email from backend and send reminders
        user_email = fetch_user_email()
        auto_email_reminders(recurring, user_email)

        # 📨 Show all emails sent in this session
        if st.session_state.get("sent_email_log"):
            st.subheader("📨 Email Reminders Sent This Session")
            for note in st.session_state.sent_email_log:
                st.success(note["message"])
    else:
        st.info("No transactions loaded.")
