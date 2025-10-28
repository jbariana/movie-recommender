import os
from typing import Any, List, Tuple

from user_profile.user_profile_test import UserProfile
from recommender.baseline import recommend_titles_for_user
from database.id_to_title import id_to_title


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


class Rating:
    def __init__(self, movie_id: int, rating: int):
        self.movie_id = movie_id
        self.rating = rating

    @classmethod
    def from_any(cls, r: Any):
        if isinstance(r, cls):
            return r
        if isinstance(r, dict):
            mid = r.get("movie_id") or r.get("movieId") or r.get("id")
            rating_val = r.get("rating")
        elif isinstance(r, (list, tuple)) and len(r) >= 2:
            mid = r[0]
            rating_val = r[1]
        else:
            raise ValueError("Unknown rating format")
        return cls(int(mid), int(rating_val))


# load current user profile
user = UserProfile.from_file("profile/user_profile.json")


def print_user_ratings(ratings: List[Any]):
    if not ratings:
        print("Ratings: []")
        return
    print("Ratings:")
    for r in ratings:
        try:
            ro = Rating.from_any(r)
        except Exception:
            print(f"  {r}")
            continue
        title = id_to_title(ro.movie_id)
        if title:
            print(f"  {title}  (id={ro.movie_id}, rating={ro.rating})")
        else:
            print(f"  id={ro.movie_id}  (rating={ro.rating})")


def cli():
    clear()
    print("Welcome to the Movie Recommender CLI \nType 'help' for commands or 'quit' to exit.")

    while True:
        command = input("> ").strip().lower()

        if command == "quit":
            print("Exiting...")
            break

        if command == "clear":
            clear()
            continue

        if command.startswith("user"):
            parts = command.split()
            if len(parts) == 1:
                print("""
user                User Help   
user reset          Resets user
user get            Get user details
user randomize <n>  Randomly rate n movies for testing purposes
user add            Add a single movie rating to local user profile""")
                continue

            sub = parts[1]

            if sub == "reset":
                user.reset()
                print("User reset to default values.")
                continue

            if sub == "get":
                print()
                print(f"User ID: {user.getUserID()}")
                ratings = getattr(user, "ratings", []) or []
                print_user_ratings(ratings)
                continue

            if sub == "randomize":
                if len(parts) != 3 or not parts[2].isdigit():
                    print("Usage: user randomize <n>")
                    continue
                n = int(parts[2])
                user.randomize(n)
                print(f"User profile randomized with {n} random ratings.")
                continue

            if sub == "add":
                try:
                    movie_id = int(input("Enter movie ID: ").strip())
                    rating = int(input("Enter rating (1-5): ").strip())
                    if rating < 1 or rating > 5:
                        print("Rating must be between 1 and 5.")
                        continue
                    user.add_rating(movie_id, rating)
                    print(f"Added rating {rating} for movie ID {movie_id}.")
                except ValueError:
                    print("Invalid input. Movie ID and rating must be integers.")
                continue

            print("Unknown user subcommand. Type 'user' for help.")
            continue

        if command.startswith("rec"):
            parts = command.split()
            k = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
            user_id_str = input("Enter user ID: ").strip()
            try:
                user_id = int(user_id_str)
            except ValueError:
                print("Invalid user ID. It must be an integer.")
                continue

            recommendations: List[Tuple[str, float]] = recommend_titles_for_user(user_id, k)
            if recommendations:
                print(f"Top {k} recommendations for user {user_id}:")
                for title, score in recommendations:
                    print(f"{title}  (score={score:.3f})")
            else:
                print(f"No recommendations found for user {user_id}.")
            continue

        if command == "help":
            print("""
Available commands:

General:
    help                Show this help message 
    clear               Clears CLI
    quit                Exit the CLI

User:
    user                User Help   
    user reset          Resets user
    user get            Get user details
    user randomize <n>  Randomly rate n movies for testing purposes
    user add            Add a single movie rating to local user profile
                  
Recommend:
    rec                 recommends 10 movies for a given user ID
    rec <k>             recommends k movies for a given user ID""")
            continue

        print("Unknown command. Type 'help' for a list of commands.")

from api.movies import save_rating

def rate_movie(movie_id):
    rating = input("Rate this movie (1-5): ")

    # Basic validation
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            print("Rating must be between 1 and 5.")
            return
    except ValueError:
        print("Invalid number.")
        return

    save_rating(user_id=1, movie_id=movie_id, rating=rating)
    print("✅ Rating saved!\n")
