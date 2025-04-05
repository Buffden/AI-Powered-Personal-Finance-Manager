from PIL import Image
from datetime import datetime
import re
import os
import pandas as pd
import numpy as np
import streamlit as st
import openai
import config

openai.api_key = config.get_openai_api_key()
def extract_text_from_image(image) -> str:
    import easyocr
    reader = easyocr.Reader(['en'])
    img = Image.open(image).convert("RGB")
    result = reader.readtext(np.array(img), detail=0)
    return "\n".join(result)

def extract_receipt_fields(text: str):
    lines = text.split("\n")
    vendor = lines[0].strip() if lines else "Unknown Vendor"

    amount_match = re.search(r"(Total|Amount|Due)\s*[:$]?\s*(\d+\.\d{2})", text, re.IGNORECASE)
    amount = float(amount_match.group(2)) if amount_match else 0.0

    date_match = re.search(r"\b(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})\b", text)
    try:
        parsed_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").date() if date_match else datetime.today().date()
    except:
        try:
            parsed_date = datetime.strptime(date_match.group(1), "%d-%m-%Y").date()
        except:
            parsed_date = datetime.today().date()

    return vendor, amount, parsed_date

def categorize_transaction(vendor: str):
    prompt = f"""
    Categorize the following vendor into one of these categories:
    [Groceries, Entertainment, Utilities, Rent, Transportation, Restaurants, Uncategorized]

    Vendor: {vendor}
    Category:
    """
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=10,
            temperature=0
        )
        category = response.choices[0].text.strip()
        return category if category else "Uncategorized"
    except:
        return "Uncategorized"

def append_to_csv(new_txn, csv_path="transactions.csv"):
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        df = pd.DataFrame(columns=["Date", "Name", "Amount ($)", "Category"])

    df = pd.concat([df, pd.DataFrame([new_txn])], ignore_index=True)
    df.to_csv(csv_path, index=False)

def add_transaction_to_state(vendor, amount, tx_date):
    category = categorize_transaction(vendor)

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
