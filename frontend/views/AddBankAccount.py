import streamlit as st
import requests
from datetime import datetime, timedelta
from components.AccountSelector import add_bank_to_state, show_account_selector
import streamlit.components.v1 as components

def show_add_bank_account():
    st.title("🏦 Connect Your Bank Account")

    # Show existing accounts
    st.subheader("Connected Accounts")
    
    # Check if we need to refresh accounts after linking
    status = st.query_params.get("status")
    
    # Force refresh accounts list if we just linked a new bank
    if status == "success":
        if "selected_accounts" in st.session_state:
            del st.session_state.selected_accounts
        st.rerun()  # Refresh the page to show new accounts
    
    selected_accounts = show_account_selector(show_title=False)

    # Add New Bank Account section
    st.subheader("➕ Add New Bank Account")
    
    if st.button("Link New Bank Account", key="link_new_bank"):
        # Open the Flask endpoint in a new tab with redirect URL
        js = """
            <script>
                const currentPath = window.location.pathname;
                const redirectUrl = encodeURIComponent('http://localhost:8501/?page=add_bank');
                window.open('http://localhost:5050/launch-plaid-link?redirect_url=' + redirectUrl, '_blank');
            </script>
        """
        st.components.v1.html(js, height=0)
        st.info("✨ Opening bank connection window in a new tab...")
        st.info("👉 Please complete the process in the new tab and return here when done.")

    # Transaction Fetching Section
    if selected_accounts:
        st.subheader("📥 Fetch Transactions")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now() - timedelta(days=30)
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now()
            )

        if st.button("Get Transactions"):
            st.info(f"📆 Date Range: `{start_date}` to `{end_date}`")
            
            # Fetch transactions for each selected account
            all_transactions = []
            with st.spinner("Fetching transactions..."):
                for account_id in selected_accounts:
                    tx_response = requests.post(
                        "http://localhost:5050/api/plaid/get_transactions",
                        json={
                            "start_date": str(start_date),
                            "end_date": str(end_date),
                            "account_id": account_id
                        }
                    )

                    if tx_response.status_code == 200:
                        transactions = tx_response.json().get("transactions", [])
                        all_transactions.extend(transactions)
                    else:
                        st.error(f"Failed to fetch transactions for account {account_id}")

            if all_transactions:
                st.success(f"Found {len(all_transactions)} transactions.")
                # Store in session state
                st.session_state['transactions'] = all_transactions
                # Display simplified transaction table
                table = [
                    {
                        "Date": tx["date"],
                        "Name": tx["name"],
                        "Amount ($)": tx["amount"],
                        "Category": ", ".join(tx.get("category", [])),
                        "Account": tx.get("account_name", "")
                    }
                    for tx in all_transactions
                ]
                st.dataframe(table, use_container_width=True)
            else:
                st.warning("No transactions found for the selected period.") 