# Movie Recommender

## Overview
Uses python for AI based recommendations on movies based on publicly available databases of movies and user ratings. 

## Proj Structure
```plaintext
movie_recommender/
├── data/                      # Datasets, db inits, etc.
│   ├── dataset_info.txt        # documentation on our data set
│   └── ml_latest_small.zip     # small version of movielens dataset
├── database/                  # SQLite database management
│   └──
├── profile/                   # Local user profile
│   ├── __init__.py             # init file 
│   ├── user_profile_test.py    # includes object structure and methods for user objects
│   └── user_profile.json       # stores current local user, auto-updated
├── recommender/               # AI/ML recommendation logic
│   └──
├── ui/                        # user interface :P
│   ├── __init__.py             # init file
│   └── CLI.py                  # CLI interface for testing
├── main.py                     # entry point
├── README.md                   # here you are :D
└── requirements.txt            # dependencies and necessary libraries
```

