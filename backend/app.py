import os
import openai
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Set up OpenAI API key
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/")
def home():
    return "Smart Radio Station Search is running!"

@app.route("/search", methods=["POST"])
def search():
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        if not query:
            return jsonify([])

        print("Query received:", query)

        # Use OpenAI to extract search tags
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Extract relevant music genres, countries, languages, or decades from this query to use as tags in a radio station search. Output a comma-separated list of lowercase tags with no explanation."
                },
                {"role": "user", "content": query}
            ]
        )
        tags = completion.choices[0].message.content.strip()
        print("Extracted tags:", tags)

        # Call Radio Browser API
        response = requests.get(
            "https://de1.api.radio-browser.info/json/stations/search",
            params={
                "tagList": tags,
                "hidebroken": True,
                "limit": 20,
                "order": "clickcount"
            },
            headers={"User-Agent": "smart-radio-search/1.0"}
        )

        if response.status_code != 200:
            print("Radio API error:", response.status_code)
            return jsonify([])

        stations = response.json()
        return jsonify(stations)

    except Exception as e:
        print("Error:", e)
        return jsonify([])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
