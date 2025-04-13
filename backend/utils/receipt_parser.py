from PIL import Image
from datetime import datetime
import re
import os
import pandas as pd
import streamlit as st
from openai import OpenAI
import base64
import requests
from io import BytesIO
from backend.utils.config import Config
from frontend.components.AccountSelector import add_bank_to_state
import uuid
from dateutil import parser

# Get OpenAI API key
api_key = Config.get_openai_api_key()

def extract_text_from_image(image) -> str:
    client = OpenAI()
    img = Image.open(image).convert("RGB")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    encoded_image = base64.b64encode(img_bytes).decode("utf-8")

    try:
        response = client.chat.completions.create(
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
        return response.choices[0].message.content
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

    # Enhanced date parsing with multiple formats
    date_patterns = [
        # Common date formats
        r"\b(\d{4}[-/]\d{2}[-/]\d{2})\b",  # YYYY-MM-DD or YYYY/MM/DD
        r"\b(\d{2}[-/]\d{2}[-/]\d{4})\b",  # DD-MM-YYYY or DD/MM/YYYY
        r"\b(\d{2}[-/]\d{2}[-/]\d{2})\b",  # DD-MM-YY or DD/MM/YY
        # Month names
        r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b"
    ]

    parsed_date = None
    for pattern in date_patterns:
        date_match = re.search(pattern, text, re.IGNORECASE)
        if date_match:
            date_str = date_match.group(0)
            try:
                # Try different date formats
                for fmt in [
                    "%Y-%m-%d", "%Y/%m/%d",  # YYYY-MM-DD
                    "%d-%m-%Y", "%d/%m/%Y",  # DD-MM-YYYY
                    "%d-%m-%y", "%d/%m/%y",  # DD-MM-YY
                    "%d %b %Y", "%d %B %Y",  # DD Mon YYYY
                    "%b %d %Y", "%B %d %Y",  # Mon DD YYYY
                    "%b %d, %Y", "%B %d, %Y"  # Mon DD, YYYY
                ]:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt)
                        if parsed_date.year < 100:  # Fix 2-digit years
                            parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                        break
                    except ValueError:
                        continue
                if parsed_date:
                    break
            except:
                continue

    # If no date found or parsing failed, use today's date
    if not parsed_date:
        parsed_date = datetime.now()

    # Format date consistently for the application
    formatted_date = parsed_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
    return vendor, amount, formatted_date


def categorize_transaction(vendor: str, text: str):
    try:
        client = OpenAI()
        prompt = f"""
        You are a smart finance assistant. Analyze the receipt details below and return the best category.

        Vendor: {vendor}
        Receipt Contents:
        {text}
        If you're adding more than a word, then make the first letter of each important word capitalized.
        Your response must be similar to these: Food and Drink, Groceries, Health, Shopping, Bills and Utilities, Transportation, Rent, Entertainment, Other.
        """
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        category = response.choices[0].message.content.strip().capitalize()
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


def add_transaction_to_state(vendor, amount, date, text):
    """Add a receipt transaction to the state."""
    if 'transactions' not in st.session_state:
        st.session_state.transactions = []
    
    # Initialize linked_banks if it doesn't exist
    if 'linked_banks' not in st.session_state:
        st.session_state.linked_banks = {
            'manual_receipts': {
                'account_id': 'manual_upload',
                'account_name': 'Receipt Transactions',
                'account_type': 'manual',
                'balance': 0.0
            }
        }
    
    # Create a unique transaction ID
    transaction_id = str(uuid.uuid4())
    
    # Parse and standardize the date format
    try:
        # Handle different date formats
        if isinstance(date, str):
            if "GMT" in date:
                # Try parsing GMT format
                try:
                    parsed_date = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S GMT")
                except ValueError:
                    # Try alternate GMT format
                    parsed_date = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S")
            else:
                # Try other common formats
                try:
                    parsed_date = pd.to_datetime(date)
                except:
                    # Try parsing with dateutil as last resort
                    parsed_date = parser.parse(date)
        else:
            # If date is already a datetime object
            parsed_date = date if isinstance(date, datetime) else datetime.now()
        
        # Format date consistently as string
        formatted_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"Date parsing error: {e} for date: {date}")
        # Fallback to current datetime if parsing fails
        formatted_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format the transaction to match Plaid transaction format
    transaction = {
        "transaction_id": transaction_id,
        "date": formatted_date,
        "name": vendor,
        "merchant_name": vendor,
        "amount": float(amount),
        "category": [categorize_transaction(vendor, text)],  # Convert to list format
        "source": "manual_upload",
        "account_id": "manual_upload",  # Changed to match the account selector
        "account_name": "Receipt Transactions"
    }
  # 🔁 Duplicate check (same vendor, amount, and date)
    for existing in st.session_state.transactions:
        if (
            existing["name"].lower() == vendor.lower() and
            abs(existing["amount"] - float(amount)) < 0.01 and
            existing["date"].split()[0] == formatted_date.split()[0]
        ):
            st.session_state.duplicate_warning = True
            return None

    # Add transaction and sort by date
    st.session_state.transactions.append(transaction)
    st.session_state.transactions.sort(key=lambda x: x["date"], reverse=True)  # Sort newest first
    
    # Also add to all_transactions if it exists and sort it
    if 'all_transactions' in st.session_state:
        st.session_state.all_transactions.append(transaction)
        st.session_state.all_transactions.sort(key=lambda x: x["date"], reverse=True)
    
    # Reset any cached data in session state to force refresh of views
    if 'chart_summary' in st.session_state:
        del st.session_state['chart_summary']
    if 'chart_month' in st.session_state:
        del st.session_state['chart_month']
    if 'categorized_transactions' in st.session_state:
        del st.session_state['categorized_transactions']
    if 'insights_data' in st.session_state:
        del st.session_state['insights_data']
    
    # Force refresh of account selector
    if 'linked_banks' in st.session_state and 'manual_receipts' in st.session_state.linked_banks:
        del st.session_state.linked_banks['manual_receipts']
    
    # Return the transaction ID for reference
    return transaction_id

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
