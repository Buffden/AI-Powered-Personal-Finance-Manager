import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Setup path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from frontend.views import BudgetTracker as bt


class TestCategorizeTransactions(unittest.TestCase):
    @patch("frontend.views.BudgetTracker.Config.get_openai_api_key", return_value="fake-key")
    @patch("frontend.views.BudgetTracker.openai.ChatCompletion.create")
    @patch("frontend.views.BudgetTracker.st")
    def test_valid_transactions_categorized(self, mock_st, mock_create, mock_key):
        # Mock response from OpenAI
        mock_create.return_value.choices = [MagicMock(message=MagicMock(content='''{
            "categories": {
                "Food": {
                    "transactions": [
                        {"name": "Starbucks", "amount": 10.0, "date": "2023-07-01"}
                    ],
                    "suggested_budget": 50,
                    "description": "Covers small food purchases"
                }
            }
        }'''))]

        transactions = [
            {"name": "Starbucks", "amount": "10.0", "date": "2023-07-01", "category": ["Coffee"]}
        ]

        result = bt.categorize_transactions(transactions)
        self.assertIn("Food", result)
        self.assertEqual(result["Food"]["suggested_budget"], 50)
        self.assertEqual(result["Food"]["transactions"][0]["name"], "Starbucks")

    @patch("frontend.views.BudgetTracker.Config.get_openai_api_key", return_value="fake-key")
    @patch("frontend.views.BudgetTracker.openai.ChatCompletion.create")
    @patch("frontend.views.BudgetTracker.st")
    def test_openai_returns_invalid_json(self, mock_st, mock_create, mock_key):
        mock_create.return_value.choices = [MagicMock(message=MagicMock(content='not a json'))]

        result = bt.categorize_transactions([{"name": "X", "amount": "1", "date": "2023-07-01"}])
        self.assertEqual(result, {})
        mock_st.error.assert_called_once()

    @patch("frontend.views.BudgetTracker.Config.get_openai_api_key", return_value="fake-key")
    @patch("frontend.views.BudgetTracker.openai.ChatCompletion.create", side_effect=Exception("OpenAI error"))
    @patch("frontend.views.BudgetTracker.st")
    def test_openai_raises_exception(self, mock_st, mock_create, mock_key):
        result = bt.categorize_transactions([{"name": "X", "amount": "1", "date": "2023-07-01"}])
        self.assertEqual(result, {})
        mock_st.error.assert_called_once()


class TestAnalyzeTransactionsForBudgets(unittest.TestCase):
    @patch("frontend.views.BudgetTracker.Config.get_openai_api_key", return_value="fake-key")
    @patch("frontend.views.BudgetTracker.openai.ChatCompletion.create")
    @patch("frontend.views.BudgetTracker.st")
    def test_budget_suggestions_parsed_correctly(self, mock_st, mock_create, mock_key):
        mock_create.return_value.choices = [MagicMock(message=MagicMock(content="""
            Food: $150
            Rent: $1200
        """))]

        categorized = {
            "Food": {"transactions": [], "suggested_budget": 0},
            "Rent": {"transactions": [], "suggested_budget": 0},
        }

        result = bt.analyze_transactions_for_budgets(categorized)
        self.assertEqual(result["Food"], 150)
        self.assertEqual(result["Rent"], 1200)

    @patch("frontend.views.BudgetTracker.Config.get_openai_api_key", return_value="fake-key")
    @patch("frontend.views.BudgetTracker.openai.ChatCompletion.create", side_effect=Exception("Boom"))
    @patch("frontend.views.BudgetTracker.st")
    def test_analyze_budget_openai_failure(self, mock_st, mock_create, mock_key):
        result = bt.analyze_transactions_for_budgets({})
        self.assertEqual(result, {})
        mock_st.error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
