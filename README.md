# Smart Radio Search

Smart Radio Search is a web-based app for discovering and playing streaming radio stations around the world. It leverages the [Radio Browser API](https://www.radio-browser.info/) to provide search, preview, and discovery functionality.

## Features

- Search for radio stations by genre, location, language, or tags
- On load, displays top 10 stations by popularity (clicks)
- In-browser audio playback (HTML5 player)
- Country flag emoji for visual location cues
- Only one stream plays at a time
- Light/dark mode toggle
- Clickable tags to start a new search
- Tags truncated after 5 (with ellipsis)
- Filters out dead streams
- Incremental loading (Load More button for long results — if enabled)

## Project Structure

```
smart-radio-search/
├── backend/                  # Flask backend for proxying Radio Browser API
│   └── app.py
├── docs/                     # Frontend HTML/CSS/JS
│   └── index.html
├── Dockerfile                # For Fly.io deployment
├── fly.toml                  # Fly.io config file
└── README.md                 # This file
```

## Tech Stack

- Frontend: Vanilla HTML, CSS, and JavaScript
- Backend: Flask (Python)
- Data Source: [Radio Browser API](https://de1.api.radio-browser.info/)
- Hosting: [Fly.io](https://fly.io/)

## Local Development

### Prerequisites

- Python 3.9+
- Node.js (optional, not required)
- Fly.io CLI (`flyctl`)
- Git

### 1. Clone the repository

```bash
git clone https://github.com/your-username/smart-radio-search.git
cd smart-radio-search
```

### 2. Run backend locally (optional)

```bash
cd backend
pip install flask flask-cors requests
python app.py
```

Note: Production uses a live backend deployed on Fly.io at `https://smart-radio-search.fly.dev`.

### 3. Run frontend locally

You can run a basic web server in the `docs/` folder:

```bash
cd docs
python -m http.server 8000
```

Then visit: [http://localhost:8000](http://localhost:8000)

## Production Deployment (Fly.io)

### First-time setup

```bash
fly launch
```

Then use:

```bash
fly deploy
```

You can also run:

```bash
fly logs
```

To view real-time logs.

## Updating Your Deployment

1. Commit your changes to GitHub
2. Run:

   ```bash
   fly deploy
   ```

   Fly will rebuild and redeploy your Docker container.

## API Behavior (/search endpoint)

The `/search` endpoint accepts a POST request:

```json
{
  "query": "funk",
  "filter_dead": true,
  "top": false
}
```

### Parameters

- `query`: The search term (name, genre, etc.)
- `filter_dead`: Whether to exclude dead stations
- `top`: If true, returns the top 10 stations by `clickcount`

## Possible Future Enhancements

- Add user favorites/bookmarks (via local storage or user login)
- Allow sorting by bitrate or votes
- Display station logos
- Mobile responsive layout
- Analytics on most searched terms
- Internationalization / translation support

## Credits

Created by [Your Name] — feel free to fork, improve, and explore.

Powered by:
- [Radio Browser API](https://www.radio-browser.info/)
- [Flask](https://flask.palletsprojects.com/)
- [Fly.io](https://fly.io/)