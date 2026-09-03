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
  python - "$out_json" "$seed" "$job_id" "$rc" <<'PY'
from pathlib import Path
import json,sys
out=Path(sys.argv[1]); seed=int(sys.argv[2]); job_id=sys.argv[3]; rc=int(sys.argv[4])
stderr=Path("engine.stderr.txt").read_text(errors="replace")[-8000:] if Path("engine.stderr.txt").exists() else ""
stdout=Path("engine.stdout.txt").read_text(errors="replace")[-8000:] if Path("engine.stdout.txt").exists() else ""
result={
 "stage":"v0.6D1-R4.54","engine":"NEMO","probe_job_id":job_id,
 "frozen_seed":seed,"seed_injection_mode":"NEMO_RANDOM_SEED_INI_PARAMETER",
 "seed_binding_verified":False,"dry_run":True,"scientific_evidence":False,
 "status":"FAIL","returncode":rc,"metrics":[],
 "unauthorized_metric_count":0,"numeric_acceptance_threshold_count":0,
 "automatic_scientific_pass_fail_count":0,"artifact_hashes":{},
 "canonical_state_changed":False,"error":"NEMO execution failed",
 "engine_stdout_tail":stdout,"engine_stderr_tail":stderr,
}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
PY
  exit "$rc"
fi

qfreq=""
if [ -s "r454_nemo_1.qfreq" ]; then
  qfreq="r454_nemo_1.qfreq"
else
  qfreq="$(find . -maxdepth 1 -type f -name '*.qfreq' -size +0c | sort | head -n 1 || true)"
fi
if [ -z "$qfreq" ] || [ ! -s "$qfreq" ]; then
  python - "$out_json" "$seed" "$job_id" <<'PY'
from pathlib import Path
import json,sys
out=Path(sys.argv[1]); seed=int(sys.argv[2]); job_id=sys.argv[3]
files=sorted(p.name for p in Path(".").iterdir())
stderr=Path("engine.stderr.txt").read_text(errors="replace")[-8000:] if Path("engine.stderr.txt").exists() else ""
stdout=Path("engine.stdout.txt").read_text(errors="replace")[-8000:] if Path("engine.stdout.txt").exists() else ""
result={
 "stage":"v0.6D1-R4.54","engine":"NEMO","probe_job_id":job_id,
 "frozen_seed":seed,"seed_injection_mode":"NEMO_RANDOM_SEED_INI_PARAMETER",
 "seed_binding_verified":False,"dry_run":True,"scientific_evidence":False,
 "status":"FAIL","returncode":20,"metrics":[],
 "unauthorized_metric_count":0,"numeric_acceptance_threshold_count":0,
 "automatic_scientific_pass_fail_count":0,"artifact_hashes":{},
 "canonical_state_changed":False,"error":"NEMO qfreq output missing",
 "runtime_file_listing":files,"engine_stdout_tail":stdout,"engine_stderr_tail":stderr,
}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
PY
  exit 20
fi

set +e
python "$collector" "$out_json" "$work/Nemo2_R454.ini" "$qfreq" \
  "$work/engine.stdout.txt" "$work/engine.stderr.txt" "$seed" "$job_id"
crc=$?
set -e
if [ "$crc" -ne 0 ] && [ ! -s "$out_json" ]; then
  python - "$out_json" "$seed" "$job_id" "$crc" "$qfreq" <<'PY'
from pathlib import Path
import json,sys
out=Path(sys.argv[1]); seed=int(sys.argv[2]); job_id=sys.argv[3]; rc=int(sys.argv[4]); qfreq=sys.argv[5]
result={
 "stage":"v0.6D1-R4.54","engine":"NEMO","probe_job_id":job_id,
 "frozen_seed":seed,"seed_injection_mode":"NEMO_RANDOM_SEED_INI_PARAMETER",
 "seed_binding_verified":False,"dry_run":True,"scientific_evidence":False,
 "status":"FAIL","returncode":rc,"metrics":[],
 "unauthorized_metric_count":0,"numeric_acceptance_threshold_count":0,
 "automatic_scientific_pass_fail_count":0,"artifact_hashes":{},
 "canonical_state_changed":False,
 "error":"NEMO collector failed before result materialization",
 "qfreq_file":qfreq,
}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
PY
fi
exit "$crc"
