import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import streamlit as st
from frontend.views.ReceiptParser import show_receipt_parser

class TestReceiptParser(unittest.TestCase):
    @patch("frontend.views.ReceiptParser.webrtc_streamer")
    @patch("frontend.views.ReceiptParser.add_transaction_to_state")
    def test_save_pending_transactions(self, mock_add_transaction, mock_webrtc):
        # Mock the function
        mock_add_transaction.return_value = "tx123"

        # Mock Streamlit session state
        st.session_state["pending_receipts"] = [
            {
                "file": MagicMock(name="receipt1.jpg"),
                "vendor": "Vendor A",
                "amount": 123.45,
                "date": "2023-01-01",
                "category": "Food",
                "text": "Sample receipt text"
            },
            {
                "file": MagicMock(name="receipt2.jpg"),
                "vendor": "Vendor B",
                "amount": 67.89,
                "date": "2023-01-02",
                "category": "Shopping",
                "text": "Another receipt text"
            }
        ]
        st.session_state["just_saved"] = False
        st.session_state["transactions"] = []

        # Mock webrtc_streamer context
        mock_ctx = MagicMock()
        mock_ctx.video_processor.frame = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_webrtc.return_value = mock_ctx

        # Run the function
        with patch("streamlit.button", side_effect=[False, False, True]), \
             patch("streamlit.spinner"):
            show_receipt_parser()

        # Assertions
        self.assertEqual(mock_add_transaction.call_count, 2)
        self.assertEqual(len(st.session_state["transactions"]), 2)
        self.assertEqual(len(st.session_state["pending_receipts"]), 0)
        self.assertTrue(st.session_state["just_saved"])

    @patch("frontend.views.ReceiptParser.st.button", side_effect=[False, True])  # Simulate button click
    @patch("frontend.views.ReceiptParser.add_transaction_to_state")
    def test_save_pending_transactions(self, mock_add_transaction, mock_button):
        # Mock the function
        mock_add_transaction.return_value = "tx123"

        # Mock Streamlit session state
        st.session_state["pending_receipts"] = [
            {"vendor": "Vendor A", "amount": 123.45, "date": "2023-01-01", "text": "Sample receipt text"}
        ]
        st.session_state["just_saved"] = False

        # Run the function
        show_receipt_parser()

        # Assertions
        mock_add_transaction.assert_called_once_with("Vendor A", 123.45, "2023-01-01", "Sample receipt text")
        self.assertTrue(st.session_state["just_saved"])

    @patch("frontend.views.ReceiptParser.webrtc_streamer")
    @patch("frontend.views.ReceiptParser.delete_receipt_transaction")
    def test_delete_recent_transaction(self, mock_delete_transaction, mock_webrtc):
        # Mock Streamlit session state
        st.session_state["transactions"] = [
            {"transaction_id": "tx123", "date": "2023-01-01", "merchant_name": "Vendor A", "amount": 123.45, "category": ["Food"], "source": "manual_upload"}
        ]

        # Mock webrtc_streamer context
        mock_ctx = MagicMock()
        mock_ctx.video_processor.frame = np.zeros((100, 100, 3), dtype=np.uint8)  # Mock a NumPy array
        mock_webrtc.return_value = mock_ctx

        # Run the function
        with patch("streamlit.button", return_value=True), \
             patch("streamlit.columns", return_value=[MagicMock(), MagicMock()]):  # Ensure 2 columns are created
            show_receipt_parser()

        # Assertions
        mock_delete_transaction.assert_called_once_with("tx123")

    @patch("frontend.views.ReceiptParser.st.columns")
    def test_delete_recent_transaction(self, mock_columns):
        # Mock columns to simulate insufficient columns
        mock_columns.return_value = []
        with self.assertRaises(IndexError):
            show_receipt_parser()

        # Mock columns to simulate sufficient columns
        mock_columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        with patch("frontend.views.ReceiptParser.st.markdown"):
            show_receipt_parser()  # Should not raise IndexError

    @patch("frontend.views.ReceiptParser.st.columns")
    def test_delete_recent_transaction(self, mock_columns):
        mock_columns.return_value = []
        show_receipt_parser()  # Ensure no exception is raised

if __name__ == "__main__":
    unittest.main()