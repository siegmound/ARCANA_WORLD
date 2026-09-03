#!/usr/bin/env bash
set -euo pipefail
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec Rscript "$@"
