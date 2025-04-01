import streamlit as st

def show_home():
    # Welcome section
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="font-size: 2.5rem; margin-bottom: 1rem;">Welcome to FinanceAI</h1>
            <p style="font-size: 1.25rem; color: #94a3b8; margin-bottom: 2rem;">
                Your AI-powered personal finance manager
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Features grid
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div style="padding: 1.5rem; background: #1e293b; border-radius: 1rem; margin-bottom: 1rem;">
                <h3 style="color: #f8fafc; margin-bottom: 0.5rem;">🏦 Bank Integration</h3>
                <p style="color: #94a3b8;">Securely connect your bank accounts and track all your transactions in one place.</p>
            </div>
            
            <div style="padding: 1.5rem; background: #1e293b; border-radius: 1rem; margin-bottom: 1rem;">
                <h3 style="color: #f8fafc; margin-bottom: 0.5rem;">📊 Budget Tracking</h3>
                <p style="color: #94a3b8;">Set and monitor budgets for different categories. Get alerts when you're close to limits.</p>
            </div>
            
            <div style="padding: 1.5rem; background: #1e293b; border-radius: 1rem;">
                <h3 style="color: #f8fafc; margin-bottom: 0.5rem;">📈 Spending Insights</h3>
                <p style="color: #94a3b8;">Visualize your spending patterns and get actionable insights to save more.</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div style="padding: 1.5rem; background: #1e293b; border-radius: 1rem; margin-bottom: 1rem;">
                <h3 style="color: #f8fafc; margin-bottom: 0.5rem;">🔔 Bill Reminders</h3>
                <p style="color: #94a3b8;">Never miss a payment with smart bill detection and timely reminders.</p>
            </div>
            
            <div style="padding: 1.5rem; background: #1e293b; border-radius: 1rem; margin-bottom: 1rem;">
                <h3 style="color: #f8fafc; margin-bottom: 0.5rem;">💬 AI Financial Advisor</h3>
                <p style="color: #94a3b8;">Get personalized financial advice and answers to your money questions.</p>
            </div>
            
            <div style="padding: 1.5rem; background: #1e293b; border-radius: 1rem;">
                <h3 style="color: #f8fafc; margin-bottom: 0.5rem;">🔒 Secure & Private</h3>
                <p style="color: #94a3b8;">Your financial data is encrypted and never shared with third parties.</p>
            </div>
        """, unsafe_allow_html=True)

    # Get Started button
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h2 style="color: #f8fafc; margin-bottom: 1rem;">Ready to take control of your finances?</h2>
            <p style="color: #94a3b8; margin-bottom: 1.5rem;">Connect your bank account to get started</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Connect Your Bank Account", use_container_width=True):
        st.session_state["current_page"] = "add_bank"
        st.rerun()
