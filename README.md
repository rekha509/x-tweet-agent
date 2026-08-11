# x-tweet-agent

Fetch an X (Twitter) handle's recent tweets via DuckDuckGo search — no API
key needed. Results are search-indexed and approximate, not a live timeline
read.

**Must run on your own machine, not a cloud host.** DuckDuckGo (and the other
engines this aggregates across) blocks requests from cloud/datacenter IPs far
more aggressively than home connections, so this reliably works locally but
not when deployed to Render, Railway, Fly.io, etc. — they all hit the same
block. There's no permanent hosted link because of this. There IS a way to
get a temporary public link without deploying anywhere: see "Share a public
link" below — the app still runs on your machine (so its outbound searches
use your normal home IP, not a blocked one), a Cloudflare Tunnel just forwards
public internet traffic to it.

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

## Share a public link (temporary)

Double-click `start.bat`. It starts the app on port 8080 and opens a
[Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/do-more-with-tunnels/trycloudflare/)
(no account, no login) pointing at it, in two separate windows.

Look in the "Public Link" window for a line like:

```
https://some-random-words.trycloudflare.com
```

That's the link to share. Two things to know:

- **The URL is random and changes every time** you run `start.bat` — it's a
  new "quick tunnel" each run, not a fixed address.
- **The link only works while both windows from `start.bat` stay open.**
  Closing either one (or shutting down your machine) takes the link down.
  Run `start.bat` again to get a new one.

`start.bat` expects `cloudflared.exe` in this same folder — it's not committed
to the repo (Windows-only binary), so if it's missing, download it with:

```
curl -L -o cloudflared.exe https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
```

`start.bat` also depends on setup above having been done first (`pip install
-r requirements.txt`).
