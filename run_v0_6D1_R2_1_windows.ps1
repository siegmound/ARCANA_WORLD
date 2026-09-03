param(
    [switch]$FullPilot,
    [switch]$AllTests
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root "src"

Write-Host "=== ARCANA v0.6D1-R2.1 ==="
Write-Host "Root: $Root"

python (Join-Path $Root "scripts\audit_v0_6D1_R2_1.py")
if ($LASTEXITCODE -ne 0) { throw "R2.1 formal audit failed." }

python -m pytest -q (Join-Path $Root "tests\test_governed_speciation_extinction_cadence_v0_6D1_R2_1.py") --disable-warnings
if ($LASTEXITCODE -ne 0) { throw "R2.1 actuator/cadence tests failed." }

if ($AllTests) {
    python -m pytest -q (Join-Path $Root "tests") --disable-warnings
    if ($LASTEXITCODE -ne 0) { throw "Full included regression suite failed." }
}

if ($FullPilot) {
    python (Join-Path $Root "scripts\run_v0_6D1_R2_1_pilot.py")
    if ($LASTEXITCODE -ne 0) { throw "R2.1 210->180 Ma pilot failed." }
}

Write-Host "R2.1 checks PASS."
