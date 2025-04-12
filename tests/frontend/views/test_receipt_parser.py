import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import streamlit as st
from frontend.views.ReceiptParser import show_receipt_parser
from io import BytesIO
from PIL import Image
import io

class TestReceiptParser(unittest.TestCase):
    def create_mock_image(self):
        # Create a valid in-memory image
        img = Image.new("RGB", (100, 100), color="white")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        return img_bytes

    @patch("frontend.views.ReceiptParser.st.button", side_effect=[False, True])  # Ensure enough values for side_effect
    @patch("frontend.views.ReceiptParser.add_transaction_to_state")
    def test_save_pending_transactions(self, mock_add_transaction, mock_button):
        # Mock the function
        mock_add_transaction.return_value = "tx123"

        # Mock Streamlit session state
        mock_file = self.create_mock_image()
        mock_file.name = "receipt1.png"
        st.session_state["pending_receipts"] = [
            {"file": mock_file, "vendor": "Vendor A", "amount": 123.45, "date": "2023-01-01", "text": "Sample receipt text"}
        ]
        st.session_state["just_saved"] = False

        # Run the function
        show_receipt_parser()

        # Assertions
        mock_add_transaction.assert_called_once_with("Vendor A", 123.45, "2023-01-01", "Sample receipt text")
        self.assertTrue(st.session_state["just_saved"])

    @patch("frontend.views.ReceiptParser.st.button", side_effect=[False, True, False, True])  # Ensure enough values
    @patch("frontend.views.ReceiptParser.webrtc_streamer", return_value=MagicMock(video_processor=MagicMock(frame=np.zeros((100, 100, 3), dtype=np.uint8))))
    def test_save_all_pending_transactions(self, mock_webrtc, mock_button):
        # Mock Streamlit session state
        mock_file = self.create_mock_image()
        mock_file.name = "receipt1.png"
        st.session_state["pending_receipts"] = [
            {"file": mock_file, "vendor": "Vendor A", "amount": 123.45, "date": "2023-01-01", "text": "Sample receipt text"},
            {"file": mock_file, "vendor": "Vendor B", "amount": 67.89, "date": "2023-01-02", "text": "Another receipt text"}
        ]
        st.session_state["just_saved"] = False

        # Simulate saving all pending transactions
        with patch("streamlit.spinner"), \
             patch("streamlit.image"):  # Mock st.image
            show_receipt_parser()

        # Assertions
        self.assertEqual(len(st.session_state["pending_receipts"]), 0)
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

    @patch("frontend.views.ReceiptParser.extract_text_from_image")
    @patch("frontend.views.ReceiptParser.extract_receipt_fields")
    @patch("frontend.views.ReceiptParser.categorize_transaction")
    def test_file_upload_workflow(self, mock_categorize, mock_extract_fields, mock_extract_text):
        # Mock the receipt processing functions
        mock_extract_text.return_value = "Sample receipt text"
        mock_extract_fields.return_value = ("Vendor B", 67.89, "2023-01-02")
        mock_categorize.return_value = "Shopping"

        # Mock Streamlit session state
        mock_file = self.create_mock_image()
        mock_file.name = "receipt1.png"
        st.session_state["uploaded_files"] = [mock_file]
        st.session_state["processing_status"] = {}

        # Simulate the file upload and processing
        with patch("streamlit.spinner"), \
             patch("streamlit.image"):  # Mock st.image
            show_receipt_parser()

        # Assertions
        self.assertEqual(st.session_state["pending_receipts"][0]["vendor"], "Vendor B")
        self.assertEqual(st.session_state["pending_receipts"][0]["amount"], 67.89)
        self.assertEqual(st.session_state["pending_receipts"][0]["date"], "2023-01-02")
        self.assertEqual(st.session_state["pending_receipts"][0]["category"], "Shopping")

    def test_pending_transactions_table(self):
        # Mock Streamlit session state
        mock_file = self.create_mock_image()
        mock_file.name = "receipt1.png"
        st.session_state["pending_receipts"] = [
            {"file": mock_file, "vendor": "Vendor A", "amount": 123.45, "date": "2023-01-01", "category": "Food"},
            {"file": mock_file, "vendor": "Vendor B", "amount": 67.89, "date": "2023-01-02", "category": "Shopping"}
        ]

        # Simulate rendering the pending transactions table
        with patch("streamlit.dataframe") as mock_dataframe:
            show_receipt_parser()

        # Assertions
        mock_dataframe.assert_called_once()  # Ensure dataframe is called
        df = mock_dataframe.call_args[0][0]
        self.assertEqual(len(df), 2)
        self.assertIn("Vendor", df.columns)
        self.assertIn("Amount ($)", df.columns)
        self.assertIn("Date", df.columns)
        self.assertIn("Category", df.columns)

    def test_empty_states(self):
        # Mock Streamlit session state
        st.session_state["pending_receipts"] = []
        st.session_state["uploaded_files"] = []
        st.session_state["webcam_img"] = None

        # Simulate rendering the interface
        with patch("streamlit.markdown") as mock_markdown, \
             patch("streamlit.image"):  # Mock st.image
            show_receipt_parser()

        # Assertions
        mock_markdown.assert_any_call("""
        ### How to use:
        1. 📁 Upload receipt images or 📷 scan them with your webcam
        2. Review the extracted information
        3. Add receipts to pending transactions
        4. Save all pending transactions to finalize
        """)

if __name__ == "__main__":
    unittest.main()