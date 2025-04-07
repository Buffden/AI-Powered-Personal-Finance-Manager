import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Setup path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from frontend.views import BudgetTracker as bt


class TestCategorizeTransactions(unittest.TestCase):
    @patch("frontend.views.BudgetTracker.Config.get_openai_api_key", return_value="fake-key")
    @patch("frontend.views.BudgetTracker.OpenAI")
    @patch("frontend.views.BudgetTracker.st")
    def test_valid_transactions_categorized(self, mock_st, mock_openai, mock_key):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content='''{
                "categories": {
                    "Food": {
                        "transactions": [
                            {"name": "Starbucks", "amount": 10.0, "date": "2023-07-01"}
                        ],
                        "suggested_budget": 50,
                        "description": "Covers small food purchases"
                    }
                }
            }'''))
        ]

        transactions = [
            {"name": "Starbucks", "amount": "10.0", "date": "2023-07-01", "category": ["Coffee"]}
        ]

        result = bt.categorize_transactions(transactions)
        self.assertIn("Food", result)
        self.assertEqual(result["Food"]["suggested_budget"], 50)
        self.assertEqual(result["Food"]["transactions"][0]["name"], "Starbucks")

    @patch("frontend.views.BudgetTracker.Config.get_openai_api_key", return_value="fake-key")
    @patch("frontend.views.BudgetTracker.OpenAI")
    @patch("frontend.views.BudgetTracker.st")
    def test_openai_returns_invalid_json(self, mock_st, mock_openai, mock_key):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content='not a json'))
        ]

        result = bt.categorize_transactions([{"name": "X", "amount": "1", "date": "2023-07-01"}])
        self.assertEqual(result, {})
        mock_st.error.assert_called_once()

    @patch("frontend.views.BudgetTracker.Config.get_openai_api_key", return_value="fake-key")
    @patch("frontend.views.BudgetTracker.OpenAI")
    @patch("frontend.views.BudgetTracker.st")
    def test_openai_raises_exception(self, mock_st, mock_openai, mock_key):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("OpenAI error")

        result = bt.categorize_transactions([{"name": "X", "amount": "1", "date": "2023-07-01"}])
        self.assertEqual(result, {})
        mock_st.error.assert_called_once()

class TestAnalyzeTransactionsForBudgets(unittest.TestCase):
    @patch("frontend.views.BudgetTracker.Config.get_openai_api_key", return_value="fake-key")
    @patch("frontend.views.BudgetTracker.OpenAI")
    @patch("frontend.views.BudgetTracker.st")
    def test_budget_suggestions_parsed_correctly(self, mock_st, mock_openai, mock_key):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="Food: $150\nRent: $1200"))
        ]

        categorized = {
            "Food": {"transactions": [], "suggested_budget": 0},
            "Rent": {"transactions": [], "suggested_budget": 0},
        }

        result = bt.analyze_transactions_for_budgets(categorized)
        self.assertEqual(result["Food"], 150)
        self.assertEqual(result["Rent"], 1200)

    @patch("frontend.views.BudgetTracker.Config.get_openai_api_key", return_value="fake-key")
    @patch("frontend.views.BudgetTracker.OpenAI")
    @patch("frontend.views.BudgetTracker.st")
    def test_analyze_budget_openai_failure(self, mock_st, mock_openai, mock_key):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Boom")

        result = bt.analyze_transactions_for_budgets({})
        self.assertEqual(result, {})
        mock_st.error.assert_called_once()

class TestShowBudgetTracker(unittest.TestCase):
    @patch("frontend.views.BudgetTracker.show_account_selector", return_value=[])
    @patch("frontend.views.BudgetTracker.st")
    def test_no_accounts_selected(self, mock_st, mock_selector):
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.stop.side_effect = Exception("Streamlit stopped")
        
        with self.assertRaises(Exception) as ctx:
            bt.show_budget_tracker()
        self.assertIn("Streamlit stopped", str(ctx.exception))
        mock_st.warning.assert_called_with("⚠️ Please select at least one account to view budget tracking.")

    @patch("frontend.views.BudgetTracker.show_account_selector", return_value=["acc_123"])
    @patch("frontend.views.BudgetTracker.st")
    def test_no_transactions_in_session_state(self, mock_st, mock_selector):
        mock_st.session_state = {}  # No 'transactions' key
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.stop.side_effect = Exception("Streamlit stopped")

        with self.assertRaises(Exception) as ctx:
            bt.show_budget_tracker()

        mock_st.warning.assert_called_with("⚠️ Please fetch transactions from the Home page first.")
        self.assertIn("Streamlit stopped", str(ctx.exception))

    @patch("frontend.views.BudgetTracker.show_account_selector", return_value=["acc_123"])
    @patch("frontend.views.BudgetTracker.st")
    def test_no_transactions_for_selected_account(self, mock_st, mock_selector):
        mock_st.session_state = {
            "transactions": [{"account_id": "other_acc", "date": "2023-08-01"}]  # Different account
        }
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.stop.side_effect = Exception("Streamlit stopped")

        with self.assertRaises(Exception) as ctx:
            bt.show_budget_tracker()

        mock_st.warning.assert_called_with("No transactions found for selected accounts.")
        self.assertIn("Streamlit stopped", str(ctx.exception))

    @patch("frontend.views.BudgetTracker.BudgetTracker")
    @patch("frontend.views.BudgetTracker.show_account_selector", return_value=["acc_123"])
    @patch("frontend.views.BudgetTracker.st")
    def test_month_selector_and_initialization(self, mock_st, mock_selector, mock_tracker_class):
        tracker_instance = MagicMock()
        tracker_instance.get_overspending_summary.return_value = {}
        tracker_instance.get_monthly_summary.return_value = [
            {"category": "TestCat", "spent": 5.0, "limit": 100}
        ]
        mock_tracker_class.return_value = tracker_instance

        # Fully populate session_state to avoid KeyErrors
        mock_st.session_state = {
            "transactions": [
                {"account_id": "acc_123", "date": "2023-08-01", "name": "X", "amount": 5.0}
            ],
            "categorized_transactions": {},
            "previous_month": None
        }

        mock_st.selectbox.return_value = "2023-08"
        mock_st.spinner.return_value.__enter__.return_value = None
        mock_st.spinner.return_value.__exit__.return_value = None
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.number_input.return_value = 100
        mock_st.altair_chart = MagicMock()
        mock_st.subheader = MagicMock()
        mock_st.caption = MagicMock()
        mock_st.dataframe = MagicMock()
        mock_st.button.side_effect = [False, False]  # For Analyze and AI Suggestion buttons

        # Patch categorize_transactions to avoid actual OpenAI call
        with patch("frontend.views.BudgetTracker.categorize_transactions", return_value={
            "TestCat": {
                "transactions": [{"name": "X", "amount": 5.0, "date": "2023-08-01"}],
                "suggested_budget": 100
            }
        }):
            bt.show_budget_tracker()

        assert "2023-08" in mock_st.session_state['categorized_transactions']
        tracker_instance.set_monthly_limit.assert_called_with("2023-08", "TestCat", 100)

if __name__ == "__main__":
    unittest.main()
