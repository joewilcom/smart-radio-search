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


@app.route("/proxy")
def proxy():
    """
    Proxy any audio URL (even if HTTP-only) through our HTTPS Flask domain
    so the browser never sees mixed-content.
    """
    upstream_url = request.args.get("url")
    if not upstream_url:
        return ("Missing ?url=", 400)

    try:
        upstream = requests.get(upstream_url, stream=True, timeout=10)
        upstream.raise_for_status()
    except Exception as e:
        return (f"Upstream fetch failed: {e}", 502)

    def generate():
        for chunk in upstream.iter_content(chunk_size=4096):
            if chunk:
                yield chunk

    return Response(
        stream_with_context(generate()),
        content_type=upstream.headers.get("content-type", "audio/mpeg")
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
