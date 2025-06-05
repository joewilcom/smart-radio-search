# Smart Radio Search

Discover, preview, and play streaming radio stations from around the world with AI-powered genre tagging, live filtering, and one-at-a-time playback.

**Live Demo:** [https://joewilcom.github.io/smart-radio-search/](https://joewilcom.github.io/smart-radio-search/)

## Features

* **Global Radio Discovery:** Access a wide range of internet radio stations via the Radio Browser API.
* **AI-Powered Search:** Type natural language queries (e.g., "80s rock classics usa", "relaxing jazz from France"). The backend uses OpenAI (GPT-3.5 Turbo) to extract relevant search tags (genres, countries, keywords).
* **AI Station Summaries:** Short descriptions for each station generated on demand via OpenAI.
* **Filtering Controls:**
    * Search by station name or keywords.
    * Filter by country.
    * Filter by common genres.
    * Sort results by votes, clicks, or bitrate (client-side sorting).
* **Instant Preview:** Listen to radio streams directly within the app.
* **One-at-a-Time Playback:** Only one audio stream plays at a time.
* **Dark Mode:** Toggle between light and dark themes for comfortable viewing.
* **Responsive Design:** Works on various screen sizes.
* **Dynamic Station Cards:** Displays station name, country (with flag), a short AI-generated station summary, click/vote stats, bitrate, codec, and clickable tags.

## Technology Stack

* **Frontend:**
    * HTML5
    * CSS3 (with CSS Variables for theming)
    * JavaScript (Vanilla JS, ES6+)
* **Backend:**
    * Python 3
    * Flask (Web framework)
    * Flask-CORS (Handles Cross-Origin Resource Sharing)
* **APIs & Services:**
    * **Radio Browser API:** Provides the database of radio stations.
    * **OpenAI API (gpt-3.5-turbo):** Powers the AI search query understanding.
    * **Flag CDN:** For displaying country flags.
* **Deployment:**
    * **Frontend:** GitHub Pages
    * **Backend:** Koyeb (or any platform supporting Python/Flask deployment)

## Project Structure

A brief overview of key files and folders:

```
├── smart-radio-search/   # (If this folder is used for GitHub Pages root)
│   └── index.html        # Main frontend file (HTML, CSS, JS)
├── backend/              # (If backend code is organized here)
│   ├── app.py            # Flask backend application
│   ├── requirements.txt  # Python dependencies
│   └── .env              # Local environment variables (OpenAI API Key) - DO NOT COMMIT
├── index.html            # Or if at root for GitHub Pages
├── app.py                # Or if Flask app is at root
├── requirements.txt      # Or if at root
├── .env                  # Or if at root (for local dev)
├── Dockerfile            # For containerized deployment (optional for Koyeb basic deploys)
└── README.md             # This file
```
## How It Works

1.  **Frontend (`index.html`):** The user interacts with the web interface to search for radio stations.
    * On load, it fetches a list of countries and top radio stations.
    * When a search is initiated (e.g., typing "upbeat pop" or selecting filters):
        * The text query is sent to the backend's `/ai-query` endpoint.
2.  **AI Query Processing (Backend `/ai-query` in `app.py`):**
    * This endpoint receives the text query.
    * It calls the OpenAI API to parse the query and extract relevant search tags (e.g., genres, location keywords).
    * It returns these tags to the frontend.
3.  **Station Search (Backend `/search` in `app.py`):**
    * The frontend makes another request to the `/search` endpoint, sending the original search text, any AI-generated tags, and selected filters (country, genre dropdowns).
    * The backend constructs a query for the **Radio Browser API** using these parameters.
        * If AI tags are present, they are used for `tagList`.
        * If only a text search term is present (no AI tags), it's used as a broader `searchterm`.
        * Country codes and specific station names are also used if provided.
    * Results from the Radio Browser API are returned to the frontend.
4.  **Displaying Results (Frontend):**
    * The stations are displayed as cards, each with an HTML `<audio>` player.
    * Audio `preload` is set to `none` to minimize initial network traffic.
    * The app ensures only one audio stream plays at a time.
5.  **Chat Recommendations (Backend `/chat` in `app.py`):**
    * The chat box sends your conversation to this endpoint.

    * The backend prepends a system prompt so OpenAI suggests useful search terms in quotes and recommends station names when possible.

    * The response appears below the chat field.
6.  **Audio Proxy (Backend `/proxy` in `app.py`):**
    * A simple proxy endpoint is available in the backend. While not currently used for the main audio playback in `index.html` (audio `src` is directly from Radio Browser API results), it can be used to circumvent potential CORS or mixed-content issues with certain streams if needed in the future.

## Setup and Installation (Local Development)

To run this project locally, you'll need Python 3.x and an OpenAI API Key.

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-folder-name>
    ```

2.  **Backend Setup (`app.py`):**
    *(Assuming `app.py` and `requirements.txt` are at the project root. If they are in a `backend/` subfolder, `cd` into it first or adjust paths.)*

    * **Create and activate a Python virtual environment:**
        ```bash
        python -m venv venv
        # On Windows
        .\venv\Scripts\activate
        # On macOS/Linux
        source venv/bin/activate
        ```
    * **Install dependencies:**
        ```bash
        pip install -r requirements.txt
        ```
    * **Set up environment variables:**
        Create a file named `.env` in the same directory as `app.py`. Add your OpenAI API key to it:
        ```
        OPENAI_API_KEY=sk-yourActualOpenAIApiKeyHere
        FLASK_DEBUG=True
        ```
        **Important:** Add `.env` to your `.gitignore` file to prevent committing your API key.
    * **Run the Flask backend server:**
        ```bash
        python app.py
        ```
        The backend should now be running, typically on `http://127.0.0.1:5000/`.

3.  **Frontend Setup (`index.html`):**
    * **Configure API Base URL (if needed):**
        Open `index.html` in your text editor. Find the line:
        `const API_BASE = 'https://simple-naomi-joewilcom-71ae2211.koyeb.app';`
        For local testing against your local backend, change this to:
        `const API_BASE = 'http://127.0.0.1:5000';`
        Remember to change it back to your deployed Koyeb URL when committing for the live version.
    * **Open in browser:**
        Open the `index.html` file directly in your web browser.

## Deployment

* **Frontend (GitHub Pages):**
    * The `index.html` file (and any other static assets if you add them) can be deployed using GitHub Pages.
    * Ensure your GitHub repository is configured to serve from the appropriate branch and folder.
    * The `API_BASE` constant in `index.html` must point to your deployed backend URL.
* **Backend (Koyeb):**
    * The Flask application (`app.py`) is deployed to Koyeb.
    * Koyeb can typically build and deploy from `requirements.txt`. If you use a `Dockerfile`, ensure it's configured correctly.
    * **Crucially, set the `OPENAI_API_KEY` environment variable in your Koyeb service settings.**
    * The backend uses `Flask-CORS` and is configured to allow requests from any origin for easier local testing. Adjust this in `app.py` if you need stricter rules.

## Contributing

Feel free to fork this project, make improvements, and submit pull requests. If you find any issues or have suggestions, please open an issue.
