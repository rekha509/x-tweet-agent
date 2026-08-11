@echo off
cd /d "%~dp0"

echo Starting the server and public tunnel...
echo.

start "X Tweet Agent - Server (do not close)" cmd /k python -m uvicorn api:app --host 127.0.0.1 --port 8080

timeout /t 3 /nobreak >nul

start "X Tweet Agent - Public Link (do not close)" cmd /k cloudflared.exe tunnel --url http://127.0.0.1:8080

echo Two windows just opened:
echo   1. "X Tweet Agent - Server"      - runs the app
echo   2. "X Tweet Agent - Public Link" - runs the tunnel
echo.
echo In the "Public Link" window, look for a line like:
echo   https://some-random-words.trycloudflare.com
echo That is your public link for this run. Share it with friends.
echo.
echo IMPORTANT: the link changes every time you run this script, and it
echo only works while BOTH of those windows stay open. Closing this launcher
echo window (e.g. with a key below) will NOT stop them, since they run in
echo their own separate windows - but closing the "Server" or "Public Link"
echo window directly will stop that part and break the link.
echo.
pause
