param([switch]$Smoke)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ArgsList = @("$Root\scripts\run_v0_6D1_R3_13_longterm_reassembly.py")
if ($Smoke) { $ArgsList += "--smoke" }
& python @ArgsList
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
