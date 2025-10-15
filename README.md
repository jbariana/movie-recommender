# Movie Recommender v0.2

## Overview

Uses Python to generate AI-based movie recommendations from public datasets (MovieLens) and user ratings. This repo includes a SQLite database loader, a baseline recommender, and a simple CLI to print Top-K picks.

## Project Structure

```plaintext
movie_recommender/
├── .vscode/
│   └── settings.json               # VS Code Python settings / interpreter path
├── api/                            # API modules
│   ├── __init__.py
│   ├── api.py                      #handles front end to back end response
│   ├── init_and_sync.py            # initializes and syncs database / user profile
│   ├── routes.py                    # handles flask routing 
│   └── sync_user_json.py            # sync's user json to db
├── data/                           # Raw dataset + notes
│   ├── ml-latest-small/            # MovieLens small dataset
│   │   ├── links.csv
│   │   ├── movies.csv
│   │   ├── ratings.csv
│   │   ├── tags.csv
│   │   └── README.txt
│   └── dataset_info.txt
├── database/                       # SQLite database management
│   ├── __init__.py
│   ├── connection.py               # get_db() / connection helpers
│   ├── db_query.py
│   ├── id_to_title.py              # for getting a title given an ID
│   ├── init_db.py                  # build schema + load CSVs into movies.db
│   └── load_movielens.py           # loads db into created schema
├── recommender/                    # Recommendation logic
│   ├── __init__.py
│   ├── baseline.py                 # simple first-pass recommender
│   └── data_loader.py              # helper functions to load CSV/DB data
├── ui/                             # user interfaces
│   ├── web/
│   │   ├── static/
│   │   │   ├── css/
│   │   │   │   └── style.css       #style sheet for page
│   │   │   └── js/
│   │   │       └── main.js      #Main javascript for page
│   │   └── templates/
│   │       └── index.html        #Main test page
│   ├──  __init__.py
├── cli.py                          # command-line interface script
├── user_profile/                   # Local user profile data
│   ├── __init__.py
│   ├── user_profile.json            #Local user profile stored as local json
│   └── user_profile_test.py        #user profile object and functionality
├── .gitignore
├── README.md
├── app.py                          # Flask app entry point
└── requirements.txt                # project dependencies

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
  - Button pressed passed via routing to api.py
    - api.py serves requests
      - Recommender reads data from the database (recommender/baseline.py + recommender/data_loader.py)
      - Top-K movie recommendations are returned
      - Results are rendered in HTML
    - javascript updates web page with results/button actions
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

## Old CLI Commands

```plaintext
General functions
    help                Show a help message w/ these commands
    clear               Clears CLI
    quit                Exit the CLI

User functions
    user                User Help
    user reset          Resets user
    user get            Get user details
    user randomize <n>  Randomly rate n movies for testing purposes
    user add rating     Add a single movie rating to local user profile

Recommend functions
    rec                 recommends 10 movies for a given user ID
    rec <k>             recommends k movies for a given user ID

```
