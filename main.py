from flask import Flask
from flask_cors import CORS
from apis import register_routes

app = Flask(__name__)
CORS(app)  # ✅ Enable CORS for frontend calls

# Register all API routes
register_routes(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
