from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from ddgs import DDGS
from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException

logger = logging.getLogger(__name__)

_STATUS_URL_RE = re.compile(r"(?:x\.com|twitter\.com)/(\w+)/status/(\d+)")


class XApiError(Exception):
    """Base error for tweet-fetch failures."""


class UserNotFoundError(XApiError):
    pass


class ForbiddenError(XApiError):
    """Unused with the DDGS backend — there's no auth or account-visibility
    concept to enforce. Kept only so importers don't break."""


class AuthError(XApiError):
    """Unused with the DDGS backend — there are no credentials. Kept only
    so importers don't break."""


class NetworkError(XApiError):
    pass


class RateLimitError(XApiError):
    def __init__(self, reset_epoch: int | None) -> None:
        self.reset_epoch = reset_epoch
        super().__init__("Rate limit exceeded")


@dataclass
class TweetSearchResult:
    tweets: list[dict[str, Any]]
    exhausted: bool


class XClient:
    """DuckDuckGo-search-backed tweet fetcher.

    There is no official API involved: this scrapes indexed search results
    for `site:x.com` / `site:twitter.com` status-URL hits, the same approach
    as the original get_tweets_search.py. Results reflect whatever DDG has
    indexed — not a live, authoritative read of the account's timeline.
    """

    def __init__(self, timeout: int = 10) -> None:
        self._timeout = timeout

    def get_recent_tweets(self, handle: str, max_results: int) -> TweetSearchResult:
        query = f'"{handle}" (site:x.com OR site:twitter.com)'
        try:
            with DDGS(timeout=self._timeout) as ddgs:
                raw_results = ddgs.text(query, max_results=max_results)
        except RatelimitException as exc:
            raise RateLimitError(None) from exc
        except TimeoutException as exc:
            raise NetworkError(f"DDGS request timed out: {exc}") from exc
        except DDGSException as exc:
            # ddgs raises this same exception both for a genuinely empty
            # result set and for some silent engine-level blocks (e.g. a
            # 429/202 page that just fails to parse into results) — there's
            # no status code or header to tell those apart here, so "no
            # results found" text is treated as an empty search and anything
            # else as a network-layer failure.
            if "no results found" in str(exc).lower():
                raw_results = []
            else:
                raise NetworkError(f"DDGS search failed: {exc}") from exc

        exhausted = len(raw_results) < max_results

        seen_ids: set[int] = set()
        tweets: list[dict[str, Any]] = []
        for r in raw_results:
            url = r.get("href", "")
            match = _STATUS_URL_RE.search(url)
            if not match:
                continue
            if match.group(1).lower() != handle.lower():
                continue
            tweet_id = int(match.group(2))
            if tweet_id in seen_ids:
                continue
            seen_ids.add(tweet_id)
            tweets.append(
                {
                    "id": tweet_id,
                    "title": r.get("title", ""),
                    "url": url,
                    "snippet": r.get("body", ""),
                }
            )

        tweets.sort(key=lambda t: t["id"], reverse=True)

        if not tweets:
            raise UserNotFoundError(f"No tweets found for @{handle} in DuckDuckGo's index.")

        return TweetSearchResult(tweets=tweets, exhausted=exhausted)
