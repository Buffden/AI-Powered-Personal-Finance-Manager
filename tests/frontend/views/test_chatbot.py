import unittest
from unittest.mock import patch, MagicMock
from frontend.views.Chatbot import show_chatbot

class TestChatbotUI(unittest.TestCase):

    def test_chat_flow(self):
        mock_st = MagicMock()
        mock_config = MagicMock()
        mock_chat = MagicMock(return_value=("Mocked response", []))

        mock_session = MagicMock()
        mock_session.transactions = [{"amount": 100}]
        mock_session.chat_started = False
        mock_session.conversation_history = []

        mock_session.__getitem__.side_effect = lambda key: getattr(mock_session, key)
        mock_session.__setitem__.side_effect = lambda key, value: setattr(mock_session, key, value)
        mock_session.__contains__.side_effect = lambda key: hasattr(mock_session, key)

        mock_st.session_state = mock_session
        mock_st.text_area.return_value = "Save for a car"
        mock_st.button.return_value = True
        mock_st.spinner.return_value.__enter__.return_value = None
        mock_st.spinner.return_value.__exit__.return_value = None
        mock_st.rerun = MagicMock()
        mock_st.chat_input.return_value = None  # Prevent follow-up input from triggering second call

        with patch("frontend.views.Chatbot.st", mock_st), \
            patch("frontend.views.Chatbot.Config", mock_config), \
            patch.dict(show_chatbot.__globals__, {"chat_with_advisor": mock_chat}):

            mock_config.get_openai_api_key.return_value = "fake-key"
            show_chatbot()

        mock_chat.assert_called_once()
        mock_st.rerun.assert_called_once()

    def test_no_api_key(self):
        mock_st = MagicMock()
        mock_config = MagicMock()
        mock_config.get_openai_api_key.side_effect = ValueError("Missing key")

        mock_session = MagicMock()
        mock_session.transactions = [{"amount": 50}]
        mock_session.chat_started = False

        mock_session.__getitem__.side_effect = lambda key: getattr(mock_session, key)
        mock_session.__setitem__.side_effect = lambda key, value: setattr(mock_session, key, value)
        mock_session.__contains__.side_effect = lambda key: hasattr(mock_session, key)

        mock_st.session_state = mock_session
        mock_st.text_area.return_value = ""
        mock_st.button.return_value = True
        mock_st.spinner.return_value.__enter__.return_value = None
        mock_st.spinner.return_value.__exit__.return_value = None
        mock_st.error = MagicMock()

        with patch("frontend.views.Chatbot.st", mock_st), \
             patch("frontend.views.Chatbot.Config", mock_config):

            show_chatbot()

        mock_st.error.assert_called_with("⚠️ OpenAI API key not configured. Please add it to your .env file.")

    def test_empty_message(self):
        mock_st = MagicMock()
        mock_config = MagicMock()
        mock_config.get_openai_api_key.return_value = "somekey"

        mock_session = MagicMock()
        mock_session.transactions = [{"amount": 25}]
        mock_session.chat_started = True
        mock_session.conversation_history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"}
        ]

        mock_session.__getitem__.side_effect = lambda key: getattr(mock_session, key)
        mock_session.__setitem__.side_effect = lambda key, value: setattr(mock_session, key, value)
        mock_session.__contains__.side_effect = lambda key: hasattr(mock_session, key)

        mock_st.session_state = mock_session
        mock_st.chat_input.return_value = ""
        mock_st.chat_message.return_value.__enter__.return_value = None
        mock_st.chat_message.return_value.__exit__.return_value = None

        with patch("frontend.views.Chatbot.st", mock_st), \
             patch("frontend.views.Chatbot.Config", mock_config):
            show_chatbot()

        mock_st.chat_input.assert_called_once()

if __name__ == "__main__":
    unittest.main()
