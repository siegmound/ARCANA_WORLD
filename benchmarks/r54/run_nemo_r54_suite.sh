#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?R5.4 output root required}"
CONDA_EXE="${2:?absolute conda executable required}"
CONDA_ENV="${3:-arcana-nemo242}"
STREAM_RUNNER="${4:?stream runner path required}"
PARALLEL="${5:-6}"
if ! [[ "$PARALLEL" =~ ^[1-9][0-9]*$ ]]; then echo "invalid parallel worker count" >&2; exit 4; fi
if [[ ! -x "$CONDA_EXE" ]]; then echo "conda executable unavailable: $CONDA_EXE" >&2; exit 5; fi
if [[ ! -f "$STREAM_RUNNER" ]]; then echo "stream runner unavailable: $STREAM_RUNNER" >&2; exit 6; fi
mapfile -d '' CONFIGS < <(find "$ROOT/nemo_work" -name STREAM_CONFIG.json -print0 | sort -z)
if [[ ${#CONFIGS[@]} -eq 0 ]]; then echo "no R5.4 streams prepared" >&2; exit 7; fi
run_one(){
  local cfg="$1" wd seed variant status qcount
  wd="$(dirname "$cfg")"
  seed="${wd##*/seed_}"
  variant="$(basename "$(dirname "$wd")")"
  if [[ -f "$wd/engine.returncode.txt" && "$(tr -d '[:space:]' < "$wd/engine.returncode.txt")" == "0" && -f "$wd/STREAM_RUNTIME.json" ]]; then
    status="$(grep -o '"status"[[:space:]]*:[[:space:]]*"[^"]*"' "$wd/STREAM_RUNTIME.json" | head -1 | sed 's/.*:[[:space:]]*"//;s/"$//' || true)"
    qcount="$(find "$wd" -maxdepth 1 -name '*.qfreq' | wc -l | tr -d '[:space:]')"
    if [[ "$status" == "PASS_R54_NEMO_STREAM" && "$qcount" == "1" ]]; then echo "RESUME $wd"; return 0; fi
  fi
  echo "START $wd"
  set +e
  bash "$STREAM_RUNNER" "$wd" "$CONDA_EXE" "$CONDA_ENV" "$seed" "$variant"
  local rc=$?
  set -e
  echo "END rc=$rc $wd"
  return 0
}
export CONDA_EXE CONDA_ENV STREAM_RUNNER
export -f run_one
printf '%s\0' "${CONFIGS[@]}" | xargs -0 -n1 -P "$PARALLEL" bash -c 'run_one "$1"' _
failed=0
for cfg in "${CONFIGS[@]}"; do
  wd="$(dirname "$cfg")"
  [[ -f "$wd/engine.returncode.txt" ]] || { failed=$((failed+1)); continue; }
  [[ "$(tr -d '[:space:]' < "$wd/engine.returncode.txt")" == "0" ]] || failed=$((failed+1))
done
printf 'R5.4 NEMO streams: %d; failed: %d\n' "${#CONFIGS[@]}" "$failed"
[[ "$failed" -eq 0 ]]
