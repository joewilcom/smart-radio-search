import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("Missing OpenAI API key. Set the OPENAI_API_KEY environment variable.")

client = OpenAI(api_key=api_key)

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "Smart Radio Search API is running."

@app.route("/ai-query", methods=["POST"])
def ai_query():
    try:
        data = request.get_json()
        user_query = data.get("query", "")
        if not user_query:
            return jsonify({"error": "No query provided"}), 400

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Turn the user's music query into a few relevant genre-style tags for radio station discovery. "
                        "Respond with a comma-separated list."
                    )
                },
                {"role": "user", "content": user_query}
            ],
            max_tokens=20,
        )

        ai_tags = response.choices[0].message.content.strip()
        return jsonify({"tags": ai_tags})

    except Exception as e:
        print("Error in /ai-query:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)