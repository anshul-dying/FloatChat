from flask import Flask, jsonify
from flask_cors import CORS
from src.api.routes.chat import chat_bp
from src.api.routes.data import data_bp
from src.utils.logging import get_logger

app = Flask(__name__)
logger = get_logger(__name__)

# Configure CORS
CORS(
    app,
    resources={r"/*": {"origins": [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]}},
    supports_credentials=True
)

# Register blueprints
app.register_blueprint(chat_bp, url_prefix="/api")
app.register_blueprint(data_bp, url_prefix="/api")

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "FloatChat API is running"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)