#!/usr/bin/env bash
set -euo pipefail
ini_src="$1"
work="$2"
out_json="$3"
mkdir -p "$work"
rm -f "$work"/r41_nemo_b1* "$out_json"
cp "$ini_src" "$work/Nemo2_R41_B1.ini"
cd "$work"
set +e
nemo2.4.2 Nemo2_R41_B1.ini >engine.stdout.txt 2>engine.stderr.txt
rc=$?
set -e
if [ "$rc" -ne 0 ]; then
  printf '{\n  "status": "FAIL",\n  "returncode": %s,\n  "metrics": {},\n  "error": "NEMO execution failed"\n}\n' "$rc" > "$out_json"
  exit "$rc"
fi
qfreq="r41_nemo_b1_1.qfreq"
if [ ! -s "$qfreq" ]; then
  printf '{\n  "status": "FAIL",\n  "returncode": 0,\n  "metrics": {},\n  "error": "NEMO qfreq output missing"\n}\n' > "$out_json"
  exit 20
fi
rows=$(awk 'NR>1 {n++} END {print n+0}' "$qfreq")
final_gap=$(awk '
NR>1 {
  pop=$1; locus=$3; freq=$5;
  if(pop==1) p1[locus]=freq;
  if(pop==2) p2[locus]=freq;
}
END {
  n=0; s=0;
  for(i in p1) if(i in p2) {d=p1[i]-p2[i]; if(d<0)d=-d; s+=d; n++;}
  if(n==0) print "nan"; else printf "%.12g", s/n;
}' "$qfreq")
initial_gap="0.45"
status="FAIL"
if awk -v f="$final_gap" -v i="$initial_gap" -v r="$rows" 'BEGIN {exit !((f+0)<(i+0) && r>=16)}'; then status="PASS"; fi
cat > "$out_json" <<JSON
{
  "status": "$status",
  "returncode": 0,
  "metrics": {
    "initial_mean_frequency_gap": $initial_gap,
    "final_mean_frequency_gap": $final_gap,
    "qfreq_rows": $rows,
    "generations": 100,
    "patches": 2,
    "loci": 8
  }
}
JSON
[ "$status" = "PASS" ] || exit 21
