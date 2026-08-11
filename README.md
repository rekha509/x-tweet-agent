# x-tweet-agent

Fetch an X (Twitter) handle's recent tweets via DuckDuckGo search — no API
key needed. Results are search-indexed and approximate, not a live timeline
read.

## Setup

```
pip install -r requirements.txt
```

No `.env` is required. See `.env.example` for the two optional overrides
(`CACHE_TTL_HOURS`, `CACHE_PATH`).

## Run

CLI:

```
python agent.py jack --count 3
```

Web app + API (serves the search page at `/`, and `GET /tweets/{handle}`):

```
uvicorn api:app --host 0.0.0.0 --port 8080
```

or, equivalently:

```
python api.py
```

`api.py` reads the port from the `PORT` env var (default `8080`) and binds to
`0.0.0.0`, so it's ready to deploy as-is (e.g. Render: build command
`pip install -r requirements.txt`, start command `python api.py`).

The SQLite cache defaults to a file in the OS temp directory, since some
hosts' app directories are read-only or wiped between deploys.
