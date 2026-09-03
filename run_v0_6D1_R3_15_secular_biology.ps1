param(
    [switch]$Smoke,
    [string]$Python = "python"
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root "src"
$script = Join-Path $Root "scripts\run_v0_6D1_R3_15_secular_biology.py"
$argsList = @($script)
if ($Smoke) { $argsList += "--smoke" }
& $Python @argsList
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
