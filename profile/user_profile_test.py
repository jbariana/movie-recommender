import json

class UserProfile:
    def __init__(self, username):
        self.username = username
        self.ratings = []  # list of (movie_id, rating) tuples

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

    def to_file(self):
        data = {
            "username": self.username,
            "ratings": self.ratings
        }
        with open("profile/user_profile.json", "w") as f:
            json.dump(data, f, indent=4)

    def add_rating(self, movie_id, rating): 
        self.ratings.append((movie_id, rating))
        self.to_file()

    def get_rating(self, movie_id):
        for m_id, r in self.ratings:
            if m_id == movie_id:
                return r

    def reset(self):
        self.username = "user_test"
        self.ratings = []
        self.to_file()
        
    def getUsername(self):
        return self.username
    
    def setUsername(self, new_username):
        self.username = new_username
        self.to_file()
        
    def randomize(self, num_ratings):
        import random
        movie_ids = list(range(1, 9743)) #9743 movies in dataset currently(test program so just gonna hardcode and change later) 
        self.ratings = []
        for _ in range(num_ratings):
            movie_id = random.choice(movie_ids)
            rating = random.randint(1, 5)
            self.ratings.append((movie_id, rating))
        self.to_file()

    
