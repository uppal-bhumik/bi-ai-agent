from flask import Flask
from routes_v2.openai_routes_v2 import openai_bp

import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.register_blueprint(openai_bp)

app.secret_key = os.getenv('FLASK_SECRET_KEY')

@app.route('/')
def home():
    return "BI-AI Agent Backend is Running!"

if __name__ == "__main__":
    print("🚀 Starting BI-AI Agent Backend...")
    app.run(port=5050, debug=True, use_reloader=False)