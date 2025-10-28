# Movie Recommender v0.2

## Overview

Uses Python to generate AI-based movie recommendations from public datasets (MovieLens) and user ratings. This repo includes a SQLite database loader, a baseline recommender, and a simple CLI to print Top-K picks.

## Project Structure

```plaintext
movie_recommender/
├── .vscode/
│   └── settings.json               # VS Code Python settings / interpreter path
├── api/                            # API's that will be exposed to frontend
│   └── init_and_sync.py            # initializes and syncs database with csv data/json local user profile data
│
├── data/                           # Raw dataset + notes
│   ├── ml-latest-small/            # MovieLens small dataset (CSV files)
│   │   ├── links.csv
│   │   ├── movies.csv
│   │   ├── ratings.csv
│   │   ├── tags.csv
│   │   └── README.txt              # Dataset license/details (from GroupLens)
│   └── dataset_info.txt            # Our brief dataset notes
│
├── database/                       # SQLite database management
│   ├── __init__.py
│   ├── .gitkeep
│   ├── connection.py               # get_db() / connection helpers
│   ├── init_db.py                  # build schema + load CSVs into movies.db
│   ├── id_to_title.py              # for getting a title given an ID
│   ├── load_movielens.py           # loads db into created schema
│   └── movies.db                   # generated after running init_db.py
│
├── user_profile/                     # Local user profile (optional)
│   ├── __init__.py
│   ├── user_profile.json           # local prefs; read by CLI/recommender if needed
│   └── user_profile_test.py        # sample structure / quick tests for profiles
│
├── recommender/                    # Recommendation logic
│   ├── __init__.py
│   ├── .gitkeep
│   ├── baseline.py                 # very first pass recommender (e.g., popular/top-N)
│   └── data_loader.py              # helper functions to load CSV/DB data
│
├── ui/                             # user interface(s)
│   ├── __init__.py
│   ├── CLI.py                      # cli test ui
│   ├── web/                        # all web functions
│       ├── static/                      # css/js
│       │   └── style.css                   # stylesheet for web
│       └── templates/                  # html
│           └── index.html                  # html for test web page
│
├── .gitignore
├── main.py                         # script to initialize and sync database
├── app.py                          # entry point to flask application
├── README.md
└── requirements.txt          # project dependencies
```

## TL;DR Flow (what happens when you “use it”)

```plaintext
- Run app.py
- app.py checks if the database exists at DB_PATH
  - If not, it calls main.init_database_and_sync() to:
      - initialize the database schema (database.init_db.main)
      - load MovieLens data from CSVs (database.load_movielens.main)
      - sync user ratings from JSON profile (database.sync_json.sync_user_ratings)
- Flask app starts and serves endpoints:
  - "/" or "/index" renders index.html from ui/web/templates
- Frontend requests (via browser) access routes:
  - Recommender reads data from the database (recommender/baseline.py + recommender/data_loader.py)
  - Top-K movie recommendations are returned
  - Results are rendered in HTML
```

## INSTALL INFO

```plaintext
1. clone repository
    git clone <url>

2. Install dependencies shown in 'requirements.txt'
    pip install -r requirements.txt

3. Run app.py

4. Go to localhost:8000 to see web frontend(before we set up hosting lol)
```
