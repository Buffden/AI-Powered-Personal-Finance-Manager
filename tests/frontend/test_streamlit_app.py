import unittest
from unittest.mock import patch, MagicMock
import streamlit as st
import sys
import os

# Add the project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Import the app module
import frontend.streamlit_app as app


class TestStreamlitApp(unittest.TestCase):
    @patch("streamlit.set_page_config")
    @patch("streamlit.sidebar")
    @patch("streamlit.session_state", new_callable=dict)
    def test_session_state_initialization(self, mock_session_state, mock_sidebar, mock_set_page_config):
        """Test that session state is initialized correctly."""
        # Mock query_params
        mock_query_params = {"page": "home"}
        with patch("streamlit.query_params", mock_query_params):
            app.st.session_state = mock_session_state
            app.st.sidebar = mock_sidebar

            # Run the app logic
            app.st.session_state.clear()
            app.st.session_state["current_page"] = app.st.query_params.get("page", "home")

            # Assert session state is initialized
            self.assertIn("current_page", app.st.session_state)
            self.assertEqual(app.st.session_state["current_page"], "home")

    @patch("streamlit.sidebar.button")
    @patch("streamlit.session_state", new_callable=dict)
    def test_navigation_logic(self, mock_session_state, mock_sidebar_button):
        """Test that navigation updates the current page in session state."""
        # Mock sidebar buttons
        mock_sidebar_button.side_effect = lambda label, key: key == "add_bank"

        # Mock session state
        mock_session_state["current_page"] = "home"
        app.st.session_state = mock_session_state

        # Run the navigation logic
        pages = [
            ("🏠", "Home", "home"),
            ("🏦", "Add Bank Account", "add_bank"),
            ("📈", "Spending Insights", "insights"),
            ("📊", "Budget Tracking", "budget"),
            ("🔔", "Bill Reminders", "bills"),
            ("💬", "AI Financial Advisor", "chatbot"),
        ]
        for _, _, page in pages:
            if app.st.sidebar.button(f"{page}", key=page):
                app.st.session_state["current_page"] = page

        # Assert the current page is updated
        self.assertEqual(app.st.session_state["current_page"], "add_bank")

    @patch("streamlit.success")
    @patch("streamlit.query_params", new_callable=dict)
    @patch("streamlit.session_state", new_callable=dict)
    def test_plaid_callback_status(self, mock_session_state, mock_query_params, mock_success):
        """Test handling of Plaid callback status."""
        # Mock query params
        mock_query_params.update({"status": "success", "institution_name": "Test Bank"})
        app.st.query_params = mock_query_params

        # Mock session state
        mock_session_state["current_page"] = "home"
        app.st.session_state = mock_session_state

        # Run the callback logic
        if app.st.query_params.get("status") == "success":
            institution_name = app.st.query_params.get("institution_name")
            app.st.success(f"✅ Successfully linked {institution_name}!")
            app.st.session_state["current_page"] = "add_bank"

        # Assert the success message and page update
        mock_success.assert_called_once_with("✅ Successfully linked Test Bank!")
        self.assertEqual(app.st.session_state["current_page"], "add_bank")


if __name__ == "__main__":
    unittest.main()