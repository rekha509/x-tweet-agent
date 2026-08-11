from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Iterator

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from config import Config
from service import TweetResult, TweetService
from xclient import (
    AuthError,
    ForbiddenError,
    NetworkError,
    RateLimitError,
    UserNotFoundError,
    XApiError,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

APPROXIMATE_RESULTS_NOTE = (
    "Results come from DuckDuckGo's search index, not a live timeline read: "
    "they are approximate and may not be the literal last N tweets."
)

app = FastAPI(
    title="X Tweet Agent API",
    description=APPROXIMATE_RESULTS_NOTE,
)

config = Config.load()

STATIC_DIR = Path(__file__).parent / "static"


class TweetOut(BaseModel):
    id: int
    title: str
    snippet: str
    url: str


class TweetsResponse(BaseModel):
    username: str
    from_cache: bool
    tweets: list[TweetOut]


def get_service() -> Iterator[TweetService]:
    service = TweetService(config)
    try:
        yield service
    finally:
        service.close()


def _to_response(result: TweetResult) -> TweetsResponse:
    return TweetsResponse(
        username=result.username,
        from_cache=result.from_cache,
        tweets=[
            TweetOut(
                id=tw["id"],
                title=tw.get("title", ""),
                snippet=tw.get("snippet", ""),
                url=tw.get("url", ""),
            )
            for tw in result.tweets
        ],
    )


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


@app.get(
    "/tweets/{handle}",
    response_model=TweetsResponse,
    description=f"Fetch a handle's recent tweets. {APPROXIMATE_RESULTS_NOTE}",
)
def get_tweets(
    handle: str,
    count: int = Query(3, ge=1),
    refresh: bool = False,
    service: TweetService = Depends(get_service),
) -> TweetsResponse:
    try:
        result = service.get_recent_tweets(handle, count=count, refresh=refresh)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except AuthError as exc:
        raise HTTPException(status_code=500, detail="Internal server error") from exc
    except RateLimitError as exc:
        raise HTTPException(status_code=429, detail="Rate limit exceeded") from exc
    except NetworkError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except XApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return _to_response(result)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
