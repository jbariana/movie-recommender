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
