#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?R5.6 output root required}"
CONDA_EXE="${2:?absolute conda executable required}"
CONDA_ENV="${3:-arcana-slim52}"
STREAM_RUNNER="${4:?stream runner path required}"
COLLECTOR="${5:?collector path required}"
PARALLEL="${6:-4}"
if ! [[ "$PARALLEL" =~ ^[1-9][0-9]*$ ]]; then echo "invalid parallel worker count" >&2; exit 4; fi
mapfile -d '' CONFIGS < <(find "$ROOT/slim_work" -name STREAM_CONFIG.json -print0 | sort -z)
if [[ ${#CONFIGS[@]} -eq 0 ]]; then echo "no R5.6 streams prepared" >&2; exit 5; fi
run_one(){
  local cfg="$1" wd seed variant status
  wd="$(dirname "$cfg")"; seed="${wd##*/seed_}"; variant="$(basename "$(dirname "$wd")")"
  if [[ -f "$wd/STREAM_RUNTIME.json" && -f "$wd/r56.trees" && -f "$wd/ANCESTRY_RESULT.json" ]]; then
    status="$(grep -o '"status"[[:space:]]*:[[:space:]]*"[^"]*"' "$wd/STREAM_RUNTIME.json" | head -1 | sed 's/.*:[[:space:]]*"//;s/"$//' || true)"
    if [[ "$status" == "PASS_R56_SLIM_STREAM" ]]; then echo "RESUME $wd"; return 0; fi
  fi
  echo "START $wd"
  set +e
  bash "$STREAM_RUNNER" "$wd" "$CONDA_EXE" "$CONDA_ENV" "$seed" "$variant" "$COLLECTOR"
  local rc=$?
  set -e
  echo "END rc=$rc $wd"
  return 0
}
export CONDA_EXE CONDA_ENV STREAM_RUNNER COLLECTOR
export -f run_one
printf '%s\0' "${CONFIGS[@]}" | xargs -0 -n1 -P "$PARALLEL" bash -c 'run_one "$1"' _
failed=0
for cfg in "${CONFIGS[@]}"; do
  wd="$(dirname "$cfg")"
  [[ -f "$wd/STREAM_RUNTIME.json" ]] || { failed=$((failed+1)); continue; }
  status="$(grep -o '"status"[[:space:]]*:[[:space:]]*"[^"]*"' "$wd/STREAM_RUNTIME.json" | head -1 | sed 's/.*:[[:space:]]*"//;s/"$//' || true)"
  [[ "$status" == "PASS_R56_SLIM_STREAM" ]] || failed=$((failed+1))
done
printf 'R5.6 SLiM streams: %d; failed: %d\n' "${#CONFIGS[@]}" "$failed"
[[ "$failed" -eq 0 ]]
