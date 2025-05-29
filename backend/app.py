import os
import requests
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

# ─── Load env & init OpenAI ─────────────────────────────────────────────────
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_KEY)

# ─── Flask & CORS setup ───────────────────────────────────────────────────────
app = Flask(__name__)
# Allow your GitHub Pages origin (and local dev) to call any route:
CORS(app, origins=["https://joewilcom.github.io", "http://localhost:5000"])

RADIO_API = "https://all.api.radio-browser.info/json"

# ─── Countries ────────────────────────────────────────────────────────────────
@app.route("/countries")
def countries():
    resp = requests.get(f"{RADIO_API}/stations/topclick/100", timeout=5)
    resp.raise_for_status()
    seen = {}
    for s in resp.json():
        code = s.get("countrycode")
        name = s.get("country")
        if code and name and code not in seen:
            seen[code] = name
    out = [{"code": c, "name": seen[c]} for c in sorted(seen, key=lambda k: seen[k])]
    return jsonify(out)

# ─── Station Search / Top Stations ────────────────────────────────────────────
@app.route("/search", methods=["POST", "OPTIONS"])
def search():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()

    data    = request.get_json() or {}
    top     = data.get("top", False)
    country = data.get("countrycode")
    genre   = data.get("tagList")
    name    = data.get("name")

    params = {"limit": 50}
    if country:
        params["countrycode"] = country

    if top:
        url = f"{RADIO_API}/stations/topclick/50"
    else:
        url = f"{RADIO_API}/stations/search"
        if genre:
            params["tagList"] = genre
        if name:
            params["name"] = name

    resp = requests.get(url, params=params, timeout=5)
    resp.raise_for_status()
    return jsonify(resp.json())

# ─── AI Tag Refinement ────────────────────────────────────────────────────────
@app.route("/ai-query", methods=["POST", "OPTIONS"])
def ai_query():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()

    data = request.get_json(silent=True) or {}
    q = (data.get("query") or "").strip()
    if not q:
        return jsonify({"error": "No query provided"}), 400

    try:
        result = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system","content":(
                    "Turn the user's music query into a few relevant genre tags, comma-separated."
                )},
                {"role":"user","content": q}
            ],
            max_tokens=20
        )
        tags = result.choices[0].message.content.strip()
        return jsonify({"tags": tags})
    except Exception as e:
        app.logger.error("AI error: %s", e)
        return jsonify({"error": "AI service failed"}), 500

# ─── CORS Preflight Helper ────────────────────────────────────────────────────
def _build_cors_preflight_response():
    response = make_response()
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

# ─── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
