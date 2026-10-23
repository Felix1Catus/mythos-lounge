#!/usr/bin/env bash
# Launch the MYTHOS Lounge control panel and open it in a browser (WSL-friendly).
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${MYTHOS_PANEL_PORT:-8765}"
# use 127.0.0.1 (IPv4) explicitly: browsers resolve "localhost" to IPv6 ::1 first,
# which WSL2's localhost relay does not forward -> page "loads forever".
# the ?v=<epoch> cache-buster forces the browser to fetch a fresh index.html every
# launch, so an older cached build can never be served by mistake.
URL="http://127.0.0.1:${PORT}/?v=$(date +%s)"

# start the server in the background
python3 "$DIR/server.py" --port "$PORT" &
SRV=$!
trap 'kill $SRV 2>/dev/null || true' EXIT INT TERM

# wait for it to bind
for _ in $(seq 1 30); do
  if (exec 3<>"/dev/tcp/127.0.0.1/${PORT}") 2>/dev/null; then exec 3>&- 3<&-; break; fi
  sleep 0.2
done

echo "panel: $URL   (Ctrl-C to stop)"
# open a browser from WSL (first that works wins)
( command -v wslview  >/dev/null 2>&1 && wslview "$URL" ) 2>/dev/null \
 || ( command -v xdg-open >/dev/null 2>&1 && xdg-open "$URL" ) 2>/dev/null \
 || explorer.exe "$URL" 2>/dev/null \
 || powershell.exe -NoProfile -Command "Start-Process '$URL'" 2>/dev/null \
 || echo "open this in your browser: $URL"

wait $SRV
