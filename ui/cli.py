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
        if command == "clear":
            clear()
            continue
        
        # USER: handle all user/* subcommands via startswith
        if command.startswith("user"):
            parts = command.split()
            # user alone -> print user help
            if len(parts) == 1:
                print("""\

user                User Help   
user reset          Resets user
user get            Get user details
user update         Update username
user randomize <n>  Randomly rate n movies for testing purposes
add rating          Add a single movie rating to local user profile""")
                continue

            sub = parts[1]
            if sub == "reset":
                user.reset()
                print("User reset to default values.")
                continue

            if sub == "get":
                print()
                print(f"Username: {user.getUsername()}\nRatings: {user.ratings}")
                continue

            if sub == "update":
                user.setUsername(input("Enter new username: ").strip())
                print("Username updated.")
                continue

            if sub == "randomize":
                if len(parts) != 3 or not parts[2].isdigit():
                    print("Usage: user randomize <n>  (where n is a positive integer)")
                    continue
                n = int(parts[2])
                if n <= 0:
                    print("Please enter a positive integer for n.")
                    continue
                user.randomize(n)
                print(f"User profile randomized with {n} random ratings.")
                continue
            #ADD SINGLE RATING TO USER
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
                
            else:
                print("Unknown user subcommand. Type 'user' for help.")
            continue
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
        if command.startswith("rec"):
            parts = command.split()
            k = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None

            user_id = input("Enter user ID: ").strip()
            print()
            # account for 'REC'
            if k is None:
                k = 10

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
        if command == "help":
            print("""\

Available commands:

General:
    help                Show this help message 
    clear               Clears CLI
    quit                Exit the CLI

User:
    user                User Help   
    user reset          Resets user
    user get            Get user details
    user update         Update username
    user randomize <n>  Randomly rate n movies for testing purposes
    user add rating     Add a single movie rating to local user profile
                  
Recommend:
    rec                 recommends 10 movies for a given user ID
    rec <k>             recommends k movies for a given user ID""")
            continue
        else:
            print("Unknown command. Type 'help' for a list of commands.")
            continue