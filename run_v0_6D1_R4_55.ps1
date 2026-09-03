param(
  [string]$Python = "python",
  [switch]$NoResume
)

$ErrorActionPreference = "Stop"
$Root = (Get-Location).Path
$env:PYTHONPATH = Join-Path $Root "src"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"

$Base = Join-Path $Root ".pytest_tmp_r455"
if (Test-Path $Base) {
  Remove-Item -Recurse -Force $Base
}

Write-Host "=== R4.55 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_55_source_manifest.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.55 regression ==="
& $Python -m pytest -q ".\tests\test_r455_non_geonomics_80_stream_execution_evidence_capture.py" --basetemp $Base
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$Runtime = Join-Path $Root "outputs\v0_6D1_R4_55\R4_55_RUNTIME_IDENTITY_EVIDENCE.json"
Write-Host "=== R4.55 fresh governed runtime identity evidence ==="
& ".\capture_v0_6D1_R4_0_runtime_evidence.ps1" -OutputPath $Runtime
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.55 preexecution authority + exact dispatch binding ==="
& $Python ".\scripts\preflight_v0_6D1_R4_55.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.55 scientific execution: 20 jobs / 80 frozen streams ==="
& ".\capture_v0_6D1_R4_55_scientific_jobs.ps1" `
  -Python $Python `
  -RuntimeIdentityEvidence $Runtime `
  -NoResume:$NoResume
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.55 aggregate full non-Geonomics scientific evidence corpus ==="
& $Python ".\scripts\aggregate_v0_6D1_R4_55.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.55 final fail-closed execution/evidence seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_55_seal.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "PASS_R455_INTEGRATED_AND_FINAL_SEAL_RUN"
