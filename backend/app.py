import os
import requests
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import openai # Added for OpenAI API
from dotenv import load_dotenv # Added to load .env file for local development

# Load environment variables from .env file (especially for OPENAI_API_KEY locally)
load_dotenv()

app = Flask(__name__)
# Allow requests from any origin. "supports_credentials" helps with preflight
# requests made by modern browsers.
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

RADIO_API = "https://all.api.radio-browser.info/json"

# Cache top tags from the Radio Browser API
TOP_TAGS = None

def fetch_top_tags(limit: int = 200):
    """Fetch and cache the most common tags."""
    global TOP_TAGS
    if TOP_TAGS is None:
        try:
            resp = requests.get(
                f"{RADIO_API}/tags",
                params={"limit": limit, "order": "stationcount", "reverse": "true"},
                timeout=10,
            )
            resp.raise_for_status()
            TOP_TAGS = [t.get("name", "").lower() for t in resp.json() if t.get("name")]
        except Exception as e:
            print(f"Error fetching top tags: {e}")
            TOP_TAGS = []
    return TOP_TAGS

# Initialize OpenAI client
# The API key is automatically read from the OPENAI_API_KEY environment variable
try:
    client = openai.OpenAI()
    if not client.api_key: # openai library v1.x checks for key presence during client init
        print("Warning: OPENAI_API_KEY not found in environment. AI features will be disabled.")
        # You could have a flag here to disable AI features more formally if needed
except Exception as e:
    print(f"Error initializing OpenAI client: {e}. AI features may be disabled.")
    client = None


@app.route("/countries")
def countries():
    """Return the full list of countries from Radio Browser."""
    try:
        resp = requests.get(f"{RADIO_API}/countries", timeout=10)
        resp.raise_for_status()

        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching countries: {e}")
        data = []

    # Fallback to a minimal static list if the API call fails
    if not data:
        data = [
            {"iso_3166_1": "US", "name": "United States"},
            {"iso_3166_1": "GB", "name": "United Kingdom"},
            {"iso_3166_1": "DE", "name": "Germany"},
            {"iso_3166_1": "FR", "name": "France"},
        ]

    result = [
        {
            "code": c.get("iso_3166_1", "").upper(),
            "name": c.get("name", ""),
        }
        for c in data
        if c.get("iso_3166_1") and c.get("name")
    ]
    result.sort(key=lambda x: x["name"])
    return jsonify(result)


@app.route("/tags")
def tags():
    """Return the top tags for front-end helpers."""
    return jsonify(fetch_top_tags())


@app.route("/search", methods=["POST"])
def search():
    data = request.get_json() or {}
    top = data.get("top", False)
    country_code = data.get("countrycode")  # from country dropdown
    tag_list_from_frontend = data.get("tagList")  # from AI or genre dropdown
    name_from_frontend = data.get("name")  # from search text input
    limit = int(data.get("limit", 50))
    offset = int(data.get("offset", 0))

    if top:
        url = f"{RADIO_API}/stations/topvote/{limit}"
        params = {}
        if country_code and country_code != "ALL":
            params["countrycode"] = country_code
    else:
        url = f"{RADIO_API}/stations/search"
        params = {"limit": limit, "offset": offset}
        if country_code and country_code != "ALL":
            params["countrycode"] = country_code

        # Refined logic for using tag_list, name, and searchterm
        if tag_list_from_frontend and tag_list_from_frontend != "ALL":
            params["tagList"] = tag_list_from_frontend

        if name_from_frontend:
            # If AI/genre dropdown provided specific tags, and user also typed a name,
            # use the typed name as a filter for the station's actual name.
            if tag_list_from_frontend and tag_list_from_frontend != "ALL":
                params["name"] = name_from_frontend
            else:
                # If no specific tags from AI/genre dropdown, but user typed something,
                # use that typed text as a general 'searchterm' for broader matching.
                params["searchterm"] = name_from_frontend

        # Note: If only 'country_code' is set, and 'name_from_frontend' and 'tag_list_from_frontend' are empty/ALL,
        # then 'params' will only contain 'limit' and 'countrycode'. This is fine.

    try:
        resp = requests.get(url, params=params, timeout=10) # Increased timeout slightly
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.exceptions.RequestException as e:
        print(f"Error searching stations: {e}")
        print(f"Request params: {params}")
        print(f"Request URL: {url}")
        return jsonify({"error": "Failed to fetch stations from Radio API", "details": str(e)}), 502
    except Exception as e:
        print(f"An unexpected error occurred during search: {e}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@app.route("/ai-query", methods=["POST"])
def ai_query():
    if not client or not client.api_key:
        print("OpenAI client not initialized or API key missing. Skipping AI query.")
        return jsonify({"tags": ""})

    data = request.get_json() or {}
    user_query = data.get("query")

    if not user_query:
        return jsonify({"tags": ""}) # No query, no tags

    try:
        # print(f"Sending to OpenAI: {user_query}") # Uncomment for debugging
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo", # A cost-effective and capable model
            messages=[
                {"role": "system", "content": (
                    "You are an assistant that extracts relevant search tags for finding internet radio stations. "
                    "Given a user's query, identify specific genres, countries, major cities, languages, or descriptive keywords. "
                    "Return these as a single comma-separated string. "
                    "For example, if the query is 'russian rock music', return 'rock,russia,russian'. "
                    "If the query is 'classical music from Vienna', return 'classical,vienna,austria'. "
                    "If the query is 'relaxing jazz radio', return 'relaxing,jazz'. "
                    "If the query is very generic, too ambiguous for radio search, or contains offensive terms, return an empty string."
                )},
                {"role": "user", "content": user_query}
            ],
            temperature=0.2, # Lower temperature for more deterministic and focused output
            max_tokens=60 # Max length of the returned tags string
        )

        extracted_tags = completion.choices[0].message.content.strip()

        # Clean up the tags: remove extra spaces, filter out empty tags if any from splitting
        tag_parts = [tag.strip().lower() for tag in extracted_tags.split(',')]
        cleaned_parts = list(filter(None, tag_parts))

        # Match against known top tags for better accuracy
        top_tags = set(fetch_top_tags())
        matched = [t for t in cleaned_parts if t in top_tags]
        cleaned_tags = ','.join(matched if matched else cleaned_parts)

        # print(f"Extracted tags: '{cleaned_tags}'") # Uncomment for debugging
        return jsonify({"tags": cleaned_tags})

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return jsonify({"tags": ""}) # Fallback to empty tags on any error


@app.route("/summary", methods=["POST"])
def summary():
    """Return a short natural-language summary for a radio station."""
    if not client or not client.api_key:
        return jsonify({"summary": ""})

    data = request.get_json() or {}
    station = data.get("station") or {}

    name = station.get("name", "")
    country = station.get("country", "")
    tags = station.get("tags", "")

    prompt = (
        "Create a brief enticing description for this internet radio station.\n"
        f"Name: {name}\nCountry: {country}\nTags: {tags}\n"
        "Summary:"
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You write short promotional summaries for internet radio stations."
                        " Keep it under 30 words."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=60,
        )

        summary_text = completion.choices[0].message.content.strip()
        return jsonify({"summary": summary_text})
    except Exception as e:
        print(f"Error generating summary: {e}")
        return jsonify({"summary": ""})



BASE_CHAT_SYSTEM_MESSAGE = {
    "role": "system",
    "content": (

        "You help users search for internet radio stations. "
        "When they describe the music they want, reply with a brief sentence "
        "and list three to five short search terms in double quotes. Each tag should be a single word. "
        "Avoid mentioning other streaming services. "
        "You are a helpful assistant that recommends internet radio stations. "
        "When the user mentions a genre, artist, or mood, suggest a short list "
        "of stations that might match, including country or region when known. "
        "Keep replies brief. If unsure, advise how to search."

    ),
}


@app.route("/chat", methods=["POST"])
def chat():
    """Return a conversational reply with station suggestions."""
    if not client or not client.api_key:
        return jsonify({"answer": ""})

    data = request.get_json() or {}
    messages = data.get("messages") or []
    if not isinstance(messages, list):
        messages = []

    if not messages or messages[0].get("role") != "system":
        messages = [BASE_CHAT_SYSTEM_MESSAGE] + messages

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=120,
        )
        reply = completion.choices[0].message.content.strip()
        return jsonify({"answer": reply})
    except Exception as e:
        print(f"Error during chat: {e}")
        return jsonify({"answer": ""})



@app.route("/proxy")
def proxy():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "no url specified"}), 400

    try:
        upstream = requests.get(url, stream=True, timeout=10) # Increased timeout
        upstream.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Proxy error fetching upstream URL {url}: {e}")
        return jsonify({"error": str(e)}), 502
    except Exception as e: # Catch any other unexpected errors
        print(f"Unexpected proxy error for URL {url}: {e}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

    # Stream the content back
    # Note: upstream.raw.read() might load the whole thing in memory for non-chunked responses.
    # For large files, stream_with_context might be preferred with upstream.iter_content()
    def generate():
        for chunk in upstream.iter_content(chunk_size=8192):
            yield chunk

    # Only proxy essential headers to avoid issues
    proxied_headers = {}
    if 'content-type' in upstream.headers:
        proxied_headers['Content-Type'] = upstream.headers['content-type']
    if 'content-length' in upstream.headers:
        proxied_headers['Content-Length'] = upstream.headers['content-length']

    return Response(stream_with_context(generate()), status=upstream.status_code, headers=proxied_headers)


if __name__ == "__main__":
    # The host must be 0.0.0.0 to be accessible externally (e.g., by Fly.io)
    # The port is determined by Fly.io's PORT environment variable or defaults to 8080
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "False").lower() == "true",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
    )
