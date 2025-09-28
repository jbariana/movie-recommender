import os
from profile.user_profile_test import UserProfile
from recommender.baseline import recommend_titles_for_user


def clear(): 
    os.system('cls' if os.name == 'nt' else 'clear')

user = UserProfile.from_file("profile/user_profile.json")

def cli():
    clear()


    print("Welcome to the Movie Recommender CLI \nType 'help' for commands or 'quit' to exit.")


    while True:
        command = input("> ").strip().lower()
        #QUIT
        if command == "quit":
            print("Exiting...")
            break
        
        #CLEAR
        elif command == "clear":
            clear()
            continue
        
        #USER HELP
        elif command == "user":
            print("User test functions: \n\nuser reset - Resets user \nuser get - Get user details \nuser update - Update username")
            continue
        #USER RESET, GET, UPDATE
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

        #ADD SINGLE RATING TO USER
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

        # RECOMMEND: allow rec or rec <k>
        elif command.startswith("rec"):
            parts = command.split()
            k = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None

            user_id = input("Enter user ID: ").strip()

            # account for 'REC'
            if k is None:
                k_input = input("Enter number of recommendations (default 10): ").strip()
                k = int(k_input) if k_input.isdigit() else 10

            try:
                user_id = int(user_id)
            except ValueError:
                print("Invalid user ID. It must be an integer.")
                continue

            recommendations = recommend_titles_for_user(user_id, k)
            if recommendations:
                print(f"Top {k} recommendations for user {user_id}:")
                for title, score in recommendations:
                    print(f"{title}  (score={score:.3f})")
            else:
                print(f"No recommendations found for user {user_id}.")
            continue

        #HELP
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
    add rating     Add a movie rating to local user profile
                  
Recommend:
    rec <k>        reccommends k movies for a given user ID
                  """)
            continue
        else:
            print("Unknown command. Type 'help' for a list of commands.")
            continue