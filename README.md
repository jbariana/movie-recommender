# Movie Recommender

## Overview
Uses python for AI based recommendations on movies based on publicly available databases of movies and user ratings. 

## Project Structure
movie_recommender/
├── .venv/                          # (local) virtual environment — user-specific
├── .vscode/
│   └── settings.json               # VS Code Python settings / interpreter path
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
│   └── movies.db                   # generated after running init_db.py
│
├── profile/                        # Local user profile (optional)
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
├── ui/                             # Lightweight user interface(s)
│   ├── __init__.py
│   └── CLI_recommend.py            # CLI to print Top-K recs for a user
│
├── .gitignore
├── main.py                         # optional entry point (can delegate to CLI)
├── README.md
├── requirements.lock.txt
└── requirements.txt                # project dependencies

## TL;DR Flow (what happens when you “use it”)
- Data arrives → We have CSV files (movies.csv, ratings.csv, etc.) in data/.
- We build a database → database/init_db.py reads those CSVs and fills movies.db (a SQLite file).
- We ask for recommendations → The CLI app (ui/CLI_recommend.py) asks the recommender code to pick movies.
- Recommender answers → recommender/baseline.py + recommender/data_loader.py read from the DB and return Top-K movies.
- You see results → The CLI prints the list.

