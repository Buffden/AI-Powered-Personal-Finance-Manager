import unittest
from unittest.mock import patch, MagicMock, Mock
from flask import Flask
from backend.routes.plaid_routes import plaid_bp, ACCESS_TOKENS

class TestPlaidRoutes(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and test client."""
        self.app = Flask(__name__)
        self.app.register_blueprint(plaid_bp)
        self.client = self.app.test_client()

    @patch("backend.routes.plaid_routes.client.link_token_create")
    def test_create_link_token_success(self, mock_link_token_create):
        """Test the /api/plaid/create_link_token endpoint for success."""
        mock_link_token_create.return_value.to_dict.return_value = {"link_token": "mocked_link_token"}
        response = self.client.post("/api/plaid/create_link_token")
        self.assertEqual(response.status_code, 200)
        self.assertIn("link_token", response.json)
        self.assertEqual(response.json["link_token"], "mocked_link_token")

    @patch("backend.routes.plaid_routes.client.link_token_create")
    def test_create_link_token_error(self, mock_link_token_create):
        """Test the /api/plaid/create_link_token endpoint for error handling."""
        mock_link_token_create.side_effect = Exception("Mocked error")
        response = self.client.post("/api/plaid/create_link_token")
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json)
        self.assertEqual(response.json["error"], "Mocked error")

    @patch("backend.routes.plaid_routes.client.item_public_token_exchange")
    @patch("backend.routes.plaid_routes.client.accounts_get")
    def test_exchange_public_token_success(self, mock_accounts_get, mock_item_public_token_exchange):
        """Test the /api/plaid/exchange_public_token endpoint for success."""
        mock_item_public_token_exchange.return_value.to_dict.return_value = {"access_token": "mocked_access_token"}
        mock_accounts_get.return_value.to_dict.return_value = {"accounts": [{"id": "account_1"}]}

        data = {
            "public_token": "mocked_public_token",
            "institution_id": "mocked_institution_id",
            "institution_name": "Mocked Institution"
        }
        response = self.client.post("/api/plaid/exchange_public_token", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json)
        self.assertEqual(response.json["access_token"], "mocked_access_token")
        self.assertIn("accounts", response.json)
        self.assertEqual(response.json["accounts"], [{"id": "account_1"}])

    def test_exchange_public_token_missing_data(self):
        """Test the /api/plaid/exchange_public_token endpoint with missing data."""
        response = self.client.post("/api/plaid/exchange_public_token", json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)
        self.assertEqual(response.json["error"], "Missing required parameters")

    @patch("backend.routes.plaid_routes.client.transactions_get")
    def test_get_transactions_success(self, mock_transactions_get):
        from backend.routes.plaid_routes import ACCESS_TOKENS
        ACCESS_TOKENS["demo-user-123"] = {"mocked_institution_id": "mocked_access_token"}

        mock_transactions_get.return_value.to_dict.return_value = {
            "transactions": [
                {"id": "transaction_1"}
            ],
            "accounts": []
        }

        response = self.client.post("/api/plaid/get_transactions", json={
            "account_ids": ["mocked_account_id"],
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["transactions"][0]["id"], "transaction_1")
        self.assertEqual(response.json["transactions"][0]["institution_id"], "mocked_institution_id")


    def test_get_transactions_no_access_tokens(self):
        """Test the /api/plaid/get_transactions endpoint with no access tokens."""
        ACCESS_TOKENS.clear()
        response = self.client.post("/api/plaid/get_transactions", json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)
        self.assertEqual(response.json["error"], "No access tokens")

    @patch("backend.routes.plaid_routes.client.accounts_get")
    def test_get_accounts_success(self, mock_accounts_get):
        """Test the /api/plaid/get_accounts endpoint for success."""
        ACCESS_TOKENS["demo-user-123"] = "mocked_access_token"
        mock_accounts_get.return_value.to_dict.return_value = {"accounts": [{"id": "account_1"}]}

        response = self.client.get("/api/plaid/get_accounts")
        self.assertEqual(response.status_code, 200)
        self.assertIn("accounts", response.json)
        self.assertEqual(response.json["accounts"], [{"id": "account_1"}])

    def test_get_accounts_no_access_token(self):
        """Test the /api/plaid/get_accounts endpoint with no access token."""
        ACCESS_TOKENS.clear()
        response = self.client.get("/api/plaid/get_accounts")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)
        self.assertEqual(response.json["error"], "No access token")

if __name__ == "__main__":
    unittest.main()