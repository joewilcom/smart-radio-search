import os
import requests
from flask import Flask, request, jsonify
import openai

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/search', methods=['POST'])
def search():
    user_query = request.json.get('query')
    prompt = f"Convert this user query into Radio Browser API filters: '{user_query}'\nReturn JSON with keys like 'name', 'country', 'tag', etc."

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    filters = response.choices[0].message['content']
    filters_dict = eval(filters)

    api_response = requests.get("https://de1.api.radio-browser.info/json/stations/search", params=filters_dict)
    return jsonify(api_response.json())

if __name__ == '__main__':
    app.run(debug=True)
