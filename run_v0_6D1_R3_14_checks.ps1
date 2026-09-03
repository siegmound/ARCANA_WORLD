$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src" + $(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { "" })
$Tmp = Join-Path $Root ".pytest_tmp\r314_checks_$PID"
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
try {
  python -m pytest -q --basetemp "$Tmp" `
    "$Root\tests\test_r314_late_cenozoic_binding.py" `
    "$Root\tests\test_r314_c1_numeric_portability.py" `
    "$Root\tests\test_r313_longterm_postcha1_reassembly.py" `
    "$Root\tests\test_r312_postcha1_diversity_recovery.py"
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
  Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
}
