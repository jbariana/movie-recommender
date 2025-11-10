# recommender/cache.py
from __future__ import annotations
import json, time
from pathlib import Path
from typing import Any, Optional

CACHE_DIR = Path(".cache/recs")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _path(user_id: int, key: str) -> Path:
    safe_key = key.replace("/", "_")
    return CACHE_DIR / f"u{int(user_id)}_{safe_key}.json"

def get(user_id: int, key: str, version_ts: int, ttl_seconds: int = 3600) -> Optional[Any]:
    """
    Return cached payload if it exists, is fresh (ttl), and matches version_ts.
    version_ts should reflect user's latest rating timestamp (or 0 if none).
    """
    p = _path(user_id, key)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
        if data.get("version_ts") != int(version_ts):
            return None
        if (time.time() - float(data.get("saved_at", 0))) > ttl_seconds:
            return None
        return data.get("payload")
    except Exception:
        return None

def set(user_id: int, key: str, version_ts: int, payload: Any) -> None:
    p = _path(user_id, key)
    try:
        p.write_text(json.dumps(
            {"version_ts": int(version_ts), "saved_at": time.time(), "payload": payload},
            ensure_ascii=False,
        ))
    except Exception:
        # Cache failures should never break the app
        pass

def clear(user_id: int, key: str) -> None:
    p = _path(user_id, key)
    if p.exists():
        try: p.unlink()
        except Exception: pass
