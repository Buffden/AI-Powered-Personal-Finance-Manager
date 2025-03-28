from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid import Configuration, ApiClient
from datetime import datetime, timedelta


load_dotenv()

plaid_bp = Blueprint("plaid", __name__)

# Plaid SDK Client Setup
configuration = Configuration(
    host="https://sandbox.plaid.com",
    api_key={
        "clientId": os.getenv("PLAID_CLIENT_ID"),
        "secret": os.getenv("PLAID_SECRET"),
    }
)
api_client = ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

ACCESS_TOKENS = {}  # ⚠️ TEMP STORAGE – use session/file/db in production

# 1️⃣ Create Link Token
@plaid_bp.route("/api/plaid/create_link_token", methods=["POST"])
def create_link_token():
    try:
        request_data = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id="demo-user-123"),
            client_name="AI Finance Manager",
            products=[Products("transactions")],
            country_codes=[CountryCode("US")],
            language="en"
        )
        response = client.link_token_create(request_data)
        print("🔐 ENV CHECK:", os.getenv("PLAID_CLIENT_ID"), os.getenv("PLAID_SECRET"))
        return jsonify({"link_token": response.to_dict()["link_token"]})

    except Exception as e:
        import traceback
        print("💥 Full Error Traceback:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# 2️⃣ Exchange Public Token for Access Token
@plaid_bp.route("/api/plaid/exchange_public_token", methods=["POST"])
def exchange_public_token():
    try:
        public_token = request.json.get("public_token")
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        access_token = exchange_response.to_dict()["access_token"]

        # Store it in-memory (temp)
        ACCESS_TOKENS["demo-user-123"] = access_token

        return jsonify({"access_token": access_token})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3️⃣ Fetch Mock Transactions
from datetime import datetime

@plaid_bp.route("/api/plaid/get_transactions", methods=["POST"])
def get_transactions():
    try:
        access_token = ACCESS_TOKENS.get("demo-user-123")
        if not access_token:
            return jsonify({"error": "No access token"}), 400

        # 🔁 Receive string dates from frontend
        data = request.json
        start_date_str = data.get("start_date")
        end_date_str = data.get("end_date")

        # ✅ Convert string to datetime.date
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        
        print("🔍 Access Token:", access_token)
        print("📆 Start Date:", start_date, type(start_date))
        print("📆 End Date:", end_date, type(end_date))

        # 💸 Build request for Plaid
        request_data = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
            options=TransactionsGetRequestOptions(count=10)
        )

        response = client.transactions_get(request_data)
        return jsonify(response.to_dict())

    except Exception as e:
        return jsonify({"error": str(e)}), 500

