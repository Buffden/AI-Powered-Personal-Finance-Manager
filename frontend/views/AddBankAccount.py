import streamlit as st
import requests
from datetime import datetime, timedelta
from components.AccountSelector import add_bank_to_state, show_account_selector
import streamlit.components.v1 as components
import pandas as pd
import io

def process_uploaded_statement(uploaded_file):
    """Process the uploaded bank statement and extract transactions."""
    try:
        # For CSV files (we can extend this for PDF/DOC later)
        if uploaded_file.type == "text/csv":
            df = pd.read_csv(uploaded_file)
            
            # Standardize column names
            df.columns = [col.strip().lower() for col in df.columns]
            
            # Initialize transactions list if not exists
            if 'all_transactions' not in st.session_state:
                st.session_state.all_transactions = []
            
            # Register manual upload account with AccountSelector if not already done
            manual_account = {
                "account_id": "manual_upload",
                "name": "Uploaded Statement",
                "type": "other",
                "subtype": "other",
                "mask": "0000",  # Adding a default mask
                "official_name": "Manual CSV Upload",
                "balances": {
                    "available": None,
                    "current": None,
                    "limit": None,
                    "iso_currency_code": "USD"
                }
            }
            
            # Only add the manual account if it doesn't exist
            if ("manual" not in st.session_state.get("linked_banks", {}) or 
                not any(acc["account_id"] == "manual_upload" 
                       for acc in st.session_state.linked_banks.get("manual", {}).get("accounts", []))):
                add_bank_to_state("Manual Upload", "manual", [manual_account])
            
            # Convert DataFrame to list of transactions in Plaid-like format
            transactions = []
            for _, row in df.iterrows():
                # Convert amount: positive = expense (debit), negative = income (credit)
                amount = float(str(row["amount ($)"]).replace("$", "").replace(",", ""))
                
                # Create transaction in Plaid format
                transaction = {
                    "transaction_id": f"manual_{len(st.session_state.all_transactions) + len(transactions)}",
                    "account_id": "manual_upload",
                    "account_name": "Manual Upload",
                    "institution_id": "manual",
                    "institution_name": "Manual Upload",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "name": row["vendor"],
                    "amount": amount,
                    "category": [row["category"]] if "category" in row else ["Uncategorized"],
                    "category_id": "manual",
                    "pending": False,
                    "payment_channel": "other",
                    "transaction_type": "special",
                    "merchant_name": row["vendor"],
                    "source": "manual_upload",
                    "authorized_date": datetime.now().strftime("%Y-%m-%d"),
                    "authorized_datetime": datetime.now().isoformat(),
                    "datetime": datetime.now().isoformat(),
                    "payment_method": "other",
                    "payment_processor": None,
                    "personal_finance_category": {
                        "primary": row["category"] if "category" in row else "Uncategorized",
                        "detailed": row["category"] if "category" in row else "Uncategorized"
                    }
                }
                transactions.append(transaction)
            
            # Add new transactions to existing ones
            st.session_state.all_transactions.extend(transactions)
            
            # Update the main transactions list
            st.session_state.transactions = st.session_state.all_transactions.copy()
            
            return len(transactions)
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return 0

def add_bank_to_state(institution_name, institution_id, accounts):
    """Helper function to add a bank and its accounts to session state"""
    if 'linked_banks' not in st.session_state:
        st.session_state.linked_banks = {}
    
    # Add or update the bank in session state with the correct structure
    st.session_state.linked_banks[institution_id] = {
        'institution_name': institution_name,  # This is what AccountSelector expects
        'institution_id': institution_id,
        'accounts': accounts
    }
    
    # Initialize selection state for new accounts
    if 'selected_accounts' not in st.session_state:
        st.session_state.selected_accounts = {}
    if institution_id not in st.session_state.selected_accounts:
        st.session_state.selected_accounts[institution_id] = {
            acc['account_id']: False for acc in accounts
        }

def show_add_bank_account():
    st.title("🏦 Connect Your Bank Account")
    
    # Initialize transaction storage if not exists
    if 'all_transactions' not in st.session_state:
        st.session_state.all_transactions = []
    if 'transactions' not in st.session_state:
        st.session_state.transactions = []
    
    # Handle Plaid callback parameters
    status = st.query_params.get("status")
    public_token = st.query_params.get("public_token")
    institution_name = st.query_params.get("institution_name")
    institution_id = st.query_params.get("institution_id")
    
    # Display Plaid callback information if available
    if status == "success" and public_token and institution_name and institution_id:
        st.success(f"✅ Successfully linked {institution_name}!")
        
        # Show public token in a copyable code block
        st.info("🔑 Public Token:")
        st.code(public_token, language=None)
        
        # Exchange public token for access token
        st.info("🔄 Exchanging public token for access token...")
        response = requests.post(
            "http://localhost:5050/api/plaid/exchange_public_token",
            json={
                "public_token": public_token,
                "institution_id": institution_id,
                "institution_name": institution_name
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            accounts = data.get("accounts", [])
            
            # Register the bank and its accounts in session state
            add_bank_to_state(institution_name, institution_id, accounts)
            
            st.success("🔑 Access token generated successfully!")
            st.code(access_token, language=None)
            
            # Clear the query parameters to avoid duplicate processing
            current_page = st.query_params.get("page", "add_bank")
            st.query_params.clear()
            st.query_params["page"] = current_page
            
            # Force refresh the page to show new accounts
            st.rerun()
        else:
            st.error("❌ Failed to exchange public token for access token.")
            st.write("Debug: Error Response:", response.text)
    elif status == "error":
        error = st.query_params.get("error")
        st.error(f"❌ Error: {error}")
    elif status == "cancelled":
        st.info("ℹ️ Bank linking was cancelled.")
    
    # Create tabs for different methods
    tab1, tab2, tab3 = st.tabs([
        "📊 Manage Connected Banks",
        "➕ Add Another Bank",
        "📄 Upload Bank Statement"
    ])
    
    # Tab 1: Manage Connected Banks
    with tab1:
        st.subheader("Connected Accounts")
        
        # Check if we need to refresh accounts after linking
        status = st.query_params.get("status")
        
        # Force refresh accounts list if we just linked a new bank
        if status == "success":
            if "selected_accounts" in st.session_state:
                del st.session_state.selected_accounts
            st.rerun()
        
        selected_accounts = show_account_selector(show_title=False)
        
        # Transaction Fetching Section
        if selected_accounts:
            st.subheader("📥 Fetch Transactions")
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=datetime(2025, 1, 1).date(),  # Set to January 1, 2025
                    help="Sandbox data is available from January 2025 to April 2025"
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=datetime(2025, 4, 30).date(),  # Set to April 30, 2025
                    help="Sandbox data is available from January 2025 to April 2025"
                )

            if st.button("Get Transactions", use_container_width=True):
                st.info(f"📆 Date Range: `{start_date}` to `{end_date}`")
                
                # Fetch transactions for each selected account
                plaid_transactions = []
                with st.spinner("Fetching transactions..."):
                    for account_id in selected_accounts:
                        request_data = {
                            "start_date": str(start_date),
                            "end_date": str(end_date),
                            "account_ids": [account_id]
                        }
                        
                        tx_response = requests.post(
                            "http://localhost:5050/api/plaid/get_transactions",
                            json=request_data
                        )

                        if tx_response.status_code == 200:
                            transactions = tx_response.json().get("transactions", [])
                            # Add source field to distinguish Plaid transactions
                            for tx in transactions:
                                tx["source"] = "plaid"
                            plaid_transactions.extend(transactions)
                        else:
                            st.error(f"Failed to fetch transactions for account {account_id}")

                if plaid_transactions:
                    st.success(f"Found {len(plaid_transactions)} transactions.")
                    
                    # Remove any existing Plaid transactions for these accounts
                    st.session_state.all_transactions = [
                        tx for tx in st.session_state.all_transactions 
                        if tx.get("source") != "plaid" or tx.get("account_id") not in selected_accounts
                    ]
                    
                    # Add new Plaid transactions
                    st.session_state.all_transactions.extend(plaid_transactions)
                    
                    # Update the main transactions list
                    st.session_state.transactions = st.session_state.all_transactions.copy()
                    
                    # Display simplified transaction table
                    table = [
                        {
                            "Date": tx["date"],
                            "Name": tx["name"],
                            "Amount ($)": tx["amount"],
                            "Category": ", ".join(tx.get("category", [])),
                            "Account": f"{tx.get('account_name', '')} ({tx.get('mask', '')})" if tx.get('account_name') else "",
                            "Source": tx.get("source", "unknown")
                        }
                        for tx in plaid_transactions
                    ]
                    st.dataframe(table, use_container_width=True)
                    
                    # Show total transactions count
                    st.info(f"Total transactions in system: {len(st.session_state.all_transactions)}")
                else:
                    st.warning("No transactions found for the selected period.")
    
    # Tab 2: Add Another Bank
    with tab2:
        st.info("💡 You can connect multiple bank accounts to get a complete view of your finances.")
        if st.button("Link New Bank Account", key="link_new_bank", use_container_width=True):
            # Open the Flask endpoint in a new tab with redirect URL
            js = """
                <script>
                    const redirectUrl = encodeURIComponent('http://localhost:8501/?page=add_bank_account');
                    window.open('http://localhost:5050/launch-plaid-link?redirect_url=' + redirectUrl, '_blank');
                </script>
            """
            st.components.v1.html(js, height=0)
            st.info("✨ Opening bank connection window in a new tab...")
            st.info("👉 Please complete the process in the new tab and return here when done.")
    
    # Tab 3: Upload Bank Statement
    with tab3:
        st.info("📝 Upload your bank statement in CSV format to import transactions.")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a bank statement file",
            type=["csv"],  # We'll add PDF/DOC support later
            help="Currently supporting CSV files. PDF and DOC support coming soon!"
        )
        
        if uploaded_file:
            st.write("File details:")
            file_details = {
                "Filename": uploaded_file.name,
                "File type": uploaded_file.type,
                "File size": f"{uploaded_file.size / 1024:.2f} KB"
            }
            for key, value in file_details.items():
                st.write(f"- {key}: {value}")
            
            if st.button("Process Statement", use_container_width=True):
                with st.spinner("Processing your bank statement..."):
                    num_transactions = process_uploaded_statement(uploaded_file)
                    if num_transactions > 0:
                        st.success(f"✅ Successfully imported {num_transactions} transactions!")
                        
                        # Show the imported transactions
                        if 'transactions' in st.session_state:
                            st.subheader("Imported Transactions")
                            st.dataframe(
                                st.session_state.transactions,
                                use_container_width=True
                            )
                    else:
                        st.error("No transactions were imported. Please check the file format.") 