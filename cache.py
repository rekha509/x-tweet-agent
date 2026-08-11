from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

NEGATIVE_LOOKUP_TTL_SECONDS = 15 * 60


@dataclass
class CachedTweets:
    response: dict[str, Any]
    exhausted: bool


class Cache:
    """SQLite-backed cache.

    Two tables:
      - negative_lookups: handles that recently returned zero results, expired
        by a short TTL, so a typo'd handle doesn't re-hit search on every retry.
      - tweets: raw search results keyed by handle, expired by TTL.
    """

    def __init__(self, db_path: Path) -> None:
        self._conn = sqlite3.connect(str(db_path))
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA busy_timeout=5000;")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS negative_lookups (
                key TEXT PRIMARY KEY,
                failed_at REAL NOT NULL
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tweets (
                cache_key TEXT PRIMARY KEY,
                response_json TEXT NOT NULL,
                fetched_at REAL NOT NULL,
                exhausted INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        try:
            self._conn.execute("ALTER TABLE tweets ADD COLUMN exhausted INTEGER NOT NULL DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # column already exists (fresh DB, or already migrated)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # -- negative lookups (short TTL) --

    def get_negative_lookup(self, key: str) -> bool:
        row = self._conn.execute(
            "SELECT failed_at FROM negative_lookups WHERE key = ?",
            (key,),
        ).fetchone()
        if not row:
            return False
        return (time.time() - row[0]) <= NEGATIVE_LOOKUP_TTL_SECONDS

    def store_negative_lookup(self, key: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO negative_lookups (key, failed_at) VALUES (?, ?)",
            (key, time.time()),
        )
        self._conn.commit()

    # -- tweets (TTL) --

    def get_tweets(self, cache_key: str, ttl_hours: float) -> CachedTweets | None:
        row = self._conn.execute(
            "SELECT response_json, fetched_at, exhausted FROM tweets WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
        if not row:
            return None
        response_json, fetched_at, exhausted = row
        age_hours = (time.time() - fetched_at) / 3600
        if age_hours > ttl_hours:
            return None
        return CachedTweets(response=json.loads(response_json), exhausted=bool(exhausted))

    def store_tweets(self, cache_key: str, response: dict[str, Any], exhausted: bool) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO tweets (cache_key, response_json, fetched_at, exhausted) VALUES (?, ?, ?, ?)",
            (cache_key, json.dumps(response), time.time(), int(exhausted)),
        )
        self._conn.commit()
