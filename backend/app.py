import os
import requests
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
# Allow only your GH Pages origin to talk to us
CORS(app, origins=["https://joewilcom.github.io"])

RADIO_API = "https://all.api.radio-browser.info/json"

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

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json() or {}
    top     = data.get("top", False)
    country = data.get("countrycode")
    genre   = data.get("tagList")
    name    = data.get("name")

    params = {"limit": 50}
    if country and country != "ALL":
        params["countrycode"] = country

    if top:
        url = f"{RADIO_API}/stations/topclick/50"
    else:
        url = f"{RADIO_API}/stations/search"
        if genre and genre != "ALL":
            params["tagList"] = genre
        if name:
            params["name"] = name

    resp = requests.get(url, params=params, timeout=5)
    resp.raise_for_status()
    return jsonify(resp.json())

@app.route("/ai-query", methods=["POST"])
def ai_query():
    # … your existing OpenAI logic here …
    # return jsonify({"tags": "..."})


# … your existing imports, app setup, /countries and /search routes …

@app.route("/proxy")
def proxy():
    """
    A simple example proxy endpoint. 
    Pulls the `url` query-param from the client,
    fetches it server-side, and streams it back.
    """
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "no url specified"}), 400

    # fetch the target
    try:
        upstream = requests.get(url, stream=True, timeout=5)
        upstream.raise_for_status()
    except Exception as e:
        return jsonify({"error": str(e)}), 502

    # stream it back
    return Response(
        upstream.raw.read(),
        status=upstream.status_code,
        headers={k: v for k, v in upstream.headers.items()
                 if k.lower() in ("content-type", "content-length")}
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
