import streamlit as st
import pandas as pd

def initialize_account_state():
    """Initialize account selection state if not exists"""
    if 'linked_banks' not in st.session_state:
        st.session_state.linked_banks = {}  # Store bank and account info
    if 'selected_accounts' not in st.session_state:
        st.session_state.selected_accounts = {}  # Store selection state
    
    # Add Receipt Transactions as a bank only if there are receipt transactions
    has_receipts = any(
        tx.get('source') == 'manual_upload' 
        for tx in st.session_state.get('transactions', [])
    )
    
    # Add or remove receipt transactions based on their existence
    if has_receipts:
        if 'manual_receipts' not in st.session_state.linked_banks:
            receipt_account = {
                'account_id': 'manual_upload',
                'name': 'Receipt Transactions',
                'type': 'receipts',
                'mask': None
            }
            st.session_state.linked_banks['manual_receipts'] = {
                'institution_name': '📷 Receipt Transactions',
                'institution_id': 'manual_receipts',
                'accounts': [receipt_account]
            }
            # Initialize selection state for receipt account
            if 'manual_receipts' not in st.session_state.selected_accounts:
                st.session_state.selected_accounts['manual_receipts'] = {
                    'manual_upload': True  # Default to selected
                }
    else:
        # Remove receipt transactions if no receipts exist
        if 'manual_receipts' in st.session_state.linked_banks:
            del st.session_state.linked_banks['manual_receipts']
        if 'manual_receipts' in st.session_state.selected_accounts:
            del st.session_state.selected_accounts['manual_receipts']

def update_account_selection(bank_id, account_id, is_selected):
    """Update the selection state of an account"""
    if bank_id not in st.session_state.selected_accounts:
        st.session_state.selected_accounts[bank_id] = {}
    st.session_state.selected_accounts[bank_id][account_id] = is_selected

def show_account_selector(show_title=True):
    """
    Render the account selector component
    Returns: List of selected account IDs
    """
    initialize_account_state()
    
    if show_title:
        st.subheader("🏦 Select Accounts")

    selected_accounts = []
    
    # Check if there are any real bank accounts (excluding receipt transactions)
    real_banks = {k: v for k, v in st.session_state.linked_banks.items() if k != 'manual_receipts'}
    if not real_banks:
        if show_title:
            st.warning("No banks linked. Please add a bank account first.")
        return []

    # Create expander for each bank
    for bank_id, bank_info in st.session_state.linked_banks.items():
        with st.expander(f"🏛️ {bank_info['institution_name']}", expanded=True):
            # Select All checkbox for this bank
            all_selected = all(
                st.session_state.selected_accounts.get(bank_id, {}).get(acc['account_id'], False)
                for acc in bank_info['accounts']
            )
            if st.checkbox(
                "Select All",
                value=all_selected,
                key=f"select_all_{bank_id}"
            ):
                # Select all accounts for this bank
                for acc in bank_info['accounts']:
                    update_account_selection(bank_id, acc['account_id'], True)
                    selected_accounts.append(acc['account_id'])
            else:
                # Individual account checkboxes
                for acc in bank_info['accounts']:
                    # Create account label based on available fields
                    if acc['type'] == 'receipts':
                        account_label = acc['name']
                    elif 'mask' in acc and acc['mask']:
                        account_label = f"{acc['name']} ({acc['type']}) - {acc['mask']}"
                    else:
                        account_label = f"{acc['name']} ({acc['type']})"
                    
                    is_selected = st.checkbox(
                        account_label,
                        value=st.session_state.selected_accounts.get(bank_id, {}).get(acc['account_id'], False),
                        key=f"account_{bank_id}_{acc['account_id']}"
                    )
                    update_account_selection(bank_id, acc['account_id'], is_selected)
                    if is_selected:
                        selected_accounts.append(acc['account_id'])
            
            # Show bank summary
            st.caption(f"Total Accounts: {len(bank_info['accounts'])}")

    return selected_accounts

def add_bank_to_state(institution_name, institution_id, accounts):
    """
    Add a new bank and its accounts to the session state
    """
    bank_id = institution_id
    st.session_state.linked_banks[bank_id] = {
        'institution_name': institution_name,
        'institution_id': institution_id,
        'accounts': accounts
    }
    
    # Initialize selection state for new accounts
    if bank_id not in st.session_state.selected_accounts:
        st.session_state.selected_accounts[bank_id] = {
            acc['account_id']: False for acc in accounts
        }

def get_selected_accounts_summary():
    """
    Get a summary of selected accounts
    Returns: DataFrame with bank and account details
    """
    selected_data = []
    
    for bank_id, bank_info in st.session_state.linked_banks.items():
        for acc in bank_info['accounts']:
            if st.session_state.selected_accounts.get(bank_id, {}).get(acc['account_id'], False):
                account_data = {
                    'Bank': bank_info['institution_name'],
                    'Account Name': acc['name'],
                    'Account Type': acc['type'],
                    'Account ID': acc['account_id']
                }
                # Only add mask if it exists
                if 'mask' in acc:
                    account_data['Last 4 Digits'] = acc['mask']
                selected_data.append(account_data)
    
    return pd.DataFrame(selected_data) if selected_data else None 