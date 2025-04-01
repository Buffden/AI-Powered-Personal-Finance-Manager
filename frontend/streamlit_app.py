# frontend/app.py
import streamlit as st
import sys
from pathlib import Path

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
    st.session_state["current_page"] = "home"

# Custom CSS
st.markdown("""
    <style>
        section[data-testid="stSidebar"] > div {
            background-color: #111827;
            padding: 2rem 1rem;
        }
        .sidebar-logo {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 3rem;
            padding: 0 0.5rem;
        }
        .logo-icon {
            width: 3rem;
            height: 3rem;
            background-color: #1e293b;
            border-radius: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }
        .company-name {
            color: #ffffff;
            font-size: 1.5rem;
            font-weight: 500;
        }
        .nav-button {
            width: 100%;
            color: #e5e7eb;
            border: none;
            text-align: left;
            padding: 0.75rem 1rem;
            margin: 0.25rem 0;
            border-radius: 0.5rem;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            background-color: transparent;
        }
        .nav-button:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
        .nav-selected {
            background-color: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(6px);
        }
        .nav-wrapper {
            display: flex;
            flex-direction: column;
        }
        .nav-button:focus {
            outline: none;
            box-shadow: none;
        }
        #MainMenu, footer, header {visibility: hidden;}
        section[data-testid="stSidebar"] .block-container {
            padding: 0;
        }
    </style>
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
    ("📊", "Budget Tracking", "budget"),
    ("📈", "Spending Insights", "insights"),
    ("🔔", "Bill Reminders", "bills"),
    ("💬", "AI Financial Advisor", "chatbot")
]

st.sidebar.markdown('<div class="nav-wrapper">', unsafe_allow_html=True)
for icon, label, page in pages:
    selected = "nav-button nav-selected" if st.session_state["current_page"] == page else "nav-button"
    if st.sidebar.button(f"{icon} {label}", key=page):
        st.session_state["current_page"] = page
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

# Page rendering
if st.session_state["current_page"] == "home":
    show_home()
elif st.session_state["current_page"] == "budget":
    show_budget_tracker()
elif st.session_state["current_page"] == "insights":
    show_insights()
elif st.session_state["current_page"] == "bills":
    show_bill_reminders()
elif st.session_state["current_page"] == "chatbot":
    show_chatbot()
