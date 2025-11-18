# Movie Recommender

## Overview

Movie recommender web app using collaborative filtering on the MovieLens dataset with user ratings stored in PostgreSQL. Supports concurrent accesses and unencrypted logins.

## Features

- Browse and search 9,000+ movies with real-time autocomplete
- Rate movies with interactive 5-star modal
- Interacts w/ a Postgre database for user and movie data.
- Get machine-learning based personalized recommendations using item-item collaborative filtering.
- Search: autocomplete dropdown + full results page
- User profile with complete rating history, watchlist, favorites, and statistics
- Basic login (no encryption)
- Rating statistics with genre insights

## Installation

```bash
# 1. Clone repository
git clone <url>
cd movie-recommender

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
# Create a .env file in the root directory with:
DATABASE_URL=your_postgres_url
SECRET_KEY=your_secret_key_here

# 5. Run application
python app.py

# 6. Open browser
# Navigate to http://localhost:5000
```

## First Time Setup

Create a .env file in the root directory with: \
DATABASE_URL=your_postgres_url \
SECRET_KEY=your_secret_key_here

## License

MIT

## Credits

- MovieLens dataset provided by GroupLens Research (University of Minnesota)
- Poster images from TMDB (The Movie Database)
