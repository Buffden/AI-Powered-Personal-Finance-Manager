from flask import Blueprint, jsonify

plaid_bp = Blueprint("plaid", __name__)

@plaid_bp.route("/api/plaid/test", methods=["GET"])
def test_plaid():
    return jsonify({"message": "Plaid route working!"})
