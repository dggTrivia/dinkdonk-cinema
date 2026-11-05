#!/usr/bin/env bash
# Runs the Dink Donk final render on a rented RunPod GPU and brings the pack home.
#
#   bash cloud-render.sh smoke   # quick end-to-end check: tiny render, a few cents
#   bash cloud-render.sh full    # the final render (out10)
#   bash cloud-render.sh fetch   # collect a finished run's result from its network volume (pod lost/stopped)
#
# Steps: create a 10 GB network volume in a data center that has a listed GPU free -> create the GPU pod there with
# the volume at /vol -> upload bundle/ -> run its run.sh -> show progress -> download the result into roxy3d/ ->
# DELETE the pod and the volume.
# Results survive anything that happens to this PC or the pod's network (run 4, 03 Nov 2026, lost a finished
# render: the pod became unreachable, the helper died with the Claude session, and the pod watchdog's stop wiped
# its container disk): the pod copies its results to the volume when the run ends and stops itself 20 min after
# a success. The helper never deletes a pod it cannot reach; once that pod has stopped it collects the results
# from the volume with a small CPU pod (same as `fetch`). The volume is deleted only after the result is home.
# A FAILED full run whose pod watchdog is armed keeps its pod for repair (ADOPT_POD=<id>, render cache intact);
# the watchdog stops it 3 h later. KEEP_ON_FAIL=0 deletes it anyway.
# Needs: tools/runpodctl/runpodctl.exe with an API key configured (owner did this), ~/.ssh/runpod_ed25519.
# Start it from a terminal of its own (not inside a Claude session), so it outlives the session.
set -euo pipefail

MODE="${1:-smoke}"
case "$MODE" in smoke|full|fetch) ;; *) echo "usage: $0 smoke|full|fetch" >&2; exit 2 ;; esac
HERE="$(cd "$(dirname "$0")" && pwd)"
ROXY="$(cd "$HERE/.." && pwd)"
RPC="$ROXY/../tools/runpodctl/runpodctl.exe"
KEY="$HOME/.ssh/runpod_ed25519"
ARCHIVE="${ARCHIVE:-$HERE/roxy-cloud-bundle.tar.gz}"   # Codex's packed bundle (contains bundle/)
OUTDIR="${OUTDIR:-$ROXY/out10.new}"   # full-mode unpack destination; relative paths use the caller's cwd
# first available wins (RunPod stock changes by the minute); override with GPUS="id1,id2"
GPUS="${GPUS:-NVIDIA GeForce RTX 5090,NVIDIA GeForce RTX 4090,NVIDIA L40S}"
CLOUD="${CLOUD:-SECURE}"   # community machines often lack a public ssh port
# small RunPod base image (sshd via the account key; Blender brings its own CUDA/OptiX runtime). The official
# templates get "no instances available" on current hosts, and the big PyTorch images take ages to pull.
IMAGE="${IMAGE:-runpod/base:0.7.0-ubuntu2004}"
BOOT_MIN="${BOOT_MIN:-20}"
LOST_MIN="${LOST_MIN:-20}"   # ssh down this long: stop polling the pod, wait for it to stop, then fetch
MAX_HOURS="${MAX_HOURS:-$([ "$MODE" = full ] && echo 6 || echo 0.75)}"   # fast pipeline: ~2-3.5 h
LOG="$HERE/cloud-$MODE-$(date +%Y%m%d-%H%M%S).log"
# Git Bash rewrites /vol-style args for native programs (it sent "C:/Program Files/Git/vol"); runpodctl needs them verbatim
rpc() { MSYS_NO_PATHCONV=1 "$RPC" "$@"; }
say() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }
js() { node -e "try{const j=JSON.parse(require('fs').readFileSync(0,'utf8'));console.log($1)}catch{console.log('')}"; }
[ -x "$RPC" ] || { echo "runpodctl not found at $RPC" >&2; exit 1; }
[ -f "$KEY" ] || { echo "ssh key $KEY missing" >&2; exit 1; }

# fetch works from the state file of the run it collects (FETCH_MODE=smoke for a smoke run)
RUN_MODE="$MODE"; [ "$MODE" = fetch ] && RUN_MODE="${FETCH_MODE:-full}"
STATE="$HERE/cloud-state-$RUN_MODE.json"
POD=""; VOL=""; DC=""; FETCH_POD=""
declare -A VOLS=()   # data center -> volume made while looking for a GPU (or "none")
KEEP_POD=""   # FAILED full run with an armed watchdog: kept for repair
LOST=""       # pod unreachable: never delete it, it may still be rendering
RESULT_HOME=""
save_state() { node -e "require('fs').writeFileSync(process.argv[1],JSON.stringify({pod:process.argv[2],volume:process.argv[3],dataCenter:process.argv[4],mode:process.argv[5],log:process.argv[6]},null,1))" "$STATE" "$POD" "$VOL" "$DC" "$RUN_MODE" "$LOG"; }

cleanup() {
  for d in "${!VOLS[@]}"; do   # volumes made while looking for a GPU that the run did not end up using
    [ "${VOLS[$d]}" != none ] && [ "${VOLS[$d]}" != "$VOL" ] && { rpc network-volume delete "${VOLS[$d]}" >>"$LOG" 2>&1 || say "!! could not delete volume ${VOLS[$d]} - delete it in the RunPod console"; }
  done
  [ -n "$FETCH_POD" ] && { say "deleting fetch pod $FETCH_POD"; rpc pod remove "$FETCH_POD" >>"$LOG" 2>&1 || say "!! could not delete fetch pod $FETCH_POD - delete it in the RunPod console"; }
  if [ -n "$KEEP_POD" ]; then
    say "pod $POD KEPT for repair (still billing). Its watchdog stops it 3 h after the failure."
    say "  repair: fix the bundle, then ADOPT_POD=$POD bash cloud-render.sh $RUN_MODE    give up: $RPC pod remove $POD"
  elif [ -n "$LOST" ]; then
    say "pod $POD left alone (unreachable; it stops itself). Collect later: bash cloud-render.sh fetch"
  elif [ -n "$POD" ] && [ "$MODE" != fetch -o -n "$RESULT_HOME" ]; then
    say "deleting pod $POD (billing stops)"
    rpc pod remove "$POD" >>"$LOG" 2>&1 || say "!! could not delete pod $POD - delete it in the RunPod console"
  fi
  if [ -n "$VOL" ]; then
    if [ -n "$RESULT_HOME" ] || [ "${VOL_EMPTY:-}" = 1 ]; then
      say "deleting network volume $VOL"; rpc network-volume delete "$VOL" >>"$LOG" 2>&1 || say "!! could not delete volume $VOL - delete it in the RunPod console"
      rm -f "$STATE"
    else
      say "network volume $VOL ($DC) KEPT - it holds this run's results/logs (~\$0.70/month). Collect: bash cloud-render.sh fetch"
    fi
  fi
}
trap cleanup EXIT
trap 'exit 130' INT TERM   # Ctrl-C: leave through the EXIT trap once (a bare INT trap would resume the script)

wait_ssh() {   # $1 pod id -> HOST PORT USERNAME, SSH and SCP arrays
  HOST=""; PORT=""; USERNAME="root"; local end=$(( $(date +%s) + BOOT_MIN * 60 )) j
  while [ -z "$HOST" ]; do
    if [ "$(date +%s)" -gt "$end" ]; then say "no ssh after ${BOOT_MIN} min - giving up"; return 1; fi
    sleep 15
    j="$(rpc pod get "$1" -o json 2>/dev/null || true)"
    read -r HOST PORT USERNAME < <(js 'j.ssh&&j.ssh.ip&&j.ssh.port?j.ssh.ip+" "+j.ssh.port+" "+(j.ssh.user||"root"):""' <<<"$j") || true
    [ -n "$HOST" ] || say "pod state: $(js '(j.runtimeStatus||j.desiredStatus||"?")+" "+(j.runtimeStatusReason||"")' <<<"$j")"
  done
  SSH=(ssh -i "$KEY" -p "$PORT" -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 -o ConnectTimeout=20 "$USERNAME@$HOST")
  SCP=(scp -i "$KEY" -P "$PORT" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20)
  say "ssh $USERNAME@$HOST:$PORT"
}

collect() {   # $1 = directory on the pod holding the results (the volume's results folder)
  local src="$1"
  "${SCP[@]}" "$USERNAME@$HOST:$src/progress.log" "$HERE/progress-$RUN_MODE.log" >>"$LOG" 2>&1 || true
  "${SCP[@]}" "$USERNAME@$HOST:$src/run.log" "$HERE/run-$RUN_MODE.log" >>"$LOG" 2>&1 || true
  local code; code="$("${SSH[@]}" "cat $src/EXIT 2>/dev/null" || true)"
  if [ "$code" != 0 ]; then say "run did not succeed (EXIT=${code:-missing}); logs in cloud/progress-$RUN_MODE.log and run-$RUN_MODE.log"; return 1; fi
  if [ "$RUN_MODE" = full ]; then
    "${SCP[@]}" "$USERNAME@$HOST:$src/out10.tar.gz" "$HERE/result-full.tar.gz" >>"$LOG" 2>&1
    local want got; want="$("${SSH[@]}" "cut -d' ' -f1 $src/out10.tar.gz.sha256")"; got="$(sha256sum "$HERE/result-full.tar.gz" | cut -d' ' -f1)"
    [ "$want" = "$got" ] || { say "!! downloaded archive checksum mismatch - volume kept"; return 1; }
    rm -rf "$OUTDIR"; mkdir -p "$OUTDIR" && tar -C "$OUTDIR" -xzf "$HERE/result-full.tar.gz"
    say "pack unpacked into $OUTDIR (Claude checks it, then promotes it)"
  else
    "${SCP[@]}" "$USERNAME@$HOST:$src/smoke.tar.gz" "$HERE/result-smoke.tar.gz" >>"$LOG" 2>&1
    rm -rf "$HERE/smoke-result"; mkdir -p "$HERE/smoke-result" && tar -C "$HERE/smoke-result" -xzf "$HERE/result-smoke.tar.gz"
    say "smoke result in roxy3d/cloud/smoke-result"
  fi
  RESULT_HOME=1
}

fetch_from_volume() {   # small CPU pod in the volume's data center reads /vol/results
  say "looking for a small pod in $DC to read volume $VOL"
  # 03 Nov smoke: a CPU pod with the volume sat at "awaiting_container" for 20+ min in EU-RO-1 (both base images),
  # while GPU pods boot in ~20 s - so try the cheapest GPUs in the volume's data center first, CPU last, and keep
  # retrying (the results are safe on the volume; only the pick-up waits for capacity).
  local end=$(( $(date +%s) + ${FETCH_WAIT_MIN:-360} * 60 )) j g
  local list="${FETCH_GPUS:-NVIDIA RTX 2000 Ada Generation,NVIDIA RTX A4000,NVIDIA RTX A4500,NVIDIA RTX 4000 Ada Generation,NVIDIA RTX A5000,NVIDIA GeForce RTX 3090,NVIDIA L4,NVIDIA RTX A6000,NVIDIA A40,NVIDIA GeForce RTX 4090,NVIDIA L40S,NVIDIA GeForce RTX 5090},CPU"
  while :; do
    while IFS= read -r g; do
      if [ "$g" = CPU ]; then
        j="$(rpc pod create --compute-type cpu --name dinkdonk-fetch --image runpod/base:0.6.2-cpu --ports "22/tcp" --data-center-ids "$DC" \
          --network-volume-id "$VOL" --volume-mount-path /vol --container-disk-in-gb 20 -o json 2>&1 || true)"
      else
        j="$(rpc pod create --name dinkdonk-fetch --image "$IMAGE" --gpu-id "$g" --cloud-type SECURE --ports "22/tcp" --data-center-ids "$DC" \
          --network-volume-id "$VOL" --volume-mount-path /vol --container-disk-in-gb 20 -o json 2>&1 || true)"
      fi
      echo "$j" >>"$LOG"; FETCH_POD="$(js 'j.id||""' <<<"$j")"
      [ -n "$FETCH_POD" ] || continue
      say "fetch pod $FETCH_POD ($g, $(js 'j.costPerHr+" $/h"' <<<"$j")) in $DC"
      if BOOT_MIN=10 wait_ssh "$FETCH_POD"; then collect /vol/results; return; fi
      rpc pod remove "$FETCH_POD" >>"$LOG" 2>&1; FETCH_POD=""
    done < <(tr ',' '\n' <<<"$list")
    [ "$(date +%s)" -lt "$end" ] || { say "!! nothing in $DC could read volume $VOL for ${FETCH_WAIT_MIN:-360} min - retry later: bash cloud-render.sh fetch"; return 1; }
    say "nothing free in $DC to read the volume - retrying in 2 min"; sleep 120
  done
}

if [ "$MODE" = fetch ]; then
  [ -f "$STATE" ] || { say "no $STATE - nothing to fetch"; exit 1; }
  read -r POD VOL DC < <(js 'j.pod+" "+j.volume+" "+j.dataCenter' <"$STATE")
  say "fetching $RUN_MODE run: pod $POD, volume $VOL in $DC"
  ST="$(rpc pod get "$POD" -o json 2>/dev/null | js 'j.runtimeStatus||j.desiredStatus||"gone"')" || true
  case "$ST" in
    running|RUNNING) say "pod $POD is still running - collecting from it directly"; wait_ssh "$POD" && collect /vol/results || true ;;
    *) { [ -z "$ST" ] || [ "$ST" = gone ]; } && POD="";   # already deleted: nothing to remove later
       fetch_from_volume || true ;;
  esac
  [ -n "$RESULT_HOME" ] || exit 1   # cleanup deletes the render pod and the volume only once the result is home
  say "done"; exit 0
fi

[ -f "$ARCHIVE" ] || { echo "bundle archive missing ($ARCHIVE)" >&2; exit 1; }
# RunPod creates a network volume only with >= $5 on the account; a full run (~2-3.5 h at <= $1.19/h) then
# spends ~$2.5-3.7 of it, and a pod that runs out of credit stops mid-render
MIN_BALANCE="${MIN_BALANCE:-$([ "$MODE" = full ] && echo 5.5 || echo 5.1)}"
BALANCE="$(rpc user -o json 2>/dev/null | js 'j.clientBalance??""')" || true
if [ -z "${ADOPT_POD:-}" ] && [ -n "$BALANCE" ] && node -e "process.exit(+'$BALANCE' < +'$MIN_BALANCE' ? 0 : 1)"; then
  say "RunPod balance \$$BALANCE is below \$$MIN_BALANCE needed for a $MODE run - top up first (MIN_BALANCE overrides)"; exit 1
fi

if [ -n "${ADOPT_POD:-}" ]; then
  POD="$ADOPT_POD"; [ -f "$STATE" ] && read -r VOL DC < <(js 'j.volume+" "+j.dataCenter' <"$STATE"); say "using existing pod $POD (volume ${VOL:-none})"
fi
# GPU + data center: a network volume ties the pod to one data center, so pick (DC, GPU) pairs RunPod lists as
# in stock, make the volume there, then the pod. Volumes that end up unused are deleted at once.
GPU_END=$(( $(date +%s) + ${WAIT_GPU_MIN:-30} * 60 ))   # stock comes and goes: keep trying for a while
SWEEP=0
while [ -z "$POD" ]; do
  # The stock list is sparse (03 Nov evening it listed none of the render GPUs anywhere), so every 5th round with
  # nothing listed also sweeps every data center for the first three GPUs; volumes made on the way are reused.
  PAIRS="$(rpc datacenter list -o json 2>/dev/null | SWEEP=$(( SWEEP % 5 == 0 )) node -e '
    const want=process.argv[1].split(",");let d=[];try{d=JSON.parse(require("fs").readFileSync(0,"utf8"))}catch{}
    const pin=process.env.PIN_DC;const out=[];
    for(const g of want)for(const c of d)if(!pin||c.id===pin)for(const a of c.gpuAvailability||[])if(a.gpuId===g&&a.stockStatus&&a.stockStatus!=="None")out.push(c.id+"|"+g);
    if(!out.length&&process.env.SWEEP==="1")for(const g of want.slice(0,3))for(const c of d)if(!pin||c.id===pin)out.push(c.id+"|"+g);
    console.log(out.join("\n"))' "$GPUS")" || true; SWEEP=$(( SWEEP + 1 ))
  while IFS='|' read -r TRY_DC GPU; do
    [ -n "$TRY_DC" ] || continue
    if [ -z "${VOLS[$TRY_DC]:-}" ]; then
      J="$(rpc network-volume create --name "dinkdonk-$MODE-$(date +%m%d%H%M)" --size 10 --data-center-id "$TRY_DC" -o json 2>&1 || true)"; echo "$J" >>"$LOG"
      VOLS[$TRY_DC]="$(js 'j.id||""' <<<"$J")"
      [ -n "${VOLS[$TRY_DC]}" ] || { say "  no network volume possible in $TRY_DC: $(echo "$J" | grep -o '"error":"[^"]*' | cut -c10-90)"; VOLS[$TRY_DC]=none; continue; }
      say "network volume ${VOLS[$TRY_DC]} created in $TRY_DC"
    fi
    [ "${VOLS[$TRY_DC]}" = none ] && continue
    say "creating pod: $GPU in $TRY_DC, $CLOUD cloud"
    J="$(rpc pod create --name "dinkdonk-$MODE" --image "$IMAGE" --ports "22/tcp" --gpu-id "$GPU" --cloud-type "$CLOUD" \
      --data-center-ids "$TRY_DC" --network-volume-id "${VOLS[$TRY_DC]}" --volume-mount-path /vol \
      --container-disk-in-gb 80 --env '{"NVIDIA_DRIVER_CAPABILITIES":"all"}' -o json 2>&1 || true)"; echo "$J" >>"$LOG"
    POD="$(js 'j.id||j.pod?.id||""' <<<"$J")"
    if [ -n "$POD" ]; then DC="$TRY_DC"; VOL="${VOLS[$TRY_DC]}"; break; fi
    say "  not available: $(echo "$J" | grep -o '"error":"[^"]*' | cut -c10-90)"
  done <<<"$PAIRS"
  [ -n "$POD" ] && break
  for d in "${!VOLS[@]}"; do [ "${VOLS[$d]}" != none ] && rpc network-volume delete "${VOLS[$d]}" >>"$LOG" 2>&1; done; VOLS=()
  if [ "$(date +%s)" -gt "$GPU_END" ]; then say "no listed GPU became available in ${WAIT_GPU_MIN:-30} min - try again later"; exit 1; fi
  say "none free right now - retrying in 60 s"; sleep 60
done
for d in "${!VOLS[@]}"; do [ "$d" != "$DC" ] && [ "${VOLS[$d]}" != none ] && rpc network-volume delete "${VOLS[$d]}" >>"$LOG" 2>&1; done
VOLS=(["$DC"]="$VOL")
VOL_EMPTY=1; save_state
say "pod $POD created in $DC (volume $VOL at /vol) - waiting for ssh (max ${BOOT_MIN} min)"
wait_ssh "$POD" || exit 1

say "uploading bundle ($(du -sh "$ARCHIVE" | cut -f1))"
"${SCP[@]}" "$ARCHIVE" "$USERNAME@$HOST:/workspace/bundle.tar.gz" >>"$LOG" 2>&1
# the slim base image lacks the GL/EGL loader libs Blender's compositor/image code needs (NVIDIA provides the driver side)
say "installing system libraries for Blender"
"${SSH[@]}" "export DEBIAN_FRONTEND=noninteractive; (apt-get update -qq && apt-get install -y -qq libegl1 libgl1 libglvnd0 libgles2 libxkbcommon0 libsm6 libice6 libxi6 libxrender1 libxxf86vm1 libxfixes3 libxext6 libx11-6 zstd >/dev/null) 2>&1 | tail -n 3" | tee -a "$LOG"
# ssh sessions lack the pod's RUNPOD_* env, which run.sh needs to arm its watchdog; take it from PID 1.
# Results go to the network volume (/vol/results) the moment the run ends; a successful pod stops itself 20 min
# later (the helper normally deletes it first), a failed one is left to its watchdog's 3 h repair window.
"${SSH[@]}" "cat > /workspace/launch.sh" <<'EOF'
while IFS= read -r kv; do export "$kv"; done < <(tr '\0' '\n' < /proc/1/environ | grep -E '^RUNPOD_(POD_ID|API_KEY)=')
R=/vol/results; mkdir -p $R; rm -f $R/EXIT
cd /workspace/bundle && rm -f EXIT
( while :; do cp -f progress.log $R/ 2>/dev/null; sleep 300; done ) & SYNC=$!
bash run.sh "$1" > run.log 2>&1; CODE=$?
kill $SYNC 2>/dev/null
cp -f progress.log run.log $R/ 2>/dev/null
if [ "$1" = full ] && [ -f out10.tar.gz ]; then
  cp out10.tar.gz $R/out10.tar.gz.partial && mv $R/out10.tar.gz.partial $R/out10.tar.gz && (cd $R && sha256sum out10.tar.gz > out10.tar.gz.sha256)
fi
[ "$1" = smoke ] && tar -czf $R/smoke.tar.gz smoke progress.log run.log
sync; echo $CODE > $R/EXIT; echo $CODE > EXIT
if [ $CODE = 0 ]; then sleep 1200; runpodctl pod stop "$RUNPOD_POD_ID" >/dev/null 2>&1 || true; fi
EOF
# ADOPT_POD repair: the bundle is replaced by the fixed one; work/ (render cache) is kept, and the old out10
# is moved aside because changed scripts change its build fingerprint (the pipeline refuses a foreign out10)
ASIDE=""; [ -n "${ADOPT_POD:-}" ] && ASIDE="[ ! -d bundle/out10 ] || mv bundle/out10 bundle/out10.prev-\$(date +%s);"
"${SSH[@]}" "cd /workspace && $ASIDE tar -xzf bundle.tar.gz && (nohup bash /workspace/launch.sh $MODE >/dev/null 2>&1 &) && echo started" | tee -a "$LOG"
VOL_EMPTY=""

DEADLINE=$(( $(date +%s) + $(node -e "console.log(Math.round($MAX_HOURS*3600))") ))
LAST_OK=$(date +%s)
while :; do
  sleep 60
  OUT="$("${SSH[@]}" 'cd /workspace/bundle; tail -n 1 progress.log 2>/dev/null | cut -c1-200; [ -f /vol/results/EXIT ] && echo "__END__ $(cat /vol/results/EXIT)"; true' 2>>"$LOG")" && LAST_OK=$(date +%s) || OUT=""
  [ -n "$OUT" ] && say "$(echo "$OUT" | grep -v '^__' | tail -n 1)"
  case "$OUT" in
    *"__END__ 0"*) break ;;
    *__END__*)
      say "render FAILED - log follows"; "${SSH[@]}" "tail -n 60 /workspace/bundle/run.log" | tee -a "$LOG" || true
      collect /vol/results || true
      if [ "$MODE" = full ] && [ "${KEEP_ON_FAIL:-1}" = 1 ] && "${SSH[@]}" 'pgrep -f bundle/watchdog.sh' >/dev/null 2>&1; then KEEP_POD=1; fi
      exit 1 ;;
  esac
  if [ -z "$OUT" ] && [ $(( $(date +%s) - LAST_OK )) -gt $(( LOST_MIN * 60 )) ]; then
    # Unreachable: it may still be rendering. Never delete it; wait until it stops (itself after a success,
    # or its watchdog), then read the results from the volume.
    LOST=1; say "pod unreachable for ${LOST_MIN} min - waiting for it to stop, then collecting from volume $VOL"
    while :; do
      ST="$(rpc pod get "$POD" -o json 2>/dev/null | js 'j.runtimeStatus||j.desiredStatus||"?"')" || true
      case "$ST" in running|RUNNING|"?"|"") sleep 300 ;; *) break ;; esac   # "" = API hiccup: keep waiting
    done
    say "pod $POD is $ST"; LOST=""
    fetch_from_volume || exit 1
    exit 0
  fi
  if [ "$(date +%s)" -gt "$DEADLINE" ]; then
    if [ -n "$OUT" ]; then say "time limit ${MAX_HOURS} h reached - stopping"; collect /vol/results || true; exit 1; fi
    LOST=1; say "time limit reached while the pod is unreachable - leaving it to its watchdog"; exit 1
  fi
done

if [ "${TEST_FETCH:-}" = 1 ]; then   # exercises the lost-pod path: GPU pod gone, result read via a CPU pod
  say "TEST_FETCH: deleting the GPU pod, collecting from volume $VOL instead"; rpc pod remove "$POD" >>"$LOG" 2>&1; POD=""
  fetch_from_volume || exit 1; say "done"; exit 0
fi
say "downloading the result"
collect /vol/results || exit 1
say "done"
