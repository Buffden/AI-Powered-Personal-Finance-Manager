import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
from datetime import datetime
from backend.utils.receipt_parser import (
    extract_text_from_image,
    extract_receipt_fields,
    categorize_transaction,
    add_transaction_to_state,
)

class TestReceiptParser(unittest.TestCase):
    @patch("backend.utils.receipt_parser.OpenAI")
    @patch("backend.utils.receipt_parser.Image.open")
    def test_extract_text_from_image(self, mock_image_open, mock_openai):
        """Test extracting text from an image."""
        mock_image = MagicMock()
        mock_image_open.return_value = mock_image
        mock_openai.return_value.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="Mocked Store\nTotal: $20.00\nDate: 2025-04-10"))
        ]

        with patch("backend.utils.receipt_parser.BytesIO", return_value=BytesIO()):
            result = extract_text_from_image("mock_image_path")
            self.assertIn("Mocked Store", result)
            self.assertIn("Total: $20.00", result)
            self.assertIn("Date: 2025-04-10", result)

    def test_extract_receipt_fields(self):
        """Test extracting fields from receipt text."""
        text = "Mocked Store\nTotal: $20.00\nDate: 2025-04-10"
        vendor, amount, date = extract_receipt_fields(text)
        self.assertEqual(vendor, "Mocked Store")
        self.assertEqual(amount, 20.00)
        self.assertEqual(datetime.strptime(date, "%a, %d %b %Y %H:%M:%S GMT").date(), datetime(2025, 4, 10).date())

    @patch("backend.utils.receipt_parser.OpenAI")
    def test_categorize_transaction(self, mock_openai):
        """Test categorizing a transaction."""
        mock_openai.return_value.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="Food and Drink"))
        ]
        category = categorize_transaction("Mocked Store", "Mocked receipt text")
        self.assertEqual(category, "Food and drink")

    @patch("backend.utils.receipt_parser.st")
    def test_add_transaction_to_state(self, mock_st):
        """Test adding a transaction to session state."""
        # Mock session_state as an object with attribute-style access
        mock_st.session_state = MagicMock()
        mock_st.session_state.transactions = []

        vendor = "Mocked Store"
        amount = 20.00
        date = "2025-04-10"
        text = "Mocked receipt text"

        transaction_id = add_transaction_to_state(vendor, amount, date, text)

        self.assertTrue(hasattr(mock_st.session_state, "transactions"))
        self.assertEqual(len(mock_st.session_state.transactions), 1)
        transaction = mock_st.session_state.transactions[0]
        self.assertEqual(transaction["name"], vendor)
        self.assertEqual(transaction["amount"], amount)
        self.assertEqual(transaction["transaction_id"], transaction_id)

if __name__ == "__main__":
    unittest.main()