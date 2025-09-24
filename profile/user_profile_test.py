import json

class UserProfile:
    def __init__(self, username):
        self.username = username
        self.ratings = []  # list of (movie_id, rating) tuples

    def add_rating(self, movie_id, rating): 
        self.ratings.append((movie_id, rating))

    def get_rating(self, movie_id):
        for m_id, r in self.ratings:
            if m_id == movie_id:
                return r

    def reset(self):
        self.username = "xxxxxx"
        self.ratings = []

    @classmethod
    def from_file(cls, filename):
        try:
            with open(filename, "r") as f:
                data = json.load(f)
            user = cls(data["username"])
            user.ratings = data.get("ratings", [])
            return user
        except FileNotFoundError:
            # If file doesn't exist, return a default user
            return cls("xxxxxx")

    def to_file(self, filename):
        data = {
            "username": self.username,
            "ratings": self.ratings
        }
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
