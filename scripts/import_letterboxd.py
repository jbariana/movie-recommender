import csv
import requests
from database.id_to_title import title_to_id
from api.api import save_rating

def import_from_letterboxd(username, user_id=1):
    """
    Imports ratings from the user's Letterboxd diary CSV export.
    You must have a public Letterboxd profile.
    """
    url = f"https://letterboxd.com/{username}/films/diary/export/"
    print(f"[INFO] Fetching Letterboxd diary from: {url}")

    resp = requests.get(url)
    if resp.status_code != 200:
        print("[ERROR] Could not download diary export. Is username correct?")
        return

    rows = resp.text.splitlines()
    reader = csv.DictReader(rows)

    imported = 0

    for row in reader:
        title = row.get("Name")
        rating_str = row.get("Rating")

        if not title or not rating_str:
            continue  # skip movies with no rating

        try:
            rating = float(rating_str)
        except:
            continue

        movie_id = title_to_id(title)  # map title → movie_id in DB
        if not movie_id:
            print(f"[WARN] Title not found in your local DB: {title}")
            continue

        save_rating(user_id, movie_id, rating)
        imported += 1

    print(f"[DONE] Imported {imported} ratings from Letterboxd for user {user_id}.")
