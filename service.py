from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cache import Cache
from config import Config
from xclient import UserNotFoundError, XClient

# Fixed page size fetched from DDGS and cached in full, so any count up to
# this ceiling can be served from a single cached fetch. Matches the
# max_results used by the original get_tweets_search.py.
MAX_FETCH = 25


@dataclass
class TweetResult:
    username: str
    tweets: list[dict[str, Any]]
    from_cache: bool


class TweetService:
    """Fetch a handle's recent tweets via search, cache-aware.

    Kept free of argparse/CLI concerns so it can be reused as-is behind a
    FastAPI route or any other frontend.
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._cache = Cache(config.cache_path)
        self._client = XClient()

    def close(self) -> None:
        self._cache.close()

    def get_recent_tweets(
        self,
        handle_or_id: str,
        count: int = 3,
        refresh: bool = False,
    ) -> TweetResult:
        handle = handle_or_id.lstrip("@")
        cache_key = handle.lower()

        response = None
        if not refresh:
            if self._cache.get_negative_lookup(cache_key):
                raise UserNotFoundError(f"No tweets found for @{handle} (cached).")
            cached = self._cache.get_tweets(cache_key, self._config.cache_ttl_hours)
            if cached is not None and (len(cached.response.get("data") or []) >= count or cached.exhausted):
                response = cached.response
        from_cache = response is not None

        if response is None:
            try:
                search_result = self._client.get_recent_tweets(handle, MAX_FETCH)
            except UserNotFoundError:
                self._cache.store_negative_lookup(cache_key)
                raise
            response = {"data": search_result.tweets}
            self._cache.store_tweets(cache_key, response, search_result.exhausted)

        tweets = (response.get("data") or [])[:count]
        return TweetResult(username=handle, tweets=tweets, from_cache=from_cache)
