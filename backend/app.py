import os
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Load environment
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("Missing OPENAI_API_KEY")

# Init Flask & OpenAI
app = Flask(__name__)
client = OpenAI(api_key=api_key)

# Global CORS for your GH Pages origin
CORS(
    app,
    resources={r"/*": {"origins": ["https://joewilcom.github.io"]}},
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"]
)

# Preflight handler to ensure 200 on OPTIONS
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        resp = make_response()
        resp.headers["Access-Control-Allow-Origin"] = "https://joewilcom.github.io"
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

@app.route("/", methods=["GET", "OPTIONS"])
def home():
    return "API is up"

@app.route("/ai-query", methods=["POST","OPTIONS"])
def ai_query():
    data = request.get_json(silent=True) or {}
    q = (data.get("query") or "").strip()
    if not q:
        return jsonify({"error":"No query"}), 400

    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system","content":(
                    "Turn the user's music query into a few relevant genre tags, comma-separated."
                )},
                {"role":"user","content":q}
            ],
            max_tokens=20
        )
        tags = resp.choices[0].message.content.strip()
        return jsonify({"tags":tags})
    except Exception as e:
        app.logger.error("AI error: %s",e)
        return jsonify({"error":str(e)}),500

@app.route("/search", methods=["POST","OPTIONS"])
def search():
    data = request.get_json(silent=True) or {}

    if data.get("top"):
        url = "http://all.api.radio-browser.info/json/stations/topclick"
        params = {"order":"clickcount","reverse":"true","limit":10,"hidebroken":"true"}
    else:
        q           = data.get("query","")
        field       = data.get("field","name")
        sort_by     = data.get("sort_by","votes")
        filter_dead = bool(data.get("filter_dead",False))

        url = "http://all.api.radio-browser.info/json/stations/search"
        params = {field:q, "order":sort_by, "reverse":"true", "limit":50}
        if filter_dead:
            params["hidebroken"]="true"

    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        stations = r.json()
    except Exception as e:
        app.logger.error("Search error: %s",e)
        return jsonify([]),500

    return jsonify(stations)

if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
