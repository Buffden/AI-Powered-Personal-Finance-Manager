from collections import defaultdict
from datetime import datetime, timedelta, date
from calendar import monthrange
from dateutil import parser as date_parser
import re


# --- STEP 1: Budget Overspending Alerts ---
def generate_notifications(overspending_summary, year_month):
    seen_messages = set()
    notifications = []

    for category, exceeded_amount in overspending_summary.items():
        message = f"⚠️ You exceeded your budget for {category} by ${exceeded_amount:.2f} in {year_month}."
        if message not in seen_messages:
            notifications.append({
                "month": year_month,
                "category": category,
                "message": message
            })
            seen_messages.add(message)

    return notifications


def normalize_name(name):
    return re.sub(r'[^a-z]', '', name.lower())

def detect_recurring_transactions(transactions):
    recurring = []
    grouped = defaultdict(list)

    for tx in transactions:
        try:
            norm_name = normalize_name(tx["name"])
            amount = round(float(tx["amount"]), 2)

            # ❌ Skip negative or zero transactions (credits/refunds)
            if amount <= 0:
                continue

            tx_date = date_parser.parse(tx["date"]).date()
            key = (norm_name, amount)
            grouped[key].append((tx_date, tx))
        except:
            continue

    for (norm_name, amount), entries in grouped.items():
        if len(entries) < 3:
            continue

        entries.sort(key=lambda x: x[0])
        dates = [entry[0] for entry in entries]
        months_seen = set((d.year, d.month) for d in dates)

        # Require recurrence in at least 3 different months
        if len(months_seen) < 3:
            continue

        avg_day = sum(d.day for d in dates) / len(dates)

        # Allow ±3 day tolerance around the average billing day
        if all(abs(d.day - avg_day) <= 3 for d in dates):
            last_date = dates[-1]
            next_month = last_date.month + 1
            next_year = last_date.year + (1 if next_month > 12 else 0)
            next_month = 1 if next_month > 12 else next_month
            max_day = monthrange(next_year, next_month)[1]
            next_day = min(round(avg_day), max_day)
            next_due = date(next_year, next_month, next_day)

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

        # Only include if due within range
        if today <= due_date <= end_date:
            reminders.append({
                "name": item["name"],
                "category": item["category"],
                "amount": item["amount"],
                "due_date": due_date.isoformat(),
                "message": f"📅 Recurring payment: **{item['name']}** (${item['amount']}) is due on {due_date}."
            })

    # Sort reminders by due date
    reminders.sort(key=lambda r: r["due_date"])
    return reminders   

from openai import OpenAI
from backend.utils.config import Config

def filter_important_recurring(recurring_candidates):
    client = OpenAI(api_key=Config.get_openai_api_key())

    # Format the recurring transactions as plain text
    formatted_list = "\n".join(
        f"- {r['name']} | ${r['amount']} | Due: {r['next_due']}"
        for r in recurring_candidates
    )

    prompt = f"""
You are a financial assistant reviewing a user's recurring transactions.

From the list below, identify and return ONLY the important recurring financial obligations, such as:
- rent or mortgage payments
- credit card or loan payments
- insurance
- utilities (electricity, water, gas, internet)
- mobile phone bills
- subscriptions (Netflix, Spotify, gym, etc.)

Ignore food, dining, fast food, coffee shop.

Just return the names of important recurring transactions, as a simple list.

Here is the list to review:

{formatted_list}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a smart financial assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        # Extract names line-by-line from the AI response
        content = response.choices[0].message.content
        important_names = set()
        for line in content.splitlines():
            if line.startswith("- "):
                name = line[2:].strip()
                if name:
                    important_names.add(name.lower())

        # Match back against original recurring candidates
        return [
            tx for tx in recurring_candidates
            if tx["name"].lower() in important_names
        ]

    except Exception as e:
        print("⚠️ AI filtering failed:", e)
        return recurring_candidates  # fallback if error
