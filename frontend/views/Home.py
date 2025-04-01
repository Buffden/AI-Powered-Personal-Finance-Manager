import streamlit as st
import requests
import streamlit.components.v1 as components
from datetime import datetime, timedelta, date

def show_home():
    # Add the FinanceAI logo and title in the main content area
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 2rem;">
            <div style="background-color: #1a2640; padding: 10px; border-radius: 8px;">
                <span style="font-size: 24px;">💰</span>
            </div>
            <h1 style="margin: 0; color: white; font-size: 24px;">FinanceAI</h1>
        </div>
    """, unsafe_allow_html=True)

    st.title("🏦 Connect Your Bank – AI Finance Manager")

    # 🔗 Step 1: Create Link Token (triggered from backend)
    st.header("🔗 Generate Plaid Link Token")

    if st.button("Generate Link Token"):
        response = requests.post("http://localhost:5050/api/plaid/create_link_token")
        
        if response.status_code == 200:
            try:
                data = response.json()
                link_token = data.get("link_token")
                st.session_state["link_token"] = link_token
                st.success("✅ Link Token created successfully.")
                st.code(link_token)

                # 💡 Instruction for user
                st.markdown("### 🔐 Open Plaid in a new tab to connect your bank")
                st.markdown(
                    """
                    1. Click the button below to open Plaid in a new tab  
                    2. Complete the flow (you can click "Continue without saving")  
                    3. Then manually copy the `public_token` from the browser DevTools console (we'll automate later!)  
                    """
                )

                # 🧠 Open Plaid in new tab
                plaid_link_url = f"https://cdn.plaid.com/link/v2/stable/link.html?token={st.session_state['link_token']}"
                js_open_new_tab = f"""
                <script>
                window.open("{plaid_link_url}", "_blank");
                </script>
                """
                components.html(js_open_new_tab, height=0)

                # Optional: let user paste public_token manually
                st.text_input("Paste public_token here:", key="manual_public_token")

            except Exception as e:
                st.error("✅ Token received, but response couldn't be parsed.")
                st.code(response.text)
        else:
            st.error(f"❌ Link token generation failed. Status: {response.status_code}")
            try:
                st.write(response.json())
            except Exception:
                st.warning("Non-JSON server response:")
                st.code(response.text)

    # 🧪 Step 2: Simulate Public Token Exchange
    st.header("🔁 Simulate Public Token Exchange (Dev Mode Only)")
    public_token = st.text_input("Paste sandbox public_token here (e.g., 'public-sandbox-xxx')")

    if st.button("Exchange Public Token"):
        res = requests.post("http://localhost:5050/api/plaid/exchange_public_token", json={
            "public_token": public_token
        })
        if res.status_code == 200:
            st.session_state["access_token"] = res.json().get("access_token")
            st.success("🎉 Access Token received!")
            st.code(st.session_state["access_token"])
        else:
            st.error("❌ Token exchange failed.")
            try:
                st.write(res.json())
            except Exception:
                st.warning("Non-JSON server response:")
                st.code(res.text)

    # 📄 Step 3: Get Transactions
    st.header("📄 View Fetched Transactions")

    # 📆 Let user pick date range
    start_date = st.date_input("Start Date", date.today() - timedelta(days=30))
    end_date = st.date_input("End Date", date.today())

    if st.button("Get Transactions"):
        st.info(f"📆 Date Range: `{start_date}` to `{end_date}`")

        tx_response = requests.post("http://localhost:5050/api/plaid/get_transactions", json={
            "start_date": str(start_date),
            "end_date": str(end_date)
        })

        if tx_response.status_code == 200:
            data = tx_response.json()
            transactions = data.get("transactions", [])
            st.session_state['transactions'] = transactions
            if not transactions:
                st.warning("No transactions found.")
            else:
                st.success(f"Found {len(transactions)} transactions.")
                # 💡 Display simplified transaction table
                table = [
                    {
                        "Date": tx["date"],
                        "Name": tx["name"],
                        "Amount ($)": tx["amount"],
                        "Category": ", ".join(tx.get("category", []))
                    }
                    for tx in transactions
                ]
                st.dataframe(table, use_container_width=True)
                st.session_state["transactions"] = transactions
        else:
            st.error("❌ Failed to fetch transactions.")
            try:
                st.write(tx_response.json())
            except Exception:
                st.code(tx_response.text)
