param([string]$Python = "python")
$ErrorActionPreference = "Stop"
& $Python -m pytest -q tests\test_r37i_production_promotion.py
if ($LASTEXITCODE -ne 0) { throw "R3.7I tests failed" }
$Seal = Join-Path $PSScriptRoot "outputs\v0_6D1_R3_7I\PRODUCTION_PROMOTION_SEAL_v0_6D1_R3_7I.json"
if (Test-Path $Seal) {
  & $Python scripts\formal_audit_v0_6D1_R3_7I_SEALED.py
  if ($LASTEXITCODE -ne 0) { throw "R3.7I sealed formal audit failed" }
} else {
  & $Python scripts\formal_audit_v0_6D1_R3_7I.py
  if ($LASTEXITCODE -ne 0) { throw "R3.7I candidate formal audit failed" }
}
