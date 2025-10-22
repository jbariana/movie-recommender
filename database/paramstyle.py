# database/paramstyle.py
import os
IS_PG = bool(os.getenv("DATABASE_URL", "").strip())
PH = "%s" if IS_PG else "?"
def ph_list(n: int) -> str:
    return ",".join(PH for _ in range(n))