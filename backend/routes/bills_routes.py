from flask import Blueprint, jsonify

bills_bp = Blueprint("bills", __name__)

@bills_bp.route("/api/bills/test", methods=["GET"])
def test_bills():
    return jsonify({"message": "Bills route working!"})
