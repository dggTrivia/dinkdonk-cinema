#!/usr/bin/env bash
# Pod-local, detached lifetime cap. This script never deletes a pod or volume.
set -u
ROOT="$1"; STATE="$2"; POD="$3"; CTL="$4"; PARENT_PID="$5"
START="$(cat "$STATE/start")"
RUN_ID="$(basename "$STATE")"
export RUNPOD_NO_UPDATE_CHECK=1
log() { printf '%s WATCHDOG %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$ROOT/progress.log"; }
current() { [[ -f "$ROOT/work/watchdog/current" ]] && [[ "$(cat "$ROOT/work/watchdog/current")" == "$RUN_ID" ]]; }
log "armed pod=$POD start=$START hard_cap_seconds=28800 grace_seconds=10800"
while current; do
  NOW="$(date +%s)"; DEADLINE=$((START + 28800)); REASON=hard-cap
  if [[ ! -f "$STATE/end" ]] && ! kill -0 "$PARENT_PID" 2>/dev/null; then
    # Also handle an untrappable SIGKILL / crashed launcher.
    printf '%s\n' "$NOW" > "$STATE/end.partial"; mv "$STATE/end.partial" "$STATE/end"
    touch "$ROOT/FAILED"; log 'launcher disappeared; recording failure'
  fi
  if [[ -f "$STATE/end" ]]; then
    FINISHED="$(cat "$STATE/end")"; GRACE=$((FINISHED + 10800))
    if (( GRACE < DEADLINE )); then DEADLINE="$GRACE"; REASON=post-run-grace; fi
  fi
  if (( NOW >= DEADLINE )); then
    current || break
    if [[ ! -f "$STATE/end" ]]; then
      touch "$ROOT/FAILED"; printf '%s\n' "$NOW" > "$STATE/end"
      printf '%s\n' 'watchdog hard cap reached before pipeline completion' > "$STATE/result"
    fi
    log "deadline reached reason=$REASON; requesting pod stop"
    # Current CLI first; compatibility with older pod images second.
    # Bound a hung CLI call, then retry transient API errors once per minute.
    if timeout 30 "$CTL" pod stop "$POD" || timeout 30 "$CTL" stop pod "$POD"; then
      log 'pod stop request accepted'; exit 0
    fi
    log 'pod stop request failed; retrying in 60 seconds'
    sleep 60
  else
    REMAIN=$((DEADLINE - NOW)); (( REMAIN > 15 )) && REMAIN=15
    sleep "$REMAIN"
  fi
done
log 'superseded by a newer run; exiting without stopping pod'
