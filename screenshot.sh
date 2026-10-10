#!/usr/bin/env bash
# Desktop + phone screenshots from offline snapshot + live server on :4279.
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-4279}"
CHROME="$(command -v google-chrome || command -v chromium || command -v chromium-browser)"
mkdir -p screenshots dist
shot() {
  local url="$1" out="$2" size="$3"; shift 3 || true
  local prof; prof="$(mktemp -d /tmp/terpsshot.XXXX)"
  "$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --run-all-compositor-stages-before-draw --virtual-time-budget=12000 \
    --window-size="$size" --user-data-dir="$prof" --screenshot="$out" "$@" "$url" >/dev/null 2>&1
  rm -rf "$prof"; echo "  $out ($(wc -c < "$out") bytes)"
}
SNAP="file://$PWD/dist/terps-football-snapshot.html"
U="http://127.0.0.1:$PORT"
shot "$SNAP" screenshots/00-best-home.png 1440,1100
shot "$SNAP" screenshots/overview.png 1440,1600
shot "$SNAP" screenshots/full.png 1440,4200
shot "$SNAP" screenshots/mobile.png 430,9000
if curl -sf "$U/healthz" >/dev/null 2>&1; then
  shot "$U/" screenshots/live.png 1440,1400
fi
# keep a legacy hero alias for older links
cp -f screenshots/00-best-home.png screenshots/00-best-desktop-hero.png
echo "screenshots done"
