import argparse
from recommender.baseline import recommend_titles_for_user

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--user", type=int, required=True)
    p.add_argument("--k", type=int, default=10)
    args = p.parse_args()
    for title, score in recommend_titles_for_user(args.user, args.k):
        print(f"{title}  (score={score:.3f})")

if __name__ == "__main__":
    main()
