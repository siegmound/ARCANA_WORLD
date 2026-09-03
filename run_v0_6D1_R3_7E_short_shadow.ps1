param([string]$Python = "python")
$ErrorActionPreference = "Stop"
& $Python scripts/run_v0_6D1_R3_7E_short_shadow.py --end-age-ma 205
if ($LASTEXITCODE -ne 0) { throw "R3.7E full short shadow replay failed with exit code $LASTEXITCODE" }
