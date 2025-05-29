# Smart Radio Search v1.3

Smart Radio Search is a web-based app for discovering, previewing, and playing streaming radio stations around the world. It uses a Flask-powered backend to proxy the [Radio Browser API](https://www.radio-browser.info/) and a vanilla-JS frontend with AI-assisted tagging and a responsive grid layout.

---

## 🔥 Highlights & Features

* **Search by name, genre, location or tags**
* **AI-powered tag refinement**: input “rock edm” → backend returns “rock, edm” tags
* **Multi-term queries**: splits on spaces (names) or commas (tags) and merges results
* **Top 10 on load**: shows the 10 most popular stations by click count
* **One-at-a-time audio playback**: starting a new station auto-pauses any playing stream
* **Responsive CSS grid** of station cards (min-width 300px)
* **Country flags** rendered via Twemoji for cross-browser consistency
* **Clickable tags**: click any tag to rerun a search for that genre
* **Enter-to-search**: press Enter in the input box to trigger a query
* **Dark/light mode toggle**
* **Tag truncation**: shows up to 5 tags per station, with “…” if more
* **Filters out dead streams** & upgrades `http://` URLs to `https://` where possible.

---

## 🚀 Project Structure

```
smart-radio-search/
├── backend/                  # Flask API proxy (POST /ai-query, POST /search)
│   └── app.py
├── docs/                     # Frontend (HTML/CSS/JS, uses twemoji.min.js)
│   └── index.html
├── Dockerfile                # Builds combined frontend+backend container
├── fly.toml                  # Fly.io configuration
└── README.md                 # This file
```

---

## 🛠 Tech Stack

* **Frontend**: HTML, CSS, JavaScript
* **Backend**: Python, Flask, Flask-CORS
* **AI-tagging**: OpenAI gpt-3.5-turbo
* **Data source**: [Radio Browser API](https://www.radio-browser.info/)
* **Hosting**: Fly.io (Docker)
* **Emoji**: Twemoji for flags

---

## 💻 Local Development

1. **Clone the repo**

   ```bash
   git clone https://github.com/your-username/smart-radio-search.git
   cd smart-radio-search
   ```

2. **Backend** (optional, uses remote backend by default)

   ```bash
   cd backend
   pip install -r requirements.txt
   python app.py
   ```

   * Runs on `http://localhost:5000`

3. **Frontend**

   ```bash
   cd docs
   python -m http.server 8000
   ```

   * Open [http://localhost:8000](http://localhost:8000) in your browser

---

## ☁️ Production Deployment

We combine frontend + backend into a single Docker container:

```bash
# First-time only:
fly launch

# Deploy:
fly deploy
```

* Your app will be live at `https://<your-app>.fly.dev`
* Check logs with `fly logs`

---

## 📡 API Endpoints

### POST `/ai-query`

* **Request**

  ```json
  { "query": "classic rock" }
  ```
* **Response**

  ```json
  { "tags": "classic rock, rock, retro" }
  ```

### POST `/search`

* **Request**

  ```json
  {
    "query": "rock",
    "filter_dead": true,
    "sort_by": "votes",
    "field": "name"        // or "tag"
  }
  ```
* **For top stations**

  ```json
  { "top": true, "filter_dead": true, "sort_by": "clickcount" }
  ```
* **Response**
  Array of station objects with:

  * `stationuuid`, `name`, `url_resolved`
  * `country`, `countrycode`
  * `bitrate`, `codec`, `tags`, `votes`, `clickcount`

---

## ⭐ Future Ideas

* Persist user favorites (localStorage or login)
* Station logos & waveforms
* Infinite scroll / “Load more”
* Mobile-first refinements
* Analytics on search trends
* i18n / translation support

---

## 🙏 Credits

Powered by OpenAI, Flask, Radio Browser API, and Twemoji.

Feel free to fork, file issues, and submit PRs!
