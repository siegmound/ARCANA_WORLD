$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$env:PYTHONPATH = "$root\src" + ($(if($env:PYTHONPATH){";$env:PYTHONPATH"}else{""}))

# R4.20-R1: avoid the host-global pytest temp root. On the first Windows
# attempt pytest could not enumerate %LOCALAPPDATA%\Temp\pytest-of-<user>
# (WinError 5) while resolving tmp_path. Use project-local scratch instead.
$pytestBase = Join-Path $root 'outputs\v0_6D1_R4_20\pytest_tmp'
$pytestParent = Split-Path -Parent $pytestBase
if(-not (Test-Path $pytestParent)) {
  New-Item -ItemType Directory -Path $pytestParent -Force | Out-Null
}

Write-Host '=== R4.20 source authority ==='
python .\scripts\check_v0_6D1_R4_20_source_manifest.py .
if($LASTEXITCODE -ne 0){ exit 2 }
Write-Host '=== R4.20 regression (R4.20-R1 project-local pytest basetemp) ==='
python -m pytest -q .\tests\test_r420_p2_adapter_preflight_target_protocol_repair.py --basetemp "$pytestBase"
if($LASTEXITCODE -ne 0){ exit 2 }
Write-Host '=== R4.20 P2 adapter implementation preflight + target-design protocol repair ==='
python .\scripts\run_v0_6D1_R4_20.py --root .
if($LASTEXITCODE -ne 0){ Write-Host 'R4.20 BLOCKED. Preserve outputs/R4.20 diagnostics.'; exit 3 }
Write-Host '=== R4.20 final fail-closed seal ==='
python .\scripts\audit_v0_6D1_R4_20_seal.py --root .
if($LASTEXITCODE -ne 0){ exit 4 }
Write-Host 'PASS_R420_INTEGRATED_AND_FINAL_SEAL_RUN'
