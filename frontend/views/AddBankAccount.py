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
        if uploaded_file.type == "text/csv":
            df = pd.read_csv(uploaded_file)
            
            # Standardize column names
            df.columns = [col.strip().lower() for col in df.columns]

            # Try to find a date column
            possible_date_cols = ["date", "transaction date", "posted date"]
            date_col = next((col for col in df.columns if col in possible_date_cols), None)

            if not date_col:
                st.error("No recognizable date column found in uploaded file.")
                return 0

            # Convert date column to datetime format
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df.dropna(subset=[date_col], inplace=True)  # Remove rows with invalid dates

            if 'all_transactions' not in st.session_state:
                st.session_state.all_transactions = []

            manual_account = {
                "account_id": "manual_upload",
                "name": "Uploaded Statement",
                "type": "other",
                "subtype": "other",
                "mask": "0000",
                "official_name": "Manual CSV Upload",
                "balances": {
                    "available": None,
                    "current": None,
                    "limit": None,
                    "iso_currency_code": "USD"
                }
            }

            if ("manual" not in st.session_state.get("linked_banks", {}) or 
                not any(acc["account_id"] == "manual_upload" 
                        for acc in st.session_state.linked_banks.get("manual", {}).get("accounts", []))):
                add_bank_to_state("Manual Upload", "manual", [manual_account])

            transactions = []
            for _, row in df.iterrows():
                amount = float(str(row["amount ($)"]).replace("$", "").replace(",", ""))
                date_str = row[date_col].strftime("%Y-%m-%d")

                transaction = {
                    "transaction_id": f"manual_{len(st.session_state.all_transactions) + len(transactions)}",
                    "account_id": "manual_upload",
                    "account_name": "Manual Upload",
                    "institution_id": "manual",
                    "institution_name": "Manual Upload",
                    "date": date_str,
                    "name": row["vendor"],
                    "amount": amount,
                    "category": [row["category"]] if "category" in row else ["Uncategorized"],
                    "category_id": "manual",
                    "pending": False,
                    "payment_channel": "other",
                    "transaction_type": "special",
                    "merchant_name": row["vendor"],
                    "source": "manual_upload",
                    "authorized_date": date_str,
                    "authorized_datetime": row[date_col].isoformat(),
                    "datetime": row[date_col].isoformat(),
                    "payment_method": "other",
                    "payment_processor": None,
                    "personal_finance_category": {
                        "primary": row["category"] if "category" in row else "Uncategorized",
                        "detailed": row["category"] if "category" in row else "Uncategorized"
                    }
                }
                transactions.append(transaction)

            st.session_state.all_transactions.extend(transactions)
            st.session_state.transactions = st.session_state.all_transactions.copy()
            return len(transactions)
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return 0

def show_add_bank_account():
    st.title("🏦 Connect Your Bank Account")
    
    # Initialize transaction storage if not exists
    if 'all_transactions' not in st.session_state:
        st.session_state.all_transactions = []
    if 'transactions' not in st.session_state:
        st.session_state.transactions = []
    
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
                    value=datetime.now() - timedelta(days=30)
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.now()
                )

            if st.button("Get Transactions", use_container_width=True):
                st.info(f"📆 Date Range: `{start_date}` to `{end_date}`")
                
                # Fetch transactions for each selected account
                plaid_transactions = []
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
                            "Account": tx.get("account_name", ""),
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
        st.info("""
        📝 Upload your bank statement in CSV format to import transactions.
        
        Expected CSV format:
        ```
        vendor,amount ($),category
        Walmart,123.45,Shopping
        Amazon,-45.67,Online Shopping
        ```
        
        Note: 
        - Positive amounts are expenses
        - Negative amounts are income
        - Category is optional
        """)
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a bank statement file",
            type=["csv"],
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
                            # Display simplified transaction table
                            table = [
                                {
                                    "Date": tx["date"],
                                    "Name": tx["name"],
                                    "Amount ($)": tx["amount"],
                                    "Category": ", ".join(tx["category"]),
                                    "Source": tx["source"]
                                }
                                for tx in st.session_state.transactions[-num_transactions:]  # Show only newly added
                            ]
                            st.dataframe(table, use_container_width=True)
                    else:
                        st.error("No transactions were imported. Please check the file format.") 