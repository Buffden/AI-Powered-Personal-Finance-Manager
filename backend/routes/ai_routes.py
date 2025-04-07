# backend/routes/ai_routes.py
from flask import Blueprint
import openai

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

def transactions_to_text(transactions):
    return "\n".join([
        f"{tx['date']} - {tx['name']} - ${tx['amount']} - {', '.join(tx.get('category', []))}"
        for tx in transactions
    ])

def chat_with_advisor(api_key, transactions, conversation_history, user_input, user_goals=None):
    openai.api_key = api_key

    if not conversation_history:
        # Inject data ONLY into the system prompt
        transaction_text = transactions_to_text(transactions)
        intro = f"User's financial goals: {user_goals}" if user_goals else ""

        conversation_history = [
            {
                "role": "system",
                "content": (
                    f"You are an AI-powered financial advisor.\n\n"
                    f"{intro}\n\n"
                    "Here is the user's transaction data:\n"
                    f"{transaction_text}\n\n"
                    "Use this data to provide personalized financial advice, including:\n"
                    "- Spending insights\n"
                    "- Budget suggestions\n"
                    "- Credit score improvement strategies (e.g., reducing high-interest spending, paying on time, avoiding overdrafts, maintaining low credit utilization)"
                )
            },
            {
                "role": "user",
                "content": "Can you review my spending and give me financial advice?"
            }
        ]

    else:
        # Follow-up questions
        conversation_history.append({"role": "user", "content": user_input})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation_history
    )

    reply = response["choices"][0]["message"]["content"]
    conversation_history.append({"role": "assistant", "content": reply})

    return reply, conversation_history

