# cache.py
import time
from functools import wraps
from typing import Any, Callable, Hashable, Tuple

class SimpleCache:
    def __init__(self, default_ttl: int = 900):
        self.store: dict[Hashable, Tuple[Any, float | None]] = {}
        self.default_ttl = default_ttl

    def _expired(self, exp: float | None) -> bool:
        return exp is not None and exp < time.time()

    def get(self, key: Hashable):
        item = self.store.get(key)
        if not item:
            return None
        value, exp = item
        if self._expired(exp):
            self.store.pop(key, None)
            return None
        return value

    def set(self, key: Hashable, value: Any, ttl: int | None = None):
        ttl = self.default_ttl if ttl is None else ttl
        exp = (time.time() + ttl) if ttl > 0 else None
        self.store[key] = (value, exp)

    def delete(self, key: Hashable):
        self.store.pop(key, None)

    def cached(self, ttl: int | None = None, key_fn: Callable[..., Hashable] | None = None):
        def deco(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                key = key_fn(*args, **kwargs) if key_fn else (fn.__name__, args, frozenset(kwargs.items()))
                hit = self.get(key)
                if hit is not None:
                    return hit
                val = fn(*args, **kwargs)
                self.set(key, val, ttl=ttl)
                return val
            return wrapper
        return deco

cache = SimpleCache()

# helper for targeted invalidation used by rating updates
def key_content_recs(user_id: int, k: int = 20, **kw):
    # keep tuple stable & hashable
    return ("content_recs", int(user_id), int(k), tuple(sorted(kw.items())))
