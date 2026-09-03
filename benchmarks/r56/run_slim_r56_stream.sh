#!/usr/bin/env bash
set -euo pipefail
WD="${1:?work directory required}"
CONDA_EXE="${2:?conda executable required}"
CONDA_ENV="${3:?conda env required}"
SEED="${4:?seed required}"
VARIANT="${5:?variant required}"
COLLECTOR="${6:?collector path required}"
if [[ ! -d "$WD" || ! -f "$WD/ARCANA_R56.slim" || ! -f "$WD/STREAM_CONFIG.json" ]]; then
  echo "R5.6 stream input missing: $WD" >&2; exit 4
fi
if [[ ! -x "$CONDA_EXE" ]]; then echo "R5.6 Conda executable unavailable: $CONDA_EXE" >&2; exit 5; fi
if [[ ! -f "$COLLECTOR" ]]; then echo "R5.6 ancestry collector unavailable: $COLLECTOR" >&2; exit 6; fi
cd "$WD"
rm -f r56.trees ANCESTRY_RESULT.json engine.stdout.txt engine.stderr.txt collector.stdout.txt collector.stderr.txt engine.returncode.txt collector.returncode.txt STREAM_RUNTIME.json
set +e
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  "$CONDA_EXE" run -n "$CONDA_ENV" slim -s "$SEED" ARCANA_R56.slim >engine.stdout.txt 2>engine.stderr.txt
rc=$?
set -e
printf '%s\n' "$rc" > engine.returncode.txt
crc=99
if [[ "$rc" -eq 0 && -f r56.trees ]]; then
  set +e
  PYTHONPATH="${PYTHONPATH:-}" "$CONDA_EXE" run -n "$CONDA_ENV" python "$COLLECTOR" --trees r56.trees --config STREAM_CONFIG.json --stdout engine.stdout.txt --output ANCESTRY_RESULT.json >collector.stdout.txt 2>collector.stderr.txt
  crc=$?
  set -e
fi
printf '%s\n' "$crc" > collector.returncode.txt
status="FAILED_R56_SLIM_STREAM"
tree_sha=""; result_sha=""
if [[ "$rc" -eq 0 && "$crc" -eq 0 && -f r56.trees && -f ANCESTRY_RESULT.json ]]; then
  status="PASS_R56_SLIM_STREAM"
  tree_sha="$(sha256sum r56.trees | awk '{print $1}')"
  result_sha="$(sha256sum ANCESTRY_RESULT.json | awk '{print $1}')"
fi
script_sha="$(sha256sum ARCANA_R56.slim | awk '{print $1}')"
cfg_sha="$(sha256sum STREAM_CONFIG.json | awk '{print $1}')"
cat > STREAM_RUNTIME.json <<EOF
{
  "stage": "v0.6D1-R5.6",
  "status": "$status",
  "slim_version": "5.2",
  "conda_env_name": "$CONDA_ENV",
  "seed": $SEED,
  "variant": "$VARIANT",
  "returncode": $rc,
  "collector_returncode": $crc,
  "slim_script_sha256": "$script_sha",
  "stream_config_sha256": "$cfg_sha",
  "tree_sha256": $(if [[ -n "$tree_sha" ]]; then printf '"%s"' "$tree_sha"; else printf 'null'; fi),
  "ancestry_result_sha256": $(if [[ -n "$result_sha" ]]; then printf '"%s"' "$result_sha"; else printf 'null'; fi)
}
EOF
if [[ "$status" != "PASS_R56_SLIM_STREAM" ]]; then
  echo "R5.6 stream failed: slim_rc=$rc collector_rc=$crc $WD" >&2
  if [[ -f engine.stderr.txt ]]; then tail -80 engine.stderr.txt >&2 || true; fi
  if [[ -f collector.stderr.txt ]]; then tail -80 collector.stderr.txt >&2 || true; fi
  exit 7
fi
