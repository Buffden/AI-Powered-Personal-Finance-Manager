from datetime import datetime, timedelta, date
from collections import defaultdict
from calendar import monthrange
import re
import streamlit as st
from backend.utils.email import send_email_reminder

# --- STEP 1: Budget Overspending Alerts ---
def generate_notifications(overspending_summary, year_month):
    notifications = []
    for category, exceeded_amount in overspending_summary.items():
        notification = {
            "month": year_month,
            "category": category,
            "message": f"⚠️ You exceeded your budget for {category} by ${exceeded_amount:.2f} in {year_month}."
        }
        notifications.append(notification)
    return notifications

# --- Normalize merchant name (strip special chars & lowercase) ---
def normalize_name(name):
    return re.sub(r'[^a-z]', '', name.lower())

# --- STEP 2: Detect Recurring Transactions ---
def detect_recurring_transactions(transactions):
    recurring = []

    grouped = defaultdict(list)
    for tx in transactions:
        try:
            norm_name = normalize_name(tx["name"])
            amount = round(float(tx["amount"]), 2)
            tx_date = datetime.strptime(tx["date"], "%Y-%m-%d").date()
            key = (norm_name, amount)
            grouped[key].append((tx_date, tx))
        except:
            continue

    for (norm_name, amount), entries in grouped.items():
        if len(entries) < 3:
            continue

        entries.sort(key=lambda x: x[0])
        day_set = set(entry[0].day for entry in entries)

        if len(day_set) == 1:
            recurring_day = entries[-1][0].day
            today = date.today()
            year = today.year
            month = today.month

            if today.day < recurring_day:
                next_due_month = month
                next_due_year = year
            else:
                next_due_month = month + 1
                next_due_year = year
                if next_due_month > 12:
                    next_due_month = 1
                    next_due_year += 1

            max_day = monthrange(next_due_year, next_due_month)[1]
            due_day = min(recurring_day, max_day)
            next_due = date(next_due_year, next_due_month, due_day)

            recurring.append({
                "name": entries[-1][1]["name"],
                "category": entries[-1][1].get("category", ["Other"])[0],
                "amount": amount,
                "next_due": next_due
            })

    return recurring

# --- STEP 3: Generate Sorted, Multi-Month Reminders ---
def generate_bill_reminders(recurring_candidates, days_ahead=5):
    today = date.today()
    end_date = today + timedelta(days=days_ahead)
    reminders = []

    for item in recurring_candidates:
        due_date = item["next_due"]

        while due_date <= end_date:
            if due_date >= today:
                reminders.append({
                    "name": item["name"],
                    "category": item["category"],
                    "amount": item["amount"],
                    "due_date": due_date.isoformat(),
                    "message": f"📅 Recurring payment: **{item['name']}** (${item['amount']}) occurs monthly on day {due_date.day}. Next due: {due_date}."
                })

            year, month = due_date.year, due_date.month + 1
            if month > 12:
                month = 1
                year += 1

            max_day = monthrange(year, month)[1]
            next_day = min(item["next_due"].day, max_day)
            due_date = date(year, month, next_day)

    reminders.sort(key=lambda r: r["due_date"])
    return reminders

# --- STEP 4: Send Emails Only Once & Keep Visible Log ---
def auto_email_reminders(recurring_candidates, user_email):
    today = date.today()
    reminders = generate_bill_reminders(recurring_candidates, days_ahead=5)

    if "sent_emails" not in st.session_state:
        st.session_state.sent_emails = set()

    if "sent_email_log" not in st.session_state:
        st.session_state.sent_email_log = []

    for r in reminders:
        reminder_key = f"{user_email}_{r['name']}_{r['due_date']}"

        if reminder_key in st.session_state.sent_emails:
            continue

        subject = f"📅 Upcoming Bill Reminder: {r['name']}"
        body = (
            f"Hello,\n\n"
            f"This is a reminder that your recurring payment for **{r['name']}** "
            f"(${r['amount']}) is due on {r['due_date']}.\n\n"
            "Stay on top of your finances! 💸\n\n"
            "-- Your AI Finance Manager"
        )

        success = send_email_reminder(user_email, subject, body)

        if success:
            st.session_state.sent_emails.add(reminder_key)
            st.session_state.sent_email_log.append({
                "name": r["name"],
                "amount": r["amount"],
                "due_date": r["due_date"],
                "message": f"📧 Email reminder sent for **{r['name']}** (${r['amount']}) due on {r['due_date']}."
            })
