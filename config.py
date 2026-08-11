from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_CACHE_TTL_HOURS = 1.0
# Hosts like Render's free tier have an ephemeral, sometimes read-only app
# directory; the OS temp dir is reliably writable everywhere.
DEFAULT_CACHE_PATH = str(Path(tempfile.gettempdir()) / "x-tweet-agent-cache.sqlite3")


@dataclass(frozen=True)
class Config:
    cache_path: Path
    cache_ttl_hours: float

    @classmethod
    def load(
        cls,
        cache_path: str | None = None,
        cache_ttl_hours: float | None = None,
    ) -> "Config":
        # No credentials needed: the DDGS backend is unauthenticated. .env is
        # entirely optional here, only for overriding cache path/TTL.
        load_dotenv()

        resolved_ttl = cache_ttl_hours
        if resolved_ttl is None:
            resolved_ttl = float(os.environ.get("CACHE_TTL_HOURS", DEFAULT_CACHE_TTL_HOURS))

        resolved_path = cache_path or os.environ.get("CACHE_PATH", DEFAULT_CACHE_PATH)

        return cls(
            cache_path=Path(resolved_path),
            cache_ttl_hours=resolved_ttl,
        )
