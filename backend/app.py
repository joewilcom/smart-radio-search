import os
import requests
from flask import Flask, request, jsonify
import openai

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/search', methods=['POST'])
def search():
    user_query = request.json.get('query')

    # Step 1: Use OpenAI to parse the natural language query
    prompt = f"""
    Convert this radio station search request into Radio Browser API filters.
    Query: "{user_query}"
    Respond with a compact JSON object using keys like 'name', 'country', 'tag', or 'language'.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        filters_str = response.choices[0].message['content']
        filters = eval(filters_str)  # ⚠️ Replace with json.loads() if needed for safety
    except Exception as e:
        return jsonify({"error": f"Failed to parse filters: {str(e)}"}), 500

    # Step 2: Use the Radio Browser API to search for stations
    radio_browser_url = "https://de1.api.radio-browser.info/json/stations/search"
    try:
        rb_response = requests.get(radio_browser_url, params=filters)
        stations = rb_response.json()
    except Exception as e:
        return jsonify({"error": f"Failed to query Radio Browser: {str(e)}"}), 500

    # Step 3: Return results
    return jsonify(stations)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
