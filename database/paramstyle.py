"""
paramstyle.py
provides database-agnostic SQL parameter placeholders
switches between postgres (%s) and sqlite (?) styles
"""

import os

#check if using postgres (DATABASE_URL set) or sqlite (default)
IS_PG = bool(os.getenv("DATABASE_URL", "").strip())

#use postgres-style %s or sqlite-style ? placeholders
PH = "%s" if IS_PG else "?"

#generate comma-separated placeholder list for IN clauses
def ph_list(n: int) -> str:
    return ",".join(PH for _ in range(n))