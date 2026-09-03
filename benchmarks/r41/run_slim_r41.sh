#!/usr/bin/env bash
set -euo pipefail
slim_file="$1"; collect_py="$2"; work="$3"; out_json="$4"
mkdir -p "$work"; rm -f "$work/r41_slim.trees" "$work/engine.stdout.txt" "$work/engine.stderr.txt" "$out_json"
cp "$slim_file" "$work/R41_two_pop_gene_flow.slim"
cd "$work"
set +e
slim -s 4101006 R41_two_pop_gene_flow.slim >engine.stdout.txt 2>engine.stderr.txt
rc=$?
set -e
if [ "$rc" -ne 0 ]; then
  printf '{"status":"FAIL","returncode":%s,"metrics":{},"error":"SLiM execution failed"}\n' "$rc" > "$out_json"
  exit "$rc"
fi
python "$collect_py" "$out_json" "$work/r41_slim.trees" "$work/engine.stdout.txt"
