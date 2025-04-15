import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from backend.flask_app import app

class TestFlaskApp(unittest.TestCase):
    def setUp(self):
        """Set up the test client for the Flask app."""
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True

    def test_home_route(self):
        """Test the root route of the Flask app."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 404, "Root route should return 404 as no route is defined.")

    def test_plaid_blueprint_registered(self):
        """Test if the Plaid blueprint is registered."""
        self.assertIn("plaid", self.app.blueprints, "Plaid blueprint should be registered.")

    def test_plaid_create_link_token(self):
        """Test the /api/plaid/create_link_token endpoint."""
        response = self.client.post("/api/plaid/create_link_token")
        self.assertIn(response.status_code, [200, 500], "Response should be 200 (success) or 500 (error).")
        if response.status_code == 200:
            self.assertIn("link_token", response.json, "Response should contain a 'link_token' key.")
        elif response.status_code == 500:
            self.assertIn("error", response.json, "Response should contain an 'error' key.")

    def test_plaid_exchange_public_token(self):
        """Test the /api/plaid/exchange_public_token endpoint with missing data."""
        response = self.client.post("/api/plaid/exchange_public_token", json={})
        self.assertEqual(response.status_code, 400, "Response should return 400 for missing parameters.")
        self.assertIn("error", response.json, "Response should contain an 'error' key.")

    def test_plaid_get_transactions(self):
        """Test the /api/plaid/get_transactions endpoint with no access tokens."""
        response = self.client.post("/api/plaid/get_transactions", json={})
        self.assertEqual(response.status_code, 400, "Response should return 400 if no access tokens are available.")
        self.assertIn("error", response.json, "Response should contain an 'error' key.")

    def test_plaid_get_accounts(self):
        """Test the /api/plaid/get_accounts endpoint with no access token."""
        response = self.client.get("/api/plaid/get_accounts")
        self.assertEqual(response.status_code, 400, "Response should return 400 if no access token is available.")
        self.assertIn("error", response.json, "Response should contain an 'error' key.")

    def test_plaid_handle_success(self):
        """Test the /api/plaid/handle-success endpoint with missing data."""
        response = self.client.post("/api/plaid/handle-success", json={})
        self.assertEqual(response.status_code, 400, "Response should return 400 for missing public token.")
        self.assertIn("error", response.json, "Response should contain an 'error' key.")

if __name__ == "__main__":
    unittest.main()