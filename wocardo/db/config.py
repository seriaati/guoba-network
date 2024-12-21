from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

TORTOISE_ORM = {
    "connections": {"default": os.getenv("DATABASE_URI") or "sqlite://db.sqlite3"},
    "apps": {
        "models": {
            "models": ["wocardo.db.models", "aerich.models"],
            "default_connection": "default",
        }
    },
}
