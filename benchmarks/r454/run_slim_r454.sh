#!/usr/bin/env bash
set -euo pipefail
slim_file="$1"; collector="$2"; work="$3"; out_json="$4"; seed="$5"; job_id="$6"
rm -rf "$work"; mkdir -p "$work"
cp "$slim_file" "$work/R454_two_pop_gene_flow.slim"
cd "$work"
set +e
slim -s "$seed" R454_two_pop_gene_flow.slim >engine.stdout.txt 2>engine.stderr.txt
rc=$?
set -e
if [ "$rc" -ne 0 ]; then exit "$rc"; fi
python "$collector" "$out_json" "$work/r454_slim.trees" "$work/engine.stdout.txt" "$seed" "$job_id"
