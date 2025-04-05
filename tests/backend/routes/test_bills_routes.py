import unittest
from flask import Flask
from backend.routes.bills_routes import bills_bp

class TestBillsRoutes(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and test client."""
        self.app = Flask(__name__)
        self.app.register_blueprint(bills_bp)
        self.client = self.app.test_client()

    def test_test_bills_route(self):
        """Test the /api/bills/test endpoint."""
        response = self.client.get("/api/bills/test")
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json)
        self.assertEqual(response.json["message"], "Bills route working!")

if __name__ == "__main__":
    unittest.main()