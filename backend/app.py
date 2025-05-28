from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import openai  # pip install openai

app = Flask(__name__)
CORS(app)

if not openai.api_key:
    raise RuntimeError("Missing OpenAI API key. Set the OPENAI_API_KEY environment variable.")


RADIO_BROWSER_API = "https://de1.api.radio-browser.info/json/stations"

def fetch_stations(query="", top=False, filter_dead=True, field="name"):
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
        if field == "tag":
            params['tag'] = query
        else:
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
    field = data.get("field", "name")  # default to name search

    stations = fetch_stations(query=query, top=top, filter_dead=filter_dead, field=field)

    if sort_by in ["votes", "clickcount", "bitrate"]:
        stations.sort(key=lambda s: s.get(sort_by) or 0, reverse=True)

    return jsonify(stations[:10] if top else stations[:50])

@app.route("/ai-query", methods=["POST"])
def ai_query():
    data = request.get_json()
    user_query = data.get("query", "")
    print(f"[AI QUERY INPUT]: {user_query}")

    prompt = f"""
You are a search assistant for a radio station app. Given a user query like "{user_query}", return a short list of 1 to 3 genre or tag words that match popular radio station tags such as 'rock', 'pop', 'electronic', 'jazz', 'chill', 'classical', etc. Use only simple, API-searchable terms.
Respond with a comma-separated list only — no explanation.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You help convert user queries to searchable radio station tags."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=20,
            temperature=0.3,
        )
        refined = response.choices[0].message["content"].strip()
        print(f"[AI QUERY OUTPUT]: {refined}")
        return jsonify({ "tags": refined })
    except Exception as e:
        print(f"[AI QUERY ERROR]: {e}")
        return jsonify({ "error": str(e) }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
