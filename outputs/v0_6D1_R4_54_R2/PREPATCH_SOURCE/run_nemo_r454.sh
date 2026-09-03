#!/usr/bin/env bash
set -euo pipefail
ini_src="$1"; work="$2"; out_json="$3"; seed="$4"; job_id="$5"; collector="$6"
rm -rf "$work"; mkdir -p "$work"
python - "$ini_src" "$work/Nemo2_R454.ini" "$seed" <<'PY'
from pathlib import Path
import re,sys
src=Path(sys.argv[1]).read_text()
seed=int(sys.argv[3])
src=re.sub(r'(?m)^random_seed\s+\d+\s*$',f'random_seed             {seed}',src)
src=re.sub(r'(?m)^logfile\s+.*$',r'logfile                 r454_nemo.log',src)
src=re.sub(r'(?m)^filename\s+.*$',r'filename                r454_nemo',src)
src=re.sub(r'(?m)^stat_log_time\s+\d+\s*$',r'stat_log_time           10',src)
src=re.sub(r'(?m)^quanti_freq_logtime\s+\d+\s*$',r'quanti_freq_logtime     10',src)
Path(sys.argv[2]).write_text(src)
PY
cd "$work"
set +e
nemo2.4.2 Nemo2_R454.ini >engine.stdout.txt 2>engine.stderr.txt
rc=$?
set -e
if [ "$rc" -ne 0 ]; then
  printf '{"stage":"v0.6D1-R4.54","engine":"NEMO","probe_job_id":"%s","frozen_seed":%s,"seed_injection_mode":"NEMO_RANDOM_SEED_INI_PARAMETER","seed_binding_verified":false,"dry_run":true,"scientific_evidence":false,"status":"FAIL","returncode":%s,"metrics":[],"unauthorized_metric_count":0,"numeric_acceptance_threshold_count":0,"automatic_scientific_pass_fail_count":0,"canonical_state_changed":false,"error":"NEMO execution failed"}\n' "$job_id" "$seed" "$rc" > "$out_json"
  exit "$rc"
fi
qfreq="$(find . -maxdepth 1 -type f -name 'r454_nemo*.qfreq' | head -n 1)"
if [ -z "$qfreq" ] || [ ! -s "$qfreq" ]; then exit 20; fi
python "$collector" "$out_json" "$work/Nemo2_R454.ini" "$qfreq" "$seed" "$job_id"
