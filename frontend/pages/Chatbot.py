import streamlit as st
import io
from backend.routes.ai_routes import chat_with_advisor

st.set_page_config(page_title="AI Financial Advisor", layout="centered")
st.title("💬 AI Financial Advisor")

# Session state setup
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'chat_started' not in st.session_state:
    st.session_state.chat_started = False

api_key = st.text_input("🔐 Enter your OpenAI API Key", type="password")

# Goals input (only at the start)
if not st.session_state.chat_started:
    user_goals = st.text_area("🎯 Enter your financial goals (optional):", placeholder="e.g., save for a home, car, or emergency...")

# Check if transactions are available
if 'transactions' not in st.session_state:
    st.warning("⚠️ Please fetch transactions from the Home page first.")
else:
    transactions = st.session_state['transactions']

    # Start chat on button press
    if not st.session_state.chat_started and st.button("🚀 Start Financial Advice Chat"):
        if not api_key:
            st.error("Please enter your OpenAI API key.")
        else:
            with st.spinner("Analyzing your transactions..."):
                initial_reply, history = chat_with_advisor(
                    api_key=api_key,
                    transactions=transactions,
                    conversation_history=[],
                    user_input="Provide financial advice based on my transactions.",
                    user_goals=user_goals
                )
                st.session_state.conversation_history = history
                st.session_state.chat_started = True
                st.rerun()

    # Show chat
    if st.session_state.chat_started:
        st.markdown("### 📌 Conversation")

        for msg in st.session_state.conversation_history:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(msg["content"])
            elif msg["role"] == "assistant":
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])

        # Input box for user follow-up
        followup = st.chat_input("Ask a question about your spending, savings, or financial goals...")

        if followup and api_key:
            with st.spinner("Advisor is thinking..."):
                reply, updated_history = chat_with_advisor(
                    api_key=api_key,
                    transactions=transactions,
                    conversation_history=st.session_state.conversation_history,
                    user_input=followup
                )
                st.session_state.conversation_history = updated_history
                st.rerun()

        # 💾 Export chat log
        if st.session_state.conversation_history:
            export_format = st.radio("💾 Export Format", ["Markdown (.md)", "Text (.txt)"], horizontal=True)

            if st.button("📥 Save Chat Log"):
                buffer = io.StringIO()

                for msg in st.session_state.conversation_history:
                    role = "User" if msg['role'] == 'user' else "Advisor"
                    content = msg['content']
                    if export_format.startswith("Markdown"):
                        buffer.write(f"### **{role}:**\n{content}\n\n")
                    else:
                        buffer.write(f"{role}:\n{content}\n\n")

                file_ext = "md" if export_format.startswith("Markdown") else "txt"
                filename = f"financial_chat_log.{file_ext}"

                st.download_button(
                    label="⬇️ Download Chat Log",
                    data=buffer.getvalue(),
                    file_name=filename,
                    mime="text/plain" if file_ext == "txt" else "text/markdown"
                )
