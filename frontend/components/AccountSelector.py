import streamlit as st
import pandas as pd

def initialize_account_state():
    """Initialize account selection state if not exists"""
    if 'linked_banks' not in st.session_state:
        st.session_state.linked_banks = {}  # Store bank and account info
    if 'selected_accounts' not in st.session_state:
        st.session_state.selected_accounts = {}  # Store selection state

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
    
    if not st.session_state.linked_banks:
        if show_title:
            st.warning("No banks linked. Please add a bank account first.")
        return []

    if show_title:
        st.subheader("🏦 Select Accounts")

    selected_accounts = []
    
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
                    is_selected = st.checkbox(
                        f"{acc['name']} ({acc['type']}) - {acc['mask']}",
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
                selected_data.append({
                    'Bank': bank_info['institution_name'],
                    'Account Name': acc['name'],
                    'Account Type': acc['type'],
                    'Last 4 Digits': acc['mask'],
                    'Account ID': acc['account_id']
                })
    
    return pd.DataFrame(selected_data) if selected_data else None 