#!/usr/bin/env bash
# Runs playtest sessions spread over one or two editor instances in parallel.
# Usage: scripts/bench.sh <level> <list file> <provider>...
#   e.g. scripts/bench.sh vault runs/vault_b5.txt meta baseten meta baseten
# Each finished session appends "<provider> runs/<dir>/" to the list file, ready for
# scripts/summarize_runs.py. Session i goes to instance i % N. Instance 2 is the copy at
# PT_SECOND_PROJECT (Remote Control on port 30011); set PT_INSTANCES=1 to use only the first.
# PT_SESSION_ARGS is passed to every session, e.g. PT_SESSION_ARGS=--no-video.
set -uo pipefail
level=$1 list=$2; shift 2
repo=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
second=${PT_SECOND_PROJECT:-/mnt/c/UnrealProjects/PlaytestArena2}
instances=${PT_INSTANCES:-2}
: >> "$repo/$list"

worker() {  # $1 = instance index, then the providers it runs, one after another
  local idx=$1; shift
  local env=()
  if [ "$idx" = 1 ]; then
    env=(UE_RC_URL=http://127.0.0.1:30011
         UE_SCREENSHOT_DIR="$second/Saved/Screenshots/WindowsEditor")
  fi
  for provider in "$@"; do
    out=$(cd "$repo" && env "${env[@]}" python3 agent/session.py --provider "$provider" \
          --level "$level" ${PT_SESSION_ARGS:-} 2>&1 | tail -2)
    report=$(echo "$out" | head -1)
    if [[ "$report" == */report.md ]]; then
      echo "$provider runs/$(basename "$(dirname "$report")")/" >> "$repo/$list"
      echo "[instance $((idx + 1))] $provider: $(echo "$out" | tail -1)"
    else
      echo "[instance $((idx + 1))] $provider FAILED: $out"
    fi
  done
}

jobs=("$@")
for ((w = 0; w < instances; w++)); do
  mine=()
  for ((i = w; i < ${#jobs[@]}; i += instances)); do mine+=("${jobs[$i]}"); done
  [ ${#mine[@]} -gt 0 ] && worker "$w" "${mine[@]}" &
done
wait
