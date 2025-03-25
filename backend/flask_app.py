# backend/flask_app.py
from flask import Flask
from flask_cors import CORS
from backend.routes.ai_routes import ai_bp
from backend.routes.plaid_routes import plaid_bp
from backend.routes.bills_routes import bills_bp

app = Flask(__name__)
CORS(app)  # This handles cross-origin from Postman or frontend

# Register routes
app.register_blueprint(ai_bp)
app.register_blueprint(plaid_bp)
app.register_blueprint(bills_bp)

if __name__ == "__main__":
    app.run(debug=True)
