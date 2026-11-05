#!/usr/bin/env bash
# Every 5 minutes: a screenshot of roxy.html (fake chat) into roxy3d/progress/, plus a copy of
# Codex's newest full render from out2/ whenever it changed. A morning timeline of the night's work.
cd "$(dirname "$0")" || exit 1
mkdir -p progress
CHROME="/c/Program Files/Google/Chrome/Application/chrome.exe"
PROF="$(cygpath -m "$PWD")/cache/prof-progress"
last=""
while true; do
  ts=$(date +%m%d-%H%M)
  "$CHROME" --headless=new --hide-scrollbars --user-data-dir="$PROF" --window-size=1920,1080 \
    --virtual-time-budget=30000 --screenshot="$(cygpath -m "$PWD")/progress/$ts-page.png" \
    "http://127.0.0.1:18770/roxy.html?demo=1" >/dev/null 2>&1
  for f in out2/full.png out2/base.png; do
    if [ -f "$f" ]; then
      sum=$(md5sum "$f" | cut -c1-12)
      if [ "$sum" != "$last" ]; then cp "$f" "progress/$ts-codex-$(basename "$f")"; last="$sum"; fi
      break
    fi
  done
  sleep 300
done
