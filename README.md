# x-tweet-agent

Fetch an X (Twitter) handle's recent tweets via DuckDuckGo search — no API
key needed. Results are search-indexed and approximate, not a live timeline
read.

**Runs locally only.** DuckDuckGo (and the other engines this aggregates
across) blocks requests from cloud/datacenter IPs far more aggressively than
home connections, so this reliably works on your own machine but not when
deployed to a cloud host (Render, Railway, Fly.io, etc. all hit the same
block). There is no public hosted link — everyone who wants to use this
needs to clone and run it themselves, as below.

## Get the code

```
git clone https://github.com/rekha509/x-tweet-agent.git
cd x-tweet-agent
```

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

Web app (search page + API, at `http://localhost:8080/`):

```
python api.py
```

or, equivalently:

```
uvicorn api:app --host 0.0.0.0 --port 8080
```

`api.py` reads the port from the `PORT` env var (default `8080`) if you want
to run it on a different port.

The SQLite cache defaults to a file in the OS temp directory.
