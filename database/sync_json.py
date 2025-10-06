from __future__ import annotations
import json
import pandas as pd
from pathlib import Path
from typing import Optional

PROFILE_PATH = Path("profile/user_profile.json")

def sync_user_ratings(df: pd.DataFrame) -> None:
    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if PROFILE_PATH.exists():
        with open(PROFILE_PATH, "r") as f:
            existing = json.load(f)
        cur = pd.DataFrame(existing.get("ratings", []))
    else:
        cur = pd.DataFrame(columns=["userId", "movieId", "rating"])

    all_df = pd.concat([cur, df[["userId", "movieId", "rating"]]], ignore_index=True)
    all_df = all_df.drop_duplicates(subset=["userId", "movieId"], keep="last").sort_values(["userId", "movieId"]).reset_index(drop=True)

    with open(PROFILE_PATH, "w") as f:
        json.dump({"ratings": all_df.to_dict(orient="records")}, f, indent=2)

def load_user_ratings_df() -> Optional[pd.DataFrame]:
    if not PROFILE_PATH.exists():
        return None
    with open(PROFILE_PATH, "r") as f:
        data = json.load(f)
    return pd.DataFrame(data.get("ratings", []))
