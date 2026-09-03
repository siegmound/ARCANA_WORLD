param([string]$Python = "python")
$ErrorActionPreference = "Stop"
& $Python scripts/run_v0_6D1_R3_7F_stress_shadow.py --end-age-ma 209 --diagnostic-smoke
if ($LASTEXITCODE -ne 0) { throw "R3.7F diagnostic smoke failed with exit code $LASTEXITCODE" }
