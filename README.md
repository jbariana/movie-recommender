# Movie Recommender

## Overview

AI-powered movie recommendation system using collaborative filtering on the MovieLens dataset with user ratings stored in PostgreSQL.

## Features

- Browse and search 9,000+ movies with real-time autocomplete
- Rate movies with interactive 5-star modal
- Get AI-powered personalized recommendations using item-item collaborative filtering
- Search: autocomplete dropdown + full results page
- User profile with complete rating history and statistics
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
