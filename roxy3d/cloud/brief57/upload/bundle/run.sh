#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
MODE="${1:-full}"
case "$MODE" in full|smoke|preflight|validate-only) ;; *) echo 'Usage: bash run.sh [full|smoke|preflight|validate-only]' >&2; exit 2;; esac
# A kernel lock is released even on a crash; a second run cannot reset the
# active watchdog or write into the first run's buffers.
mkdir -p work/watchdog
command -v flock >/dev/null || { touch FAILED; echo 'Missing prerequisite: flock' >&2; exit 1; }
exec 9>work/run.lock
flock -n 9 || { echo 'Another pipeline owns this bundle folder.' >&2; exit 1; }
START="$(date +%s)"; RUN_ID="$START-$$"; STATE="$ROOT/work/watchdog/$RUN_ID"
mkdir -p "work/watchdog/$RUN_ID"; printf '%s\n' "$START" > "$STATE/start"
printf '%s\n' "$RUN_ID" > work/watchdog/current.partial; mv work/watchdog/current.partial work/watchdog/current
rm -f -- DONE FAILED
finish() {
  rc=$?; trap - EXIT ERR INT TERM; set +e
  if [[ -f FAILED && "$rc" == 0 ]]; then rc=124; fi
  if [[ "$rc" == 0 ]]; then touch DONE; else touch FAILED; fi
  printf '%s\n' "$(date +%s)" > "$STATE/end.partial"; mv "$STATE/end.partial" "$STATE/end"
  printf 'mode=%s exit=%s\n' "$MODE" "$rc" > "$STATE/result"
  printf '%s END mode=%s exit=%s marker=%s\n' "$(date -u +%FT%TZ)" "$MODE" "$rc" "$(if [[ "$rc" == 0 ]]; then echo DONE; else echo FAILED; fi)" | tee -a progress.log
  exit "$rc"
}
trap finish EXIT
trap 'rc=$?; printf "%s ERROR exit=%s line=%s mode=%s\n" "$(date -u +%FT%TZ)" "$rc" "$LINENO" "$MODE" | tee -a "$ROOT/progress.log" >&2' ERR
trap 'exit 130' INT
trap 'exit 143' TERM
if [[ -n "${RUNPOD_POD_ID:-}" ]] && command -v runpodctl >/dev/null; then
  for command in nohup setsid timeout; do command -v "$command" >/dev/null || { echo "Missing watchdog prerequisite: $command" >&2; exit 1; }; done
  # Close the inherited run lock, detach the session and redirect every FD.
  (exec 9>&-; exec nohup setsid bash "$ROOT/watchdog.sh" "$ROOT" "$STATE" "$RUNPOD_POD_ID" "$(command -v runpodctl)" "$$") </dev/null >"$STATE/watchdog.log" 2>&1 &
  printf '%s\n' "$!" > "$STATE/watchdog.pid"
  printf '%s WATCHDOG detached; 3h after end / 8h after start\n' "$(date -u +%FT%TZ)" | tee -a progress.log
else
  printf '%s WATCHDOG disabled: requires pod-local runpodctl and RUNPOD_POD_ID\n' "$(date -u +%FT%TZ)" | tee -a progress.log
fi
for command in curl sha256sum tar xz nvidia-smi; do command -v "$command" >/dev/null || { echo "Missing prerequisite: $command" >&2; exit 1; }; done
[[ "$(uname -m)" == x86_64 ]] || { echo 'Linux x86_64 is required.' >&2; exit 1; }
[[ "$(uname -s)" == Linux ]] || { echo 'This launcher is for Linux. See README for the local Blender command.' >&2; exit 1; }
sha256sum --check --quiet BUNDLE-SHA256SUMS
mkdir -p .runtime work/cache/temp work/cache/cuda work/cache/optix work/blender-user
export TMPDIR="$ROOT/work/cache/temp" TEMP="$ROOT/work/cache/temp" TMP="$ROOT/work/cache/temp"
export XDG_CACHE_HOME="$ROOT/work/cache" CUDA_CACHE_PATH="$ROOT/work/cache/cuda" OPTIX_CACHE_PATH="$ROOT/work/cache/optix"
export BLENDER_USER_RESOURCES="$ROOT/work/blender-user" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
VERSION=5.2.3
ARCHIVE="blender-${VERSION}-linux-x64.tar.xz"
EXPECTED=78486c018b4443efe5e75ab54c290ed8c15abafd249b862c2c9ce2530a918eec
BASE="https://download.blender.org/release/Blender5.2"
BLENDER="$ROOT/.runtime/blender-${VERSION}-linux-x64/blender"
printf '%s START mode=%s\n' "$(date -u +%FT%TZ)" "$MODE" | tee -a progress.log
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv | tee -a progress.log
if [[ ! -x "$BLENDER" ]]; then
  curl --fail --location --retry 3 "$BASE/blender-${VERSION}.sha256" --output .runtime/official.sha256.partial
  OBSERVED="$(awk -v file="$ARCHIVE" '$2 == file {print $1}' .runtime/official.sha256.partial)"
  [[ "$OBSERVED" == "$EXPECTED" ]] || { echo 'Official SHA-256 does not match the pinned release checksum.' >&2; exit 1; }
  mv .runtime/official.sha256.partial .runtime/official.sha256
  if [[ ! -f ".runtime/$ARCHIVE" ]]; then
    curl --fail --location --retry 3 "$BASE/$ARCHIVE" --output ".runtime/$ARCHIVE.partial"
    printf '%s  %s\n' "$EXPECTED" ".runtime/$ARCHIVE.partial" | sha256sum --check -
    mv ".runtime/$ARCHIVE.partial" ".runtime/$ARCHIVE"
  fi
  printf '%s  %s\n' "$EXPECTED" ".runtime/$ARCHIVE" | sha256sum --check -
  tar --extract --xz --file ".runtime/$ARCHIVE" --directory .runtime
fi
"$BLENDER" --version | sed -n '1,3p' | tee -a progress.log
"$BLENDER" -b --python-exit-code 1 --python "$ROOT/pipeline.py" -- "$MODE" 2>&1 | tee -a progress.log
if [[ "$MODE" == full ]]; then
  test -s out10.tar.gz
  printf '%s SUCCESS mode=%s archive=out10.tar.gz\n' "$(date -u +%FT%TZ)" "$MODE" | tee -a progress.log
else
  printf '%s SUCCESS mode=%s\n' "$(date -u +%FT%TZ)" "$MODE" | tee -a progress.log
fi
