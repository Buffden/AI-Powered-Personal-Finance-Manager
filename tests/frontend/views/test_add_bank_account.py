import unittest
from unittest.mock import MagicMock, patch
from io import StringIO
import frontend.views.AddBankAccount as aba


class TestProcessUploadedStatement(unittest.TestCase):
    @patch("frontend.views.AddBankAccount.st")
    def test_valid_csv_upload(self, mock_st):
        mock_st.session_state = {}

        csv = StringIO("vendor,amount ($),category\nStarbucks,10.50,Coffee\nAmazon,25.99,Shopping")
        csv.name = "test.csv"
        csv.type = "text/csv"

        result = aba.process_uploaded_statement(csv)

        self.assertEqual(result, 2)
        self.assertIn("transactions", mock_st.session_state)
        self.assertEqual(mock_st.session_state["transactions"][0]["name"], "Starbucks")

    @patch("frontend.views.AddBankAccount.st")
    def test_missing_category_column(self, mock_st):
        mock_st.session_state = {}

        # Remove 'category' column entirely
        csv = StringIO("vendor,amount ($)\nStarbucks,10.50\nAmazon,25.99")
        csv.name = "test.csv"
        csv.type = "text/csv"

        result = aba.process_uploaded_statement(csv)

        self.assertEqual(len(mock_st.session_state["transactions"]), 2)
        self.assertEqual(mock_st.session_state["transactions"][1]["name"], "Amazon")

    @patch("frontend.views.AddBankAccount.st")
    def test_invalid_file_type(self, mock_st):
        bad_file = StringIO("This won't matter")
        bad_file.type = "application/pdf"
        bad_file.name = "file.pdf"

        result = aba.process_uploaded_statement(bad_file)
        self.assertEqual(result, 0)

    @patch("frontend.views.AddBankAccount.st")
    def test_csv_parsing_error(self, mock_st):
        file = StringIO("bad,csv")
        file.name = "bad.csv"
        file.type = "text/csv"

        with patch("pandas.read_csv", side_effect=Exception("parse error")):
            result = aba.process_uploaded_statement(file)
            self.assertEqual(result, 0)
            mock_st.error.assert_called_once()

class TestAddBankToState(unittest.TestCase):
    @patch("frontend.views.AddBankAccount.st")
    def test_add_new_bank_and_accounts(self, mock_st):
        # Use MagicMock for attribute-style access
        mock_st.session_state = MagicMock()
        mock_st.session_state.__contains__.side_effect = lambda key: False
        mock_st.session_state.__getitem__.side_effect = lambda key: {} if key in ["linked_banks", "selected_accounts"] else None
        mock_st.session_state.__setitem__.side_effect = lambda key, value: setattr(mock_st.session_state, key, value)

        institution_name = "Mock Bank"
        institution_id = "mock123"
        accounts = [
            {"account_id": "acc1", "name": "Checking"},
            {"account_id": "acc2", "name": "Savings"}
        ]

        aba.add_bank_to_state(institution_name, institution_id, accounts)

        self.assertTrue(hasattr(mock_st.session_state, "linked_banks"))
        self.assertEqual(
            mock_st.session_state.linked_banks[institution_id]["institution_name"],
            "Mock Bank"
        )
        self.assertTrue(hasattr(mock_st.session_state, "selected_accounts"))
        self.assertEqual(
            mock_st.session_state.selected_accounts[institution_id],
            {"acc1": False, "acc2": False}
        )

    @patch("frontend.views.AddBankAccount.st")
    def test_update_existing_bank(self, mock_st):
        mock_st.session_state = MagicMock()
        mock_st.session_state.linked_banks = {
            "mock123": {
                "institution_name": "Old Bank",
                "institution_id": "mock123",
                "accounts": [{"account_id": "old_acc"}]
            }
        }
        mock_st.session_state.selected_accounts = {
            "mock123": {"old_acc": True}
        }

        new_accounts = [{"account_id": "acc1", "name": "New"}]

        aba.add_bank_to_state("New Bank", "mock123", new_accounts)

        self.assertEqual(
            mock_st.session_state.linked_banks["mock123"]["institution_name"],
            "New Bank"
        )
        self.assertEqual(
            list(mock_st.session_state.selected_accounts["mock123"].keys()),
            ["acc1"]
        )

if __name__ == "__main__":
    unittest.main()
