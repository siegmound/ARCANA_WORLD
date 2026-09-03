#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?suite directory required}"
CONDA_ENV="${2:-arcana-nemo242}"
PARALLEL_JOBS="${3:-6}"
if ! [[ "$PARALLEL_JOBS" =~ ^[1-9][0-9]*$ ]]; then echo "ERROR: parallel jobs must be positive integer" >&2; exit 4; fi
if ! command -v conda >/dev/null 2>&1; then echo "ERROR: conda not found inside WSL" >&2; exit 2; fi
if ! conda run -n "$CONDA_ENV" bash -lc 'command -v nemo2.4.2 >/dev/null' >/dev/null 2>&1; then echo "ERROR: nemo2.4.2 not found in conda env $CONDA_ENV" >&2; exit 3; fi

mapfile -d '' INIS < <(find "$ROOT" -name Nemo2_ARCANA_R36D.ini -print0 | sort -z)
count=${#INIS[@]}
if [[ $count -eq 0 ]]; then echo "ERROR: no R3.6D NEMO jobs found under $ROOT" >&2; exit 5; fi
printf '[R3.6D] NEMO jobs: %d; parallel workers: %d\n' "$count" "$PARALLEL_JOBS"

run_one() {
  local ini="$1"; local d; d="$(dirname "$ini")"
  printf '[R3.6D] START %s\n' "$d"
  set +e
  (cd "$d" && OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
     conda run -n "$CONDA_ENV" nemo2.4.2 "$(basename "$ini")" >engine.stdout.txt 2>engine.stderr.txt)
  local rc=$?
  set -e
  printf '%s\n' "$rc" > "$d/engine.returncode.txt"
  printf '[R3.6D] END rc=%d %s\n' "$rc" "$d"
  return 0
}
export CONDA_ENV
export -f run_one
printf '%s\0' "${INIS[@]}" | xargs -0 -n1 -P "$PARALLEL_JOBS" bash -c 'run_one "$1"' _

failed=0
while IFS= read -r -d '' rcfile; do
  rc="$(tr -d '[:space:]' < "$rcfile")"
  if [[ "$rc" != "0" ]]; then failed=$((failed+1)); fi
done < <(find "$ROOT" -name engine.returncode.txt -print0)
printf 'R3.6D NEMO jobs: %d; failed: %d\n' "$count" "$failed"
[[ $failed -eq 0 ]]
