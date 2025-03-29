import datetime
from collections import defaultdict

class BudgetTracker:
    def __init__(self):
        # Store monthly limits
        self.monthly_limits = defaultdict(lambda: defaultdict(float)) # {'2025-03': {'Travel': 200, ...}}
        self.monthly_expenses = defaultdict(lambda: defaultdict(float))

    def set_monthly_limit(self, year_month, category, limit):
        self.monthly_limits[year_month][category] = limit
        
    def reset_month(self, year_month):
        self.monthly_expenses[year_month] = defaultdict(float)

    def track_monthly_expenses(self, transactions):
        for tx in transactions:
            # Clean and trim date string
            cleaned_date = tx['date'].strip().replace(" GMT", "")
            try:
                date = datetime.datetime.strptime(cleaned_date, "%a, %d %b %Y %H:%M:%S")
            except ValueError as e:
                raise ValueError(f"❌ Failed to parse date '{tx['date']}' - expected format '%a, %d %b %Y %H:%M:%S', after cleaning got: '{cleaned_date}'") from e

            year_month = date.strftime("%Y-%m")

            # ✅ Robust category extraction
            raw_category = tx.get('category', ['Uncategorized'])

            if isinstance(raw_category, list) and raw_category:
                category = raw_category[0]
            elif isinstance(raw_category, str):
                category = raw_category
            else:
                category = "Uncategorized"

            # ✅ Ensure outer and inner dicts exist (full safety)
            if year_month not in self.monthly_expenses:
                self.monthly_expenses[year_month] = defaultdict(float)

            self.monthly_expenses[year_month][category] += abs(float(tx['amount']))

    def get_overspending_summary(self, year_month):
        overspending = {}
        for category, spent in self.monthly_expenses[year_month].items():
            limit = self.monthly_limits[year_month].get(category, None)
            if limit and spent > limit:
                overspending[category] = spent - limit
        return overspending

    def get_monthly_summary(self, year_month):
        summary = []
        categories = set(self.monthly_expenses[year_month].keys()).union(self.monthly_limits[year_month].keys())
        for category in categories:
            spent = self.monthly_expenses[year_month].get(category, 0.0)
            limit = self.monthly_limits[year_month].get(category, 0.0)
            summary.append({'category': category, 'spent': spent, 'limit': limit})
        return summary
