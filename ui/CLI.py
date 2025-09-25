import os
from profile.user_profile_test import UserProfile


def clear(): 
    os.system('cls' if os.name == 'nt' else 'clear')

user = UserProfile.from_file("profile/user_profile.json")

def cli():
    clear()
    print("Welcome to the Movie Recommender CLI \nType 'help' for commands or 'quit' to exit.")
    while True:
        command = input("> ").strip().lower()
        if command == "quit":
            print("Exiting...")
            break
            
        elif command == "clear":
            clear()
            continue
        
        elif command == "user":
            print("User test functions: \n\nuser reset - Resets user \nuser get - Get user details \nuser update - Update username")
            continue
        elif command == "user reset":
            user.reset()   
            print("User reset to default values.")
            continue
        elif command == "user get":
            print(f"Username: {user.getUsername()}\nRatings: {user.ratings}")
            continue
        elif command == "user update": 
            user.setUsername(input("Enter new username: ").strip())
            print("Username updated.")     
            continue
        elif command == "add rating":
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

        elif command == "help":
            print("""\
Available commands:

General:
    help           Show this help message 
    clear          Clears CLI
    quit           Exit the CLI

User:
    user           User Help   
    user reset     Resets user
    user get       Get user details
    user update    Update username
    add rating     Add a movie rating to local user profile""")
            continue
        else:
            print("Unknown command. Type 'help' for a list of commands.")
            continue