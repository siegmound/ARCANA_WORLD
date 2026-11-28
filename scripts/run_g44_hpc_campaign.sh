#!/usr/bin/env bash
# Reproducible, commit-pinned continuation of the authorized synthetic campaign.
set -eo pipefail
LABEL=${1:?unique launch label required}
[[ "$LABEL" =~ ^[A-Za-z0-9_]+$ ]]
DEV=$(git rev-parse --show-toplevel)
SHA=${2:-$(git rev-parse HEAD)}
BASE=/home/jlpfritas/HPC-POMDP/Arcana
CAMP="$BASE/ARCANA_WORLD_EVIDENCE/R6/R6_G44_HPC_FULL_MANTLE_20261128_NEW01"
DIR=experiments/r6_thermo_provider_pilot_v1
test ! -e "$CAMP/DRIVER_${LABEL}.stdout"
trap 'rc=$?; printf "%s\n" "$rc" > "$CAMP/DRIVER_'"$LABEL"'.exitcode"' EXIT
RUNNERS=$(mktemp -d "$BASE/ARCANA_G44_HPC_RUNNERS.XXXXXX")
while IFS= read -r name; do
 case "$name" in arcana_*.py)
  git -C "$DEV" show "$SHA:$DIR/$name" > "$RUNNERS/$name"
  test "$(git -C "$DEV" hash-object "$RUNNERS/$name")" = "$(git -C "$DEV" rev-parse "$SHA:$DIR/$name")"
 ;; esac
done < <(git -C "$DEV" ls-tree --name-only "$SHA:$DIR")
printf '%s\n' "$RUNNERS" > "$CAMP/RUNNERS_${LABEL}.path"
printf '%s\n' "$SHA" > "$CAMP/RUNNERS_${LABEL}.commit"
source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$BASE/ARCANA_WORLD_R6_C11A_VERIFY.a7voPe"
test "$(git rev-parse HEAD)" = 901cbb4a38916190df6a881bb561b6558dd997dd
test -z "$(git status --porcelain)"
export PYTHONPATH="$RUNNERS:$PWD/src:$PWD"
python -u "$RUNNERS/arcana_g44_hpc_sequence.py" > "$CAMP/DRIVER_${LABEL}.stdout" 2> "$CAMP/DRIVER_${LABEL}.stderr"
