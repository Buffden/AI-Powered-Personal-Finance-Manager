import unittest

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromName("tests.backend.test_flask_app"))
    suite.addTests(loader.loadTestsFromName("tests.backend.routes.test_plaid_routes"))
    suite.addTests(loader.loadTestsFromName("tests.backend.routes.test_bills_routes"))
    suite.addTests(loader.loadTestsFromName("tests.frontend.test_streamlit_app"))
    suite.addTests(loader.loadTestsFromName("tests.frontend.views.test_budget_tracker"))
    suite.addTests(loader.loadTestsFromName("tests.frontend.views.test_add_bank_account"))
    suite.addTests(loader.loadTestsFromName("tests.frontend.views.test_chatbot"))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)