# Movie Recommender

## Overview

Uses Python to generate AI-based movie recommendations from public datasets (MovieLens) and user ratings. This repo includes a SQLite database loader, a baseline recommender, and a simple CLI to print Top-K picks.

## Project Structure

```plaintext
movie_recommender/
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
├── ui/                             # user interface(s)
│   ├── __init__.py
│   └── CLI.py                      # main ui
│
├── .gitignore
├── main.py                         # entry point
├── README.md                      
└── requirements.lock.txt          # project dependencies
```

## TL;DR Flow (what happens when you “use it”)
```plaintext
- Run Main
- Main makes call to initialize the database
    - databse.init_db.main creates SQLite schema for data
- Main calls load db function
    - database.load_movielens.main loads data from csvs into schema 
- Main calls UI (CLI currently)
- CLI accesses recommend and profile to execute commands
    - Recommender answers → recommender/baseline.py + recommender/data_loader.py read from the DB and return Top-K movies.
    - You see results → The CLI prints the list.
```
## INSTALL INFO
```plaintext
1. clone repository
    git clone <url>

2. Install dependencies shown in 'requirements.lock.txt'

3. Run the project
    python -m main
```
## Current CLI Commands
```plaintext
General functions
    help                Show a help message w/ these commands
    clear               Clears CLI
    quit                Exit the CLI

User functions
    user                User Help   
    user reset          Resets user
    user get            Get user details
    user update         Update username
    user randomize <n>  Randomly rate n movies for testing purposes
    user add rating     Add a single movie rating to local user profile
                  
Recommend functions
    rec                 recommends 10 movies for a given user ID
    rec <k>             recommends k movies for a given user ID

```
