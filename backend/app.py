import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Allow only your GH Pages origin to talk to us
CORS(app, origins=["https://joewilcom.github.io"])

RADIO_API = "https://all.api.radio-browser.info/json"

@app.route("/countries")
def countries():
    # grab top 100 clicks to build a small country list
    resp = requests.get(f"{RADIO_API}/stations/topclick/100", timeout=5)
    resp.raise_for_status()
    seen = {}
    for s in resp.json():
        code = s.get("countrycode")
        name = s.get("country")
        if code and name and code not in seen:
            seen[code] = name
    # sort by country name
    out = [{"code": c, "name": seen[c]} for c in sorted(seen, key=lambda k: seen[k])]
    return jsonify(out)

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json() or {}
    top    = data.get("top", False)
    country = data.get("countrycode")
    genre   = data.get("tagList")
    name    = data.get("name")

    # build query params
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

if __name__ == "__main__":
    # for local testing
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
