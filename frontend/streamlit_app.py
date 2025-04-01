# Starter code for frontend/app.py
import streamlit as st
import sys
from pathlib import Path

# Add both frontend and project root to Python path
frontend_path = Path(__file__).parent
project_root = frontend_path.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Initialize session state for current page
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'

st.set_page_config(
    page_title="AI Finance Manager",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
    <style>
        /* Sidebar container styling */
        section[data-testid="stSidebar"] > div {
            background-color: rgb(17, 24, 39);
            padding: 1rem;
        }
        
        /* Logo and company name container */
        .sidebar-logo {
            margin: 25px 0 45px 0;
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 10px;
        }
        
        .logo-icon {
            width: 45px;
            height: 45px;
            background-color: rgb(30, 41, 59);
            padding: 10px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }
        
        .company-name {
            color: rgb(250, 250, 250);
            font-size: 20px;
            font-weight: 500;
        }
        
        /* Navigation button styling */
        .stButton > button {
            width: 100%;
            background-color: rgb(30, 41, 59);
            color: rgb(250, 250, 250);
            border: none;
            text-align: left !important;
            padding: 12px 16px;
            cursor: pointer;
            border-radius: 8px;
            margin: 4px 0;
            transition: all 0.2s ease;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            min-height: 48px;
        }
        
        /* Button states */
        .stButton > button:hover {
            background-color: rgb(41, 55, 80);
        }
        
        .stButton > button:active {
            background-color: rgb(51, 65, 90);
        }
        
        /* Selected button state */
        .selected-nav {
            background-color: rgb(51, 65, 90) !important;
        }
        
        /* Hide default Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Adjust button icon and text alignment */
        .stButton > button > div {
            display: flex !important;
            align-items: center !important;
            gap: 12px !important;
        }
        
        /* Remove default button styles */
        .stButton > button:focus {
            box-shadow: none !important;
        }
        
        /* Adjust sidebar padding */
        section[data-testid="stSidebar"] .block-container {
            padding-top: 0;
            padding-left: 0;
            padding-right: 0;
        }
    </style>
""", unsafe_allow_html=True)

# Add logo and company name to sidebar
st.sidebar.markdown("""
    <div class="sidebar-logo">
        <div class="logo-icon">💰</div>
        <div class="company-name">FinanceAI</div>
    </div>
""", unsafe_allow_html=True)

# Navigation buttons with session state management
active_page = st.session_state.current_page
for btn_data in [
    ("🏦", "Connect Bank", 'home'),
    ("📊", "Budget Tracking", 'budget'),
    ("📈", "Spending Insights", 'insights'),
    ("🔔", "Bill Reminders", 'bills'),
    ("💬", "AI Financial Advisor", 'chatbot')
]:
    icon, label, page = btn_data
    button_class = "selected-nav" if page == active_page else ""
    if st.sidebar.button(f"{icon} {label}", key=f"nav_{page}", 
                        use_container_width=True,
                        help=f"Navigate to {label}"):
        st.session_state.current_page = page

# Import views
from views.Home import show_home
from views.BudgetTracker import show_budget_tracker
from views.Insights import show_insights
from views.BillReminders import show_bill_reminders
from views.Chatbot import show_chatbot

# Main content area
if st.session_state.current_page == 'home':
    show_home()
elif st.session_state.current_page == 'budget':
    show_budget_tracker()
elif st.session_state.current_page == 'insights':
    show_insights()
elif st.session_state.current_page == 'bills':
    show_bill_reminders()
elif st.session_state.current_page == 'chatbot':
    show_chatbot()
