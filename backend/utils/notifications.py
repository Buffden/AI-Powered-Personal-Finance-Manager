from dateutil import parser as date_parser
from datetime import datetime, timedelta
from collections import defaultdict

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

def detect_recurring_payments(transactions):
    recurring = defaultdict(list)

    for tx in transactions:
        key = (tx.get("name", ""), tx.get("category", ["Uncategorized"])[0])
        recurring[key].append({
            "amount": abs(tx["amount"]),
            "date": date_parser.parse(tx["date"])
        })

    candidates = []

    for (name, category), tx_list in recurring.items():
        if len(tx_list) < 3:
            continue  # At least 3 payments needed for pattern

        # Sort by date
        tx_list.sort(key=lambda x: x["date"])

        # Check for ~monthly interval
        intervals = [
            (tx_list[i + 1]["date"] - tx_list[i]["date"]).days
            for i in range(len(tx_list) - 1)
        ]
        avg_interval = sum(intervals) / len(intervals)

        if 27 <= avg_interval <= 33:
            recent_date = tx_list[-1]["date"]
            avg_amount = sum(tx["amount"] for tx in tx_list) / len(tx_list)
            candidates.append({
                "name": name,
                "category": category,
                "last_paid": recent_date,
                "average_amount": round(avg_amount, 2),
                "next_due": recent_date + timedelta(days=30)
            })

    return candidates

def generate_bill_reminders(recurring_candidates):
    today = datetime.today().date()
    reminders = []

    for item in recurring_candidates:
        due_date = item["next_due"].date()
        if 0 <= (due_date - today).days <= 5:
            reminders.append({
                "name": item["name"],
                "category": item["category"],
                "due_date": due_date.isoformat(),
                "message": f"📅 Upcoming bill: **{item['name']}** (${item['average_amount']}) is due on {due_date}."
            })

    return reminders
