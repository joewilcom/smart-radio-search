import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from openai import OpenAI
from dotenv import load_dotenv

# ─── Load env & initialize ─────────────────────────────────────────────────────
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("Missing OPENAI_API_KEY")

client = OpenAI(api_key=api_key)
app    = Flask(__name__)

# ─── Global CORS ────────────────────────────────────────────────────────────────
# Allow the frontend origin & local dev, on ALL routes / methods
CORS(
    app,
    resources={r"/*": {"origins": [
        "https://joewilcom.github.io",
        "http://localhost:8000"
    ]}},
    methods=["GET","POST","OPTIONS"],
    allow_headers=["Content-Type"]
)

# ─── Health check ───────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "OPTIONS"])
def home():
    return "Smart Radio Search API is running."

# ─── AI Tag Refinement Endpoint ─────────────────────────────────────────────────
@app.route("/ai-query", methods=["POST", "OPTIONS"])
def ai_query():
    data       = request.get_json(silent=True) or {}
    user_query = (data.get("query") or "").strip()
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

# ─── Search Endpoint ────────────────────────────────────────────────────────────
@app.route("/search", methods=["POST", "OPTIONS"])
def search():
    # JSON body (or empty dict)
    data = request.get_json(silent=True) or {}

    # Top-stations shortcut?
    if data.get("top"):
        url = "http://all.api.radio-browser.info/json/stations/topclick"
        params = {
            "order":      "clickcount",
            "reverse":    "true",
            "limit":      10,
            "hidebroken": "true"
        }
    else:
        # Full-text or tag search
        query       = data.get("query", "")
        field       = data.get("field", "name")    # name or tag
        sort_by     = data.get("sort_by", "votes")
        filter_dead = bool(data.get("filter_dead", False))

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
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        stations = resp.json()
    except Exception as e:
        app.logger.error("Error in /search: %s", e)
        return jsonify([]), 500

    return jsonify(stations)

# ─── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
