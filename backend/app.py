from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import openai
import os

app = Flask(__name__)
CORS(app)

# Load the OpenAI API key and print it for debugging
openai_key = os.getenv("OPENAI_API_KEY")
print(f"[DEBUG] OPENAI_API_KEY loaded: {'Yes' if openai_key else 'No'}")

if not openai_key:
    raise RuntimeError("Missing OpenAI API key. Set the OPENAI_API_KEY environment variable.")

openai.api_key = openai_key
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

def fetch_multi_tag_stations(tags, sort_by="clickcount", top=False, filter_dead=True):
    all_results = []
    seen = set()

    for tag in tags:
        stations = fetch_stations(query=tag.strip(), top=top, filter_dead=filter_dead, field="tag")
        print(f"[DEBUG] {len(stations)} stations found for tag: '{tag}'")
        for s in stations:
            key = s.get("url_resolved")
            if key and key not in seen:
                all_results.append(s)
                seen.add(key)

    if sort_by in ["votes", "clickcount", "bitrate"]:
        all_results.sort(key=lambda s: s.get(sort_by) or 0, reverse=True)

    return all_results[:10] if top else all_results[:50]

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    query = data.get("query", "")
    top = data.get("top", False)
    filter_dead = data.get("filter_dead", True)
    sort_by = data.get("sort_by", "")
    field = data.get("field", "name")

    if field == "tag":
        tags = [t.strip() for t in query.replace(",", " ").split()]
        stations = fetch_multi_tag_stations(tags, sort_by=sort_by, top=top, filter_dead=filter_dead)
    else:
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
