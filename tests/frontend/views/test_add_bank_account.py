import unittest
from unittest.mock import MagicMock, patch
from io import StringIO, BytesIO
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

    @patch("frontend.views.AddBankAccount.st")
    def test_empty_csv_file(self, mock_st):
        mock_st.session_state = {}

        empty_csv = StringIO("")
        empty_csv.name = "empty.csv"
        empty_csv.type = "text/csv"

        result = aba.process_uploaded_statement(empty_csv)
        self.assertEqual(result, 0)
        mock_st.error.assert_called_once_with("Failed to read CSV: No columns to parse from file")

    @patch("frontend.views.AddBankAccount.st")
    def test_large_csv_file(self, mock_st):
        mock_st.session_state = {}

        large_csv = StringIO("\n".join(["vendor,amount ($),category"] + [f"Vendor{i},10.00,Category{i}" for i in range(1000)]))
        large_csv.name = "large.csv"
        large_csv.type = "text/csv"

        result = aba.process_uploaded_statement(large_csv)
        self.assertEqual(result, 1000)
        self.assertEqual(len(mock_st.session_state["transactions"]), 1000)

    @patch("frontend.views.AddBankAccount.st")
    def test_invalid_csv_format(self, mock_st):
        mock_st.session_state = {}

        invalid_csv = BytesIO(b"Not a CSV content")
        invalid_csv.name = "invalid.csv"
        invalid_csv.type = "text/csv"

        result = aba.process_uploaded_statement(invalid_csv)
        self.assertEqual(result, 0)
        mock_st.error.assert_called_once_with("Missing required columns.")

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

    @patch("frontend.views.AddBankAccount.requests.post")
    @patch("frontend.views.AddBankAccount.show_account_selector")
    @patch("frontend.views.AddBankAccount.st")
    def test_add_bank_to_state_new_bank(self, mock_st, mock_show_account_selector, mock_requests_post):
        # Mock session_state with MagicMock to simulate attribute-style access
        mock_st.session_state = MagicMock()
        mock_st.session_state.linked_banks = {}
        mock_st.session_state.selected_accounts = {"mock123": {"acc1": True}}  # Ensure at least one account is selected

        # Mock show_account_selector to return selected accounts
        mock_show_account_selector.return_value = ["acc1"]

        # Mock tabs
        mock_st.tabs.return_value = [MagicMock(), MagicMock(), MagicMock()]  # Mock three tabs

        # Mock columns
        mock_st.columns.return_value = [MagicMock(), MagicMock()]  # Mock two columns

        # Define mock_uploaded_file
        mock_uploaded_file = MagicMock()
        mock_uploaded_file.name = "statement.csv"
        mock_uploaded_file.type = "text/csv"
        mock_uploaded_file.size = 1024  # Set a valid size in bytes

        mock_st.file_uploader.return_value = mock_uploaded_file

        # Mock subheader
        mock_st.subheader = MagicMock()

        # Mock the API response for requests.post
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transactions": [
                {"date": "2025-04-01", "name": "Transaction 1", "amount": 100, "category": ["Category 1"], "account_id": "acc1"},
                {"date": "2025-04-02", "name": "Transaction 2", "amount": 200, "category": ["Category 2"], "account_id": "acc1"}
            ]
        }
        mock_requests_post.return_value = mock_response

        # Call the function
        aba.show_add_bank_account()

        # Assertions
        mock_st.subheader.assert_any_call("Connected Accounts")
        mock_st.subheader.assert_any_call("📥 Fetch Transactions")
        mock_requests_post.assert_called()  # Ensure the API was called

class TestShowAddBankAccount(unittest.TestCase):
    @patch("frontend.views.AddBankAccount.requests.post")
    @patch("frontend.views.AddBankAccount.show_account_selector")
    @patch("frontend.views.AddBankAccount.st")
    def test_show_add_bank_account_manage_banks(self, mock_st, mock_show_account_selector, mock_requests_post):
        # Mock session_state with MagicMock
        mock_st.session_state = MagicMock()
        mock_st.session_state.linked_banks = {"test123": {"institution_name": "Test Bank", "accounts": []}}
        mock_st.session_state.selected_accounts = {"test123": {"acc1": True}}  # Ensure at least one account is selected

        # Mock show_account_selector to return selected accounts
        mock_show_account_selector.return_value = ["acc1"]

        # Mock tabs
        mock_st.tabs.return_value = [MagicMock(), MagicMock(), MagicMock()]  # Mock three tabs

        # Mock columns
        mock_st.columns.return_value = [MagicMock(), MagicMock()]  # Mock two columns

        # Mock file uploader
        mock_uploaded_file = MagicMock()
        mock_uploaded_file.size = 2048  # Set a valid size in bytes
        mock_st.file_uploader.return_value = mock_uploaded_file

        # Mock subheader
        mock_st.subheader = MagicMock()

        # Mock the API response for requests.post
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transactions": [
                {"date": "2025-04-01", "name": "Transaction 1", "amount": 100, "category": ["Category 1"], "account_id": "acc1"},
                {"date": "2025-04-02", "name": "Transaction 2", "amount": 200, "category": ["Category 2"], "account_id": "acc1"}
            ]
        }
        mock_requests_post.return_value = mock_response

        # Call the function
        aba.show_add_bank_account()

        # Assertions
        mock_st.subheader.assert_any_call("Connected Accounts")
        mock_st.subheader.assert_any_call("📥 Fetch Transactions")
        mock_requests_post.assert_called()  # Ensure the API was called

    @patch("frontend.views.AddBankAccount.st")
    def test_show_add_bank_account_upload_statement(self, mock_st):
        # Mock session_state with MagicMock
        mock_st.session_state = MagicMock()

        # Mock tabs to return only the "Upload Bank Statement" tab
        mock_tab = MagicMock()
        mock_st.tabs.return_value = [MagicMock(), MagicMock(), mock_tab]

        # Mock file uploader
        mock_uploaded_file = MagicMock()
        mock_uploaded_file.name = "statement.csv"
        mock_uploaded_file.type = "text/csv"
        mock_uploaded_file.size = 1024  # Set a valid size in bytes
        mock_st.file_uploader.return_value = mock_uploaded_file

        # Mock button click
        mock_st.button.side_effect = lambda label, **kwargs: label == "Process Statement"

        # Call the function
        aba.show_add_bank_account()

        # Assertions
        mock_st.file_uploader.assert_called_once_with(
            "Choose a bank statement file",
            type=["csv"],
            help="Currently supporting CSV files. PDF and DOC support coming soon!"
        )
        mock_st.button.assert_any_call("Process Statement", use_container_width=True)

    @patch("frontend.views.AddBankAccount.st")
    def test_show_add_bank_account_link_new_bank(self, mock_st):
        # Mock session_state with MagicMock
        mock_st.session_state = MagicMock()
        mock_st.tabs.return_value = [MagicMock(), MagicMock(), MagicMock()]  # Mock tabs

        # Mock file uploader
        mock_uploaded_file = MagicMock()
        mock_uploaded_file.name = "statement.csv"
        mock_uploaded_file.type = "text/csv"
        mock_uploaded_file.size = 2048  # Set a valid size in bytes (e.g., 2 KB)
        mock_st.file_uploader.return_value = mock_uploaded_file

        # Mock button click
        mock_st.button.return_value = True

        # Call the function
        aba.show_add_bank_account()

        # Assertions
        mock_st.button.assert_any_call("Link New Bank Account", key="link_new_bank", use_container_width=True)

if __name__ == "__main__":
    unittest.main()
