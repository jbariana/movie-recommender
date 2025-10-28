# Movie Recommender v0.5

## Overview

AI-powered movie recommendation system using collaborative filtering on the MovieLens dataset and other user ratings.

## Features

- Browse and search 9,000+ movies with real-time autocomplete
- Rate movies with interactive 5-star modal
- Get AI-powered personalized recommendations using item-item collaborative filtering
- Dual search: autocomplete dropdown + full results page
- User profile with complete rating history
- Rating statistics and insights

## Tech Stack

**Backend:** Python 3.x, Flask, PostgreSQL (Supabase) / SQLite, scikit-learn, pandas, numpy  
**Frontend:** Vanilla JavaScript (modular ES6), CSS3  
**Data:** MovieLens 25M dataset with TMDB poster integration

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
# Navigate to http://localhost:8000
```

## First Time Setup

On first run if DB is not initialized, the app will automatically:

1. Initialize database schema (movies, ratings, links tables)
2. Populate with MovieLens data
3. Sync any existing user ratings from `user_profile/user_profile.json`

## Usage

1. **Login**: Enter any username (no password required for demo)
2. **Search**: Type 2+ characters to see autocomplete suggestions, or press Enter for full results
3. **Rate Movies**: Click any movie card to open the 5-star rating modal
4. **Get Recommendations**: Click "Browse" to see personalized recommendations
5. **View Profile**: Click "Profile" to see all your ratings
6. **Statistics**: Click "View Statistics" for rating insights

## API Endpoints

- `GET /` - Main application page
- `POST /login` - User login
- `POST /logout` - User logout
- `GET /session` - Check current session
- `POST /api/button-click` - Main API endpoint for all actions:
  - `view_ratings_button` - Get user's ratings
  - `get_rec_button` - Get recommendations
  - `search` - Search movies
  - `add_rating_submit` - Add/update rating
  - `remove_rating` - Remove r ating
  - `view_statistics_button` - Get rating statistics

## Database Schema

**movies** table:

- `movie_id` (PRIMARY KEY)
- `title`
- `year`
- `genres`
- `poster_url`

**ratings** table:

- `user_id`
- `movie_id`
- `rating`
- `timestamp`

**links** table:

- `movie_id`
- `imdb_id`
- `tmdb_id`

## Recommendation Algorithm

Uses **item-item collaborative filtering** with cosine similarity:

1. Builds user-item rating matrix
2. Calculates item-item similarity matrix
3. For each user, scores unwatched movies based on similar items they've rated
4. Returns top-K recommendations with predicted ratings

## Development

The frontend uses ES6 modules with no build step required. Key modules:

- **main.js**: Imports all modules
- **actionHandler.js**: Centralized API communication
- **eventHandlers.js**: Event delegation and search autocomplete
- **ratingModal.js**: Star rating modal functionality
- **movieRenderer.js**: Movie list rendering with posters
- **ratings.js**: Legacy add/remove rating form
- **login.js**: Authentication UI
- **utils.js**: Session helpers

## Environment Variables

```env
DATABASE_URL=postgresql://user:pass@host:port/db  # Optional: uses SQLite if not set
SECRET_KEY=your-secret-key-here                    # Required: for Flask sessions
```

## License

MIT

## Credits

- MovieLens dataset provided by GroupLens Research (University of Minnesota)
- Poster images from TMDB (The Movie Database)
