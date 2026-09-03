param(
    [switch]$Smoke
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = "python"
$argsList = @("$Root\scripts\run_v0_6D1_R3_12_diversity_recovery.py")
if ($Smoke) { $argsList += "--smoke" }
& $Python @argsList
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
