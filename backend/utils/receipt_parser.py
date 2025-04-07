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
        parsed_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").date() if date_match else datetime.today().date()
    except:
        try:
            parsed_date = datetime.strptime(date_match.group(1), "%d-%m-%Y").date()
        except:
            parsed_date = datetime.today().date()

    return vendor, amount, parsed_date

def categorize_transaction(vendor: str, text: str):
    try:
        prompt = f"""
        You are a smart finance assistant. Analyze the receipt details below and return the best category.

        Vendor: {vendor}
        Receipt Contents:
        {text}

        Your response must be exactly one of: Food and Drink, Groceries, Health, Shopping, Bills and Utilities, Transportation, Rent, Entertainment, Other.
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
    category = categorize_transaction(vendor, text)

    new_txn = {
        "transaction_id": f"receipt_{len(st.session_state.get('transactions', []))}",
        "account_id": "manual_upload",
        "account_name": "Manual Upload",
        "institution_id": "manual",
        "institution_name": "Manual Upload",
        "date": str(tx_date),
        "name": vendor,
        "amount": amount,
        "category": [category],
        "category_id": "manual",
        "pending": False,
        "payment_channel": "other",
        "transaction_type": "special",
        "merchant_name": vendor,
        "source": "manual_upload",
        "authorized_date": str(tx_date),
        "authorized_datetime": datetime.now().isoformat(),
        "datetime": datetime.now().isoformat(),
        "payment_method": "other",
        "payment_processor": None,
        "personal_finance_category": {
            "primary": category,
            "detailed": category
        }
    }

    if "transactions" not in st.session_state:
        st.session_state.transactions = []
    st.session_state.transactions.append(new_txn)

    append_to_csv({
        "Date": tx_date,
        "Name": vendor,
        "Amount ($)": amount,
        "Category": category
    })
