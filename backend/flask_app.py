from flask import Flask
from routes.plaid_routes import plaid_bp

app = Flask(__name__)
app.register_blueprint(plaid_bp)

if __name__ == "__main__":
    app.run(port=5050) 
