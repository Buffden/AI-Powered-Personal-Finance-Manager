import streamlit as st
from backend.utils.notifications import detect_recurring_payments, generate_bill_reminders
from datetime import datetime

st.set_page_config(page_title="Notifications", layout="centered")
st.title("🔔 Budget Alerts & Bill Reminders")

# 💰 Budget alerts
if 'notifications' in st.session_state and st.session_state['notifications']:
    st.subheader("⚠️ Budget Overspending Alerts")
    for note in st.session_state['notifications']:
        st.warning(note["message"])
else:
    st.success("✅ No budget alerts!")

# 📅 Recurring bill reminders
if 'transactions' in st.session_state:
    st.subheader("📅 Upcoming Bills (within 5 days)")

    recurring = detect_recurring_payments(st.session_state['transactions'])
    reminders = generate_bill_reminders(recurring)

    if reminders:
        for r in reminders:
            st.info(r["message"])
    else:
        st.success("✅ No upcoming recurring bills!")
else:
    st.info("No transactions loaded.")


