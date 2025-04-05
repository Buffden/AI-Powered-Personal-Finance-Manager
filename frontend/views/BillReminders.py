import streamlit as st
from backend.utils.notifications import (
    detect_recurring_transactions,
    generate_bill_reminders,
    auto_email_reminders
)
from datetime import datetime

def show_bill_reminders():
    st.title("🔔 Budget Alerts & Bill Reminders")

    if 'notifications' in st.session_state and st.session_state['notifications']:
        st.subheader("⚠️ Budget Overspending Alerts")
        for note in st.session_state['notifications']:
            st.warning(note["message"])
    else:
        st.success("✅ No budget alerts!")

    if 'transactions' in st.session_state and st.session_state['transactions']:
        st.subheader("📅 Upcoming Bills")

        # User enters email manually for now
        user_email = st.text_input("📧 Enter your email to receive reminders:", value="demo@example.com")

        # Slider for date range
        days_ahead = st.slider("Show recurring bills due in the next X days:", min_value=1, max_value=90, value=5)

        # Detect & show reminders
        recurring = detect_recurring_transactions(st.session_state['transactions'])
        reminders = generate_bill_reminders(recurring, days_ahead=days_ahead)

        st.subheader(f"🔁 Recurring Payments (due within {days_ahead} days)")
        if reminders:
            for r in reminders:
                st.info(r["message"])
        else:
            st.success(f"✅ No recurring bills due in the next {days_ahead} days.")

        # Send emails only once & persist in UI
        if user_email:
            auto_email_reminders(recurring, user_email)

        if st.session_state.get("sent_email_log"):
            st.subheader("📨 Email Reminders Sent This Session")
            for note in st.session_state.sent_email_log:
                st.success(note["message"])
    else:
        st.info("No transactions loaded.")
