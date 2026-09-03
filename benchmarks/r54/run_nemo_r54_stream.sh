#!/usr/bin/env bash
set -euo pipefail
WD="${1:?work directory required}"
CONDA_EXE="${2:?conda executable required}"
CONDA_ENV="${3:?conda env required}"
SEED="${4:?seed required}"
VARIANT="${5:?variant required}"
INI="Nemo2_ARCANA_R54.ini"
if [[ ! -d "$WD" || ! -f "$WD/$INI" ]]; then echo "R5.4 stream input missing: $WD/$INI" >&2; exit 4; fi
if [[ ! -x "$CONDA_EXE" ]]; then echo "R5.4 Conda executable unavailable: $CONDA_EXE" >&2; exit 5; fi
cd "$WD"
rm -f ./*.qfreq engine.stdout.txt engine.stderr.txt engine.returncode.txt STREAM_RUNTIME.json
set +e
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  "$CONDA_EXE" run -n "$CONDA_ENV" nemo2.4.2 "$INI" >engine.stdout.txt 2>engine.stderr.txt
rc=$?
set -e
printf '%s\n' "$rc" > engine.returncode.txt
mapfile -t qfiles < <(find . -maxdepth 1 -type f -name '*.qfreq' -printf '%f\n' | sort)
qcount=${#qfiles[@]}
qsha=""
if [[ "$qcount" -eq 1 ]]; then qsha="$(sha256sum "${qfiles[0]}" | awk '{print $1}')"; fi
inisha="$(sha256sum "$INI" | awk '{print $1}')"
status="FAILED_R54_NEMO_STREAM"
if [[ "$rc" -eq 0 && "$qcount" -eq 1 ]]; then status="PASS_R54_NEMO_STREAM"; fi
cat > STREAM_RUNTIME.json <<EOF
{
  "stage": "v0.6D1-R5.4",
  "status": "$status",
  "nemo_version": "2.4.2",
  "nemo_executable_name": "nemo2.4.2",
  "conda_env_name": "$CONDA_ENV",
  "seed": $SEED,
  "variant": "$VARIANT",
  "returncode": $rc,
  "qfreq_file_count": $qcount,
  "qfreq_sha256": $(if [[ -n "$qsha" ]]; then printf '"%s"' "$qsha"; else printf 'null'; fi),
  "ini_sha256": "$inisha"
}
EOF
if [[ "$status" != "PASS_R54_NEMO_STREAM" ]]; then
  echo "R5.4 stream failed: rc=$rc qfreq_count=$qcount $WD" >&2
  exit 6
fi
