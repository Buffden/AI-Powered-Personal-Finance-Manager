from PIL import Image
from datetime import datetime
import re
import os
import pandas as pd
import streamlit as st
import openai
import base64
import requests
from io import BytesIO
from backend.utils.config import Config
from frontend.components.AccountSelector import add_bank_to_state
# Get OpenAI API key
api_key = Config.get_openai_api_key()
openai.api_key = api_key

def extract_text_from_image(image) -> str:
    img = Image.open(image).convert("RGB")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    encoded_image = base64.b64encode(img_bytes).decode("utf-8")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "From this receipt, extract only the vendor/store name. "
                    "Do not describe or summarize anything else. Just give the store name as plain text. Also give the total amount and date. Give everything in order, don't mention a label, give direct information"
           },
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_image}"}}
                    ]
                }
            ],
            max_tokens=2000
        )
        return response.choices[0].message['content']
    except Exception as e:
        return f"Error with OpenAI Vision API: {str(e)}"

def extract_receipt_fields(text: str):
    lines = text.split("\n")
    vendor = lines[0].strip() if lines else "Unknown Vendor"

    amount = 0.0
    candidates = []

    for line in lines:
        if re.search(r"(total|amount|balance)", line, re.IGNORECASE):
            matches = re.findall(r"[\$s]?([1-9]\d{0,3}[.,]\d{2})", line)
            for match in matches:
                match = match.replace(",", ".")
                try:
                    val = float(match)
                    if val > 0:
                        candidates.append(val)
                except:
                    continue

    if not candidates:
        matches = re.findall(r"[\$s]?([1-9]\d{0,3}[.,]\d{2})", text)
        for match in matches:
            match = match.replace(",", ".")
            try:
                val = float(match)
                if val > 0:
                    candidates.append(val)
            except:
                continue

    filtered = [amt for amt in candidates if 1 <= amt <= 1000]
    if filtered:
        amount = max(filtered)

    date_match = re.search(r"\b(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})\b", text)
    try:
        if date_match:
            try:
                parsed_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
            except:
                parsed_date = datetime.strptime(date_match.group(1), "%d-%m-%Y")
        else:
            parsed_date = datetime.now()
    except:
        parsed_date = datetime.now()

    # ✅ Format date to match Plaid-style HTTP/GMT format
    formatted_date = parsed_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
    return vendor, amount, formatted_date


def categorize_transaction(vendor: str, text: str):
    try:
        prompt = f"""
        You are a smart finance assistant. Analyze the receipt details below and return the best category.

        Vendor: {vendor}
        Receipt Contents:
        {text}

        Your response must be similar to these: Food and Drink, Groceries, Health, Shopping, Bills and Utilities, Transportation, Rent, Entertainment, Other.
        """
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        category = response.choices[0].message['content'].strip().capitalize()
        return category
    except:
        return "Uncategorized"

def append_to_csv(new_txn, csv_path="transactions.csv"):
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        df = pd.DataFrame(columns=["Date", "Name", "Amount ($)", "Category"])

    df = pd.concat([df, pd.DataFrame([new_txn])], ignore_index=True)
    df.to_csv(csv_path, index=False)


def add_transaction_to_state(vendor, amount, tx_date, text):
    # 🔍 Categorize based on text (simple logic or integrate your own)
    category = categorize_transaction(vendor, text)

    # ✅ Parse the date and convert to Plaid-style format
    parsed_date = pd.to_datetime(tx_date)
    formatted_date = parsed_date.strftime("%a, %d %b %Y %H:%M:%S GMT")

    # ✅ Ensure session state keys exist
    if "linked_banks" not in st.session_state:
        st.session_state.linked_banks = {}
    if "selected_accounts" not in st.session_state:
        st.session_state.selected_accounts = {}
    if "all_transactions" not in st.session_state:
        st.session_state.all_transactions = []
    if "transactions" not in st.session_state:
        st.session_state.transactions = []

    # ✅ Define the manual upload bank account
    manual_account = {
        "account_id": "manual_upload",
        "name": "Manual Upload",
        "type": "other",
        "subtype": "other",
        "mask": "0000",
        "official_name": "Manual Receipt Upload",
        "balances": {
            "available": None,
            "current": None,
            "limit": None,
            "iso_currency_code": "USD"
        }
    }

    # ✅ Register the bank if it doesn't exist
    if (
        "manual" not in st.session_state.linked_banks or
        not any(acc["account_id"] == "manual_upload"
                for acc in st.session_state.linked_banks.get("manual", {}).get("accounts", []))
    ):
        add_bank_to_state("Manual Upload", "manual", [manual_account])

    # ✅ Force-select the account so it appears in filtered views
    if "manual" not in st.session_state.selected_accounts:
        st.session_state.selected_accounts["manual"] = {}
    st.session_state.selected_accounts["manual"]["manual_upload"] = True

    # ✅ Build transaction dict in Plaid-like format
    new_txn = {
        "transaction_id": f"receipt_{len(st.session_state.all_transactions)}",
        "account_id": "manual_upload",
        "account_name": "Manual Upload",
        "institution_id": "manual",
        "institution_name": "Manual Upload",
        "date": formatted_date,
        "name": vendor,
        "amount": amount,
        "category": [category],
        "category_id": "manual",
        "pending": False,
        "payment_channel": "other",
        "transaction_type": "special",
        "merchant_name": vendor,
        "source": "manual_upload",
        "authorized_date": formatted_date,
        "authorized_datetime": parsed_date.isoformat(),
        "datetime": parsed_date.isoformat(),
        "payment_method": "other",
        "payment_processor": None,
        "personal_finance_category": {
            "primary": category,
            "detailed": category
        }
    }

    # ✅ Avoid duplicates
    for tx in st.session_state.all_transactions or st.session_state.transactions:
        if tx["name"] == vendor and abs(tx["amount"] - amount) < 0.01 and tx["date"] == formatted_date:
            st.warning("⚠️ This transaction already exists.")
            return

    # ✅ Append to transactions
    st.session_state.all_transactions.append(new_txn)
    st.session_state.transactions = st.session_state.all_transactions.copy()

def delete_receipt_transaction(transaction_id):
    # Remove from all_transactions
    if "all_transactions" in st.session_state:
        st.session_state.all_transactions = [
            tx for tx in st.session_state.all_transactions
            if tx["transaction_id"] != transaction_id
        ]

    # Update filtered transactions
    if "transactions" in st.session_state:
        st.session_state.transactions = [
            tx for tx in st.session_state.transactions
            if tx["transaction_id"] != transaction_id
        ]
