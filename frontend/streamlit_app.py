# frontend/app.py
import streamlit as st
import sys
from pathlib import Path
from views.AddBankAccount import show_add_bank_account

# Add both frontend and project root to Python path
frontend_path = Path(__file__).parent
project_root = frontend_path.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Set page config
st.set_page_config(
    page_title="AI Finance Manager",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "current_page" not in st.session_state:
    st.session_state["current_page"] = st.query_params.get("page", "home")

# Custom CSS
st.markdown("""
    <style>
        section[data-testid="stSidebar"] > div {
            background-color: #0f172a;
            padding: 1.5rem 1rem;
        }
        .sidebar-logo {
            display: flex;
            align-items: center;
            gap: 0.875rem;
            margin-bottom: 2.5rem;
            padding: 0 0.5rem;
        }
        .logo-icon {
            width: 2.25rem;
            height: 2.25rem;
            background-color: #1e293b;
            border-radius: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
        }
        .company-name {
            color: #f8fafc;
            font-size: 1.125rem;
            font-weight: 500;
        }
        .nav-button {
            width: 100%;
            color: #e2e8f0;
            border: none;
            text-align: left;
            padding: 0.625rem 0.875rem;
            margin: 0.125rem 0;
            border-radius: 0.375rem;
            cursor: pointer;
            font-size: 0.9375rem;
            transition: background-color 0.15s ease;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            background-color: transparent;
            font-weight: 400;
            line-height: 1.5;
        }
        .nav-button:hover {
            background-color: rgba(148, 163, 184, 0.1);
        }
        .nav-selected {
            background-color: #334155 !important;
            color: #ffffff;
        }
        .nav-wrapper {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            padding: 0 0.25rem;
        }
        .nav-button:focus {
            outline: none;
            box-shadow: none;
        }
        #MainMenu, footer, header {visibility: hidden;}
        section[data-testid="stSidebar"] .block-container {
            padding: 0;
        }
        /* Fix button width consistency */
        .stButton > button {
            width: 100% !important;
        }
        /* Ensure icons are consistently sized */
        .nav-button span {
            font-size: 1.125rem;
            min-width: 1.5rem;
            text-align: center;
        }
        /* Auto-scroll behavior */
        div.element-container:first-of-type {
            scroll-margin-top: 0;
        }
        
        /* Smooth scrolling */
        .main {
            scroll-behavior: smooth;
        }
    </style>
    <script>
        // More robust scroll to top function
        function scrollToTop() {
            setTimeout(function() {
                window.parent.document.querySelector('section.main').scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            }, 100);
        }
        
        // Call on page load
        window.addEventListener('load', scrollToTop);
        
        // Also call when Streamlit has finished re-running
        window.addEventListener('streamlit:render', scrollToTop);
    </script>
""", unsafe_allow_html=True)

# Logo and App Title
st.sidebar.markdown("""
    <div class="sidebar-logo">
        <div class="logo-icon">💰</div>
        <div class="company-name">FinanceAI</div>
    </div>
""", unsafe_allow_html=True)

# Navigation
pages = [
    ("🏠", "Home", "home"),
    ("🏦", "Add Bank Account", "add_bank"),
    ("📈", "Spending Insights", "insights"),
    ("📊", "Budget Tracking", "budget"),
    ("🔔", "Bill Reminders", "bills"),
    ("💬", "AI Financial Advisor", "chatbot")
]

st.sidebar.markdown('<div class="nav-wrapper">', unsafe_allow_html=True)
for icon, label, page in pages:
    selected = "nav-button nav-selected" if st.session_state["current_page"] == page else "nav-button"
    if st.sidebar.button(f"{icon} {label}", key=page):
        st.session_state["current_page"] = page
        # Update URL when clicking navigation
        st.query_params["page"] = page
        st.rerun()
    st.sidebar.markdown(f"""
        <script>
        var btn = window.parent.document.querySelector('button[key="nav_{page}"]');
        if (btn) {{
            btn.className = '{selected}';
        }}
        </script>
    """, unsafe_allow_html=True)
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Import views
from views.Home import show_home
from views.BudgetTracker import show_budget_tracker
from views.Insights import show_insights
from views.BillReminders import show_bill_reminders
from views.Chatbot import show_chatbot

# Handle Plaid callback status
status = st.query_params.get("status")
institution_name = st.query_params.get("institution_name")
error = st.query_params.get("error")

if status:
    if status == "success" and institution_name:
        st.success(f"✅ Successfully linked {institution_name}!")
        # Update current page to add_bank
        st.session_state["current_page"] = "add_bank"
        # Clear status params but keep page param
        current_page = st.query_params.get("page", "add_bank")
        st.query_params.clear()
        st.query_params["page"] = current_page
    elif status == "error" and error:
        st.error(f"❌ Error: {error}")
        st.session_state["current_page"] = "add_bank"
        current_page = st.query_params.get("page", "add_bank")
        st.query_params.clear()
        st.query_params["page"] = current_page
    elif status == "cancelled":
        st.info("ℹ️ Bank linking was cancelled.")
        st.session_state["current_page"] = "add_bank"
        current_page = st.query_params.get("page", "add_bank")
        st.query_params.clear()
        st.query_params["page"] = current_page

# Page rendering based on session state
if st.session_state["current_page"] == "home":
    show_home()
elif st.session_state["current_page"] == "add_bank":
    show_add_bank_account()
elif st.session_state["current_page"] == "budget":
    show_budget_tracker()
elif st.session_state["current_page"] == "insights":
    show_insights()
elif st.session_state["current_page"] == "bills":
    show_bill_reminders()
elif st.session_state["current_page"] == "chatbot":
    show_chatbot()
