import os
from profile.user_profile_test import UserProfile


def clear(): 
    os.system('cls' if os.name == 'nt' else 'clear')

user = UserProfile.from_file("user_profile.json") # to be done

def cli():
    clear()
    print("Welcome to the Movie Recommender CLI \nType 'help' for commands or 'quit' to exit.")
    while True:
        command = input("> ").strip().lower()
        if command == "quit":
            print("Exiting...")
            break
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
    user update    Update username""")
            
        elif command == "clear":
            clear()
            continue
        
        elif command == "user":
            print("User test functions: \n\nuser reset - Resets user \nuser get - Get user details \nuser update - Update username")
            continue
        elif command == "user reset":
            user.reset()   
            print("To be Implemented:")
            continue
        elif command == "user get":
            print("To be Implemented:")
            continue
        elif command == "user update": 
            print("To be Implemented:")
            continue
