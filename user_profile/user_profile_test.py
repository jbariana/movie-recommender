import json
from pathlib import Path
import time
from api.sync_user_json import sync_user_ratings

PROFILE_PATH = Path(__file__).parent / "user_profile.json"

class UserProfile:
    def __init__(self, user_id):
        self.user_id = user_id
        # ratings as list of dicts: {"movie_id": int, "rating": float, "timestamp": int}
        self.ratings = []

    @classmethod
    def from_file(cls, filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            user = cls(data.get("user_id", "xxxxxx"))
            user.ratings = data.get("ratings", [])
            return user
        except FileNotFoundError:
            return cls("xxxxxx")

    def get_ratings_from_json():
        return json.load(open(PROFILE_PATH, "r", encoding="utf-8")).get("ratings", [])

    def to_file(self):
        data = {
            "user_id": self.user_id,
            "ratings": self.ratings
        }
        PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        # trigger sync right after writing the profile (one-shot, no watcher)
        try:
            sync_user_ratings(PROFILE_PATH)
        except Exception as e:
            print(f"Warning: sync failed: {e}")

    def add_rating(self, movie_id, rating):
        entry = {
            "movie_id": int(movie_id),
            "rating": float(rating),
            "timestamp": int(time.time())
        }
        self.ratings.append(entry)
        self.to_file()

    def get_rating(self, movie_id):
        for r in self.ratings:
            if r.get("movie_id") == movie_id:
                return r.get("rating")

    def reset(self):
        self.user_id = "99"
        self.ratings = []
        self.to_file()
        
    def getUserID(self):
        return self.user_id
    
    def setUserID(self, new_user_id):
        self.user_id = new_user_id
        self.to_file()
        
    def randomize(self, num_ratings):
        import random
        movie_ids = list(range(1, 9743))
        self.ratings = []
        for _ in range(num_ratings):
            movie_id = random.choice(movie_ids)
            rating = random.randint(1, 5)
            self.ratings.append({
                "movie_id": movie_id,
                "rating": rating,
                "timestamp": int(time.time())
            })
        self.to_file()


