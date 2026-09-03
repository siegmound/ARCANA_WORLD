param([string]$Python = "python")
$ErrorActionPreference = "Stop"
& $Python scripts/run_v0_6D1_R3_7G_production_validation.py --end-age-ma 150
if ($LASTEXITCODE -ne 0) { throw "R3.7G governed 210->150 production-binding validation failed with exit code $LASTEXITCODE" }
