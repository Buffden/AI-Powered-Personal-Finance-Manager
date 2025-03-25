# backend/routes/ai_routes.py
from flask import Blueprint, jsonify

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

@ai_bp.route("/test", methods=["GET"])
def test_ai():
    return jsonify({"message": "AI route is working!"})
