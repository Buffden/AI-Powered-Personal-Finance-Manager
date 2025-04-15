from playwright.sync_api import sync_playwright

def test_navigation():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the Streamlit app
        page.goto("http://localhost:8501")
        page.wait_for_timeout(2000)

        # Verify the title
        assert page.title() == "AI Finance Manager"

        # Test navigation to all pages
        pages = [
            ("🏠 Home", "Welcome to FinanceAI"),
            ("📸 Receipt Parser", "📸 Receipt Scanner"),
            ("🔔 Bill Reminders", "🔔 Bill Reminders"),
            ("💬 AI Financial Advisor", "💬 AI Financial Advisor"),
            ("📈 Spending Insights", "📈 Spending Insights"),
            ("📊 Budget Tracking", "📊 Budget Tracking"),
            ("🏦 Add Bank Account", "🏦 Connect Your Bank Account"),
        ]

        for button_text, expected_text in pages:
            try:
                # Click the navigation button
                page.click(f"text={button_text}")
                # Wait for the expected text to appear
                page.wait_for_selector(f"text={expected_text}", timeout=30000)
                assert expected_text in page.content()
            except Exception as e:
                print(f"Failed to load page for {button_text}. Debugging content:")
                print(page.content())
                raise e

        # Test sidebar visibility
        sidebar_buttons = [
            "🏠 Home",
            "🏦 Add Bank Account",
            "📈 Spending Insights",
            "📊 Budget Tracking",
            "🔔 Bill Reminders",
            "💬 AI Financial Advisor",
            "📸 Receipt Parser",
        ]

        for button_text in sidebar_buttons:
            assert page.is_visible(f"text={button_text}"), f"Sidebar button {button_text} is not visible"

        # Test navigation to Spending Insights and verify account selection
        try:
            page.click("text=📈 Spending Insights")
            page.wait_for_selector("text=🏦 Select Accounts", timeout=30000)
            assert page.is_visible("text=🏦 Select Accounts"), "Account selector is not visible"
        except Exception as e:
            print("Failed to load Spending Insights or account selector. Debugging content:")
            print(page.content())
            raise e

        # Test navigation to Budget Tracking and verify elements
        try:
            page.click("text=📊 Budget Tracking")
            page.wait_for_selector("text=📊 Budget Tracker - Monthly Overspending", timeout=30000)
            if page.is_visible("text=No banks linked"):
                print("No banks linked. Skipping Budget Settings test.")
            else:
                assert page.is_visible("text=💰 Budget Settings"), "Budget Settings section is not visible"
        except Exception as e:
            print("Failed to load Budget Tracking or its elements. Debugging content:")
            print(page.content())
            raise e

        # Close browser
        browser.close()