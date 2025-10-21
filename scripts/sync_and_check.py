from pathlib import Path
import json, sqlite3, sys, traceback

REPO_ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = REPO_ROOT / "user_profile" / "user_profile.json"
DB_PATH = REPO_ROOT / "database" / "movies.db"

def read_profile():
    if not PROFILE_PATH.exists():
        print("Profile JSON not found at", PROFILE_PATH)
        return None
    try:
        return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print("Failed to read profile JSON:", e)
        traceback.print_exc()
        return None

def ensure_tables(conn):
    cur = conn.cursor()
    # Create minimal users/ratings if they don't exist (safe: IF NOT EXISTS)
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
      user_id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE
    );
    CREATE TABLE IF NOT EXISTS ratings (
      user_id INTEGER NOT NULL,
      movie_id INTEGER NOT NULL,
      rating REAL NOT NULL,
      timestamp INTEGER NOT NULL
    );
    """)
    conn.commit()

def find_movie_id(conn, candidate):
    # candidate may be int or title string
    try:
        mid = int(candidate)
        return mid
    except Exception:
        pass
    if not isinstance(candidate, str) or candidate.strip() == "":
        return None
    s = candidate.strip()
    cur = conn.cursor()
    # exact match first (case-insensitive)
    cur.execute("SELECT movie_id FROM movies WHERE LOWER(title) = LOWER(?) LIMIT 1", (s,))
    r = cur.fetchone()
    if r:
        return int(r[0])
    # partial match
    cur.execute("SELECT movie_id FROM movies WHERE title LIKE ? LIMIT 1", (f"%{s}%",))
    r = cur.fetchone()
    if r:
        return int(r[0])
    return None

def sync():
    profile = read_profile()
    if not profile:
        return

    username = profile.get("username") or str(profile.get("user_id") or "")
    ratings = profile.get("ratings") or []
    print("Profile:", username, "ratings count:", len(ratings))

    if not DB_PATH.exists():
        print("Database file not found at", DB_PATH)
        return

    conn = sqlite3.connect(str(DB_PATH))
    try:
        ensure_tables(conn)
        cur = conn.cursor()

        # find or create user
        cur.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if row:
            uid = int(row[0])
            print("Found user_id:", uid)
        else:
            cur.execute("INSERT INTO users (username) VALUES (?)", (username,))
            conn.commit()
            uid = cur.lastrowid
            print("Created user_id:", uid)

        # delete existing ratings for this user
        cur.execute("DELETE FROM ratings WHERE user_id = ?", (uid,))
        print("Deleted existing ratings for user_id", uid)

        # insert ratings from JSON
        inserted = 0
        for entry in ratings:
            movie_raw = entry.get("movie_id") if entry.get("movie_id") is not None else entry.get("movie") or entry.get("title")
            mid = find_movie_id(conn, movie_raw)
            if mid is None:
                print("  Skipping rating with unresolved movie:", movie_raw)
                continue
            try:
                rating_val = float(entry.get("rating"))
            except Exception:
                print("  Skipping rating with invalid rating value:", entry.get("rating"))
                continue
            ts = int(entry.get("timestamp") or entry.get("time") or 0) or int(__import__("time").time())
            cur.execute(
                "INSERT INTO ratings (user_id, movie_id, rating, timestamp) VALUES (?, ?, ?, ?)",
                (uid, mid, rating_val, ts),
            )
            inserted += 1

        conn.commit()
        print(f"Inserted {inserted} ratings for user_id {uid}")

        # print current rows for the user
        cur.execute("SELECT movie_id, rating, timestamp FROM ratings WHERE user_id = ?", (uid,))
        rows = cur.fetchall()
        print("DB rows for user:", rows)
    except Exception as e:
        print("Sync error:", e)
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    print("PROFILE_PATH:", PROFILE_PATH)
    print("DB_PATH:", DB_PATH)
    sync()