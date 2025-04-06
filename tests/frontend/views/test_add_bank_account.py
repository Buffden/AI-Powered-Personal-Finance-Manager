import unittest
from unittest.mock import patch
from io import StringIO
import pandas as pd
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


if __name__ == "__main__":
    unittest.main()
