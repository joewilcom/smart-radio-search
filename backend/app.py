from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

RADIO_BROWSER_API = "https://de1.api.radio-browser.info/json/stations"

def fetch_stations(query="", top=False, filter_dead=True):
    params = {
        'limit': 100,
        'order': 'clickcount',
        'reverse': True,
        'hidebroken': filter_dead,
    }

    if top:
        url = RADIO_BROWSER_API
    else:
        url = f"{RADIO_BROWSER_API}/search"
        params['name'] = query

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return []

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    query = data.get("query", "")
    top = data.get("top", False)
    filter_dead = data.get("filter_dead", True)
    sort_by = data.get("sort_by", "")

    stations = fetch_stations(query=query, top=top, filter_dead=filter_dead)

    if sort_by in ["votes", "clickcount", "bitrate"]:
        stations.sort(key=lambda s: s.get(sort_by) or 0, reverse=True)

    if top:
        return jsonify(stations[:10])
    else:
        return jsonify(stations[:50])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
