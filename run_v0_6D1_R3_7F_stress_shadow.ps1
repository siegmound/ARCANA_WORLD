param([string]$Python = "python")
$ErrorActionPreference = "Stop"
& $Python scripts/run_v0_6D1_R3_7F_stress_shadow.py --end-age-ma 188
if ($LASTEXITCODE -ne 0) { throw "R3.7F governed stress-window shadow replay failed with exit code $LASTEXITCODE" }
