param(
    [string]$CheckpointJson = "",
    [string]$CheckpointNpz = "",
    [string]$OutputDir = ""
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = "python"
if (Test-Path (Join-Path $Root ".venv\Scripts\python.exe")) {
    $Python = Join-Path $Root ".venv\Scripts\python.exe"
}
$argsList = @(
    (Join-Path $Root "scripts\run_v0_6D1_R3_21_present_lineage_registry.py"),
    "--root", $Root
)
if ($CheckpointJson -ne "") { $argsList += @("--checkpoint-json", $CheckpointJson) }
if ($CheckpointNpz -ne "") { $argsList += @("--checkpoint-npz", $CheckpointNpz) }
if ($OutputDir -ne "") { $argsList += @("--output-dir", $OutputDir) }
& $Python @argsList
if ($LASTEXITCODE -ne 0) { throw "R3.21 present-lineage registry failed closed." }
