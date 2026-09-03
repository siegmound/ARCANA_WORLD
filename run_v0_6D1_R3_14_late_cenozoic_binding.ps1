param(
  [string[]]$SearchRoot = @()
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src" + $(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { "" })
$argsList = @("$Root\scripts\run_v0_6D1_R3_14_late_cenozoic_binding.py", "--root", $Root)
foreach ($s in $SearchRoot) { $argsList += @("--search-root", $s) }
python @argsList
exit $LASTEXITCODE
