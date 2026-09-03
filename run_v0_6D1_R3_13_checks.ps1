$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $Root
try {
  $env:PYTHONPATH = "$Root\src"
  $BaseTemp = Join-Path $Root ".pytest_tmp\r313_checks_$PID"
  New-Item -ItemType Directory -Path $BaseTemp -Force | Out-Null
  python -m pytest -q --basetemp "$BaseTemp" tests/test_r313_longterm_postcha1_reassembly.py tests/test_r312_postcha1_diversity_recovery.py tests/test_r311_postcha1_recovery.py
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally { Pop-Location }
