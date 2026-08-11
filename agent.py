from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any

from config import Config
from service import TweetResult, TweetService
from xclient import RateLimitError, XApiError

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

APPROXIMATE_RESULTS_NOTE = (
    "Results come from DuckDuckGo's search index, not a live timeline read: "
    "they are approximate and may not be the literal last N tweets."
)


def print_pretty(result: TweetResult) -> None:
    if result.from_cache:
        print("(served from cache)")

    if not result.tweets:
        print(f"No tweets found for @{result.username}.")
        return

    for i, tw in enumerate(result.tweets, 1):
        print(f"{i}. {tw.get('title', '')}")
        print(f"   {tw.get('snippet', '')}")
        print(f"   {tw.get('url', '')}")
        print()


def print_json(result: TweetResult) -> None:
    payload: dict[str, Any] = {
        "username": result.username,
        "from_cache": result.from_cache,
        "tweets": [
            {
                "id": tw["id"],
                "title": tw.get("title"),
                "snippet": tw.get("snippet"),
                "url": tw.get("url"),
            }
            for tw in result.tweets
        ],
    }
    print(json.dumps(payload, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"Fetch the last N tweets for an X (Twitter) handle. {APPROXIMATE_RESULTS_NOTE}"
    )
    parser.add_argument("handle_or_id", help="Username, with or without @")
    parser.add_argument("--count", type=int, default=3, help="Number of tweets to return (default: 3)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of pretty text")
    parser.add_argument(
        "--ttl",
        type=float,
        default=None,
        help="Cache TTL in hours for tweet data (default: 1, or CACHE_TTL_HOURS in .env)",
    )
    parser.add_argument(
        "--cache-path",
        default=None,
        help="Path to the SQLite cache file (default: cache.sqlite3, or CACHE_PATH in .env)",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Bypass cached tweet data and force a fresh search",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    if args.count < 1:
        print("error: --count must be at least 1", file=sys.stderr)
        return 2

    config = Config.load(cache_path=args.cache_path, cache_ttl_hours=args.ttl)

    service = TweetService(config)
    try:
        result = service.get_recent_tweets(
            args.handle_or_id,
            count=args.count,
            refresh=args.refresh,
        )
    except RateLimitError:
        print(
            "error: rate limited by the search backend (no retry time is provided). "
            "Wait a while before retrying.",
            file=sys.stderr,
        )
        return 3
    except XApiError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        service.close()

    if args.json:
        print_json(result)
    else:
        print_pretty(result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
