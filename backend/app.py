import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Load .env at project root containing OPENAI_API_KEY
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("Missing OPENAI_API_KEY environment variable")

client = OpenAI(api_key=api_key)
app    = Flask(__name__)

# Enable CORS for your GH Pages frontend and local dev
CORS(
    app,
    resources={r"/*": {"origins": [
        "https://joewilcom.github.io",
        "http://localhost:8000"
    ]}},
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"]
)

@app.route("/")
def home():
    return "Smart Radio Search API is running."

@app.route("/ai-query", methods=["POST"])
def ai_query():
    data       = request.get_json() or {}
    user_query = data.get("query", "").strip()
    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
              "role":    "system",
              "content": (
                "Turn the user's music query into a few relevant genre-style tags. "
                "Respond with comma-separated tags."
              )
            },
            {"role": "user", "content": user_query}
        ],
        max_tokens=20,
    )
    tags = resp.choices[0].message.content.strip()
    return jsonify({"tags": tags})

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json() or {}

    # Top-click stations?
    if data.get("top"):
        url = "http://all.api.radio-browser.info/json/stations/topclick"
        params = {
            "order":      "clickcount",
            "reverse":    "true",
            "limit":      10,
            "hidebroken": "true"
        }
    else:
        # Full-text or tag-based search
        query       = data.get("query", "")
        field       = data.get("field", "name")   # name or tag
        sort_by     = data.get("sort_by", "votes")
        filter_dead = data.get("filter_dead", False)

        url = "http://all.api.radio-browser.info/json/stations/search"
        params = {
            field:     query,
            "order":   sort_by,
            "reverse": "true",
            "limit":   50
        }
        if filter_dead:
            params["hidebroken"] = "true"

    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        stations = r.json()
    except Exception as e:
        print("Error in /search:", e)
        return jsonify([]), 500

    return jsonify(stations)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
