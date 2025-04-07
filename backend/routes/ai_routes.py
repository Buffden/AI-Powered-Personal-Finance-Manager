# backend/routes/ai_routes.py
from flask import Blueprint
from openai import OpenAI

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

@ai_bp.route("/test", methods=["GET"])

def transactions_to_text(transactions):
    return "\n".join([
        f"{tx['date']} - {tx['name']} - ${tx['amount']} - {', '.join(tx.get('category', []))}"
        for tx in transactions
    ])

def chat_with_advisor(api_key, transactions, conversation_history, user_input, user_goals=None):
    client = OpenAI(api_key=api_key)

    if not conversation_history:
        transaction_text = transactions_to_text(transactions)
        intro = f"User's financial goals: {user_goals}" if user_goals else ""

        # Only system prompt + user’s visible message
        conversation_history = [
            {
                "role": "system",
                "content": (
                    "You are an AI-powered financial advisor. Use the transaction data provided (not shown to the user) "
                    "to offer clear advice on spending, saving, budgeting, and financial planning."
                )
            }
        ]

        # Inject transactions invisibly for GPT, but not shown in chat
        user_prompt = (
            f"{intro}\n\nHere is the user's transaction data:\n{transaction_text}\n\n"
            "Now provide personalized financial advice."
        )
        conversation_history.append({"role": "user", "content": user_prompt})

        # Add visible message in chat as if user just said "Give me advice"
        conversation_history.append({"role": "user", "content": "Can you review my spending and give me financial advice?"})

    else:
        # Follow-up question
        conversation_history.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation_history
    )


    reply = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": reply})

    return reply, conversation_history
