from flask import Blueprint, request, jsonify, render_template, redirect
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
from datetime import datetime
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.link_token_create_request_update import LinkTokenCreateRequestUpdate


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

# Configuration
REDIRECT_URL = os.getenv('REDIRECT_URL', 'http://localhost:8501/?page=add_bank_account')

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
        institution_id = request.json.get("institution_id")
        institution_name = request.json.get("institution_name")

        if not public_token or not institution_id:
            return jsonify({"error": "Missing required parameters"}), 400

        # Exchange public token for access token
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        access_token = exchange_response.to_dict()["access_token"]

        # Store access token with institution ID
        if "demo-user-123" not in ACCESS_TOKENS:
            ACCESS_TOKENS["demo-user-123"] = {}
        ACCESS_TOKENS["demo-user-123"][institution_id] = access_token

        # Fetch account information
        accounts_request = AccountsGetRequest(access_token=access_token)
        accounts_response = client.accounts_get(accounts_request)
        accounts = accounts_response.to_dict()["accounts"]

        return jsonify({
            "access_token": access_token,
            "accounts": accounts,
            "institution_id": institution_id,
            "institution_name": institution_name
        })
    except Exception as e:
        import traceback
        print("💥 Error in exchange_public_token:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# 3️⃣ Fetch Transactions (Updated for Multiple Banks)
@plaid_bp.route("/api/plaid/get_transactions", methods=["POST"])
def get_transactions():
    try:
        user_tokens = ACCESS_TOKENS.get("demo-user-123")
        if not user_tokens:
            return jsonify({"error": "No access tokens"}), 400

        # 🔁 Receive string dates from frontend
        data = request.json
        start_date_str = data.get("start_date")
        end_date_str = data.get("end_date")
        selected_accounts = data.get("account_ids", [])  # Optional account filtering

        # ✅ Convert string to datetime.date
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        all_transactions = []
        all_accounts = []

        # If user_tokens is a single token (string), convert to dict format
        if isinstance(user_tokens, str):
            user_tokens = {"default": user_tokens}

        # Fetch transactions from all linked banks
        for institution_id, access_token in user_tokens.items():
            try:
                # 💸 Build request for Plaid
                request_data = TransactionsGetRequest(
                    access_token=access_token,
                    start_date=start_date,
                    end_date=end_date,
                    options=TransactionsGetRequestOptions(
                        count=100,  # Increased count
                        account_ids=selected_accounts if selected_accounts else None
                    )
                )

                response = client.transactions_get(request_data)
                transactions = response.to_dict()

                # Add institution_id to each transaction for reference
                for transaction in transactions.get("transactions", []):
                    transaction["institution_id"] = institution_id

                all_transactions.extend(transactions.get("transactions", []))
                all_accounts.extend(transactions.get("accounts", []))

            except Exception as e:
                print(f"Error fetching transactions for institution {institution_id}: {str(e)}")
                continue

        return jsonify({
            "transactions": all_transactions,
            "accounts": all_accounts,
            "total_transactions": len(all_transactions)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 4️⃣ Get All Linked Accounts
@plaid_bp.route("/api/plaid/get_accounts", methods=["GET"])
def get_accounts():
    try:
        access_token = ACCESS_TOKENS.get("demo-user-123")
        if not access_token:
            return jsonify({"error": "No access token"}), 400

        request = AccountsGetRequest(access_token=access_token)
        response = client.accounts_get(request)
        return jsonify(response.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 5️⃣ Create Update Link Token (for adding more banks)
@plaid_bp.route("/api/plaid/update_link_token", methods=["POST"])
def create_update_link_token():
    try:
        access_token = ACCESS_TOKENS.get("demo-user-123")
        if not access_token:
            return jsonify({"error": "No access token"}), 400

        # Create Link Token with update mode
        request = LinkTokenCreateRequest(
            client_name="AI Finance Manager",
            language="en",
            country_codes=[CountryCode("US")],
            user=LinkTokenCreateRequestUser(client_user_id="demo-user-123"),
            access_token=access_token,
            update=LinkTokenCreateRequestUpdate(
                account_selection_enabled=True  # Allow selecting specific accounts
            )
        )
        response = client.link_token_create(request)
        return jsonify({"link_token": response.to_dict()["link_token"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 6️⃣ Store Multiple Access Tokens
@plaid_bp.route("/api/plaid/store_access_token", methods=["POST"])
def store_access_token():
    try:
        access_token = request.json.get("access_token")
        institution_id = request.json.get("institution_id")
        
        if not access_token or not institution_id:
            return jsonify({"error": "Missing required parameters"}), 400

        # Store multiple tokens per user (in-memory for demo)
        if "demo-user-123" not in ACCESS_TOKENS:
            ACCESS_TOKENS["demo-user-123"] = {}
        ACCESS_TOKENS["demo-user-123"][institution_id] = access_token

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 7️⃣ Launch Plaid Link in New Tab
@plaid_bp.route("/launch-plaid-link")
def launch_plaid_link():
    try:
        # Create a new link token
        request_data = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id="demo-user-123"),
            client_name="AI Finance Manager",
            products=[Products("transactions")],
            country_codes=[CountryCode("US")],
            language="en"
        )
        response = client.link_token_create(request_data)
        link_token = response.to_dict()["link_token"]

        # Get the redirect URL from query params or use default
        redirect_url = request.args.get('redirect_url', REDIRECT_URL)
        
        # Render the template with the link token and redirect URL
        return render_template('launch_plaid.html', 
                             link_token=link_token,
                             redirect_url=redirect_url)
    
    except Exception as e:
        print("Error creating link token:", str(e))
        return redirect(REDIRECT_URL)

# 8️⃣ Handle Plaid Success Callback
@plaid_bp.route("/api/plaid/handle-success", methods=["POST"])
def handle_plaid_success():
    try:
        data = request.json
        public_token = data.get("public_token")
        metadata = data.get("metadata", {})
        
        if not public_token:
            return jsonify({"error": "No public token provided"}), 400

        # Exchange public token for access token
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        access_token = exchange_response.to_dict()["access_token"]
        item_id = exchange_response.to_dict()["item_id"]

        # Store access token with institution info
        institution_id = metadata.get("institution", {}).get("institution_id", "default")
        
        if "demo-user-123" not in ACCESS_TOKENS:
            ACCESS_TOKENS["demo-user-123"] = {}
        ACCESS_TOKENS["demo-user-123"][institution_id] = access_token

        print(f"✅ Successfully stored access token for institution {institution_id}")
        
        return jsonify({
            "success": True,
            "institution_id": institution_id,
            "item_id": item_id
        })

    except Exception as e:
        print("Error handling Plaid success:", str(e))
        return jsonify({"error": str(e)}), 500

