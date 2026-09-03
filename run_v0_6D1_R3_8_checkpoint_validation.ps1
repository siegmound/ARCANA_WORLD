param(
  [double]$RestartEndAgeMa = 149.0
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
python (Join-Path $Root "scripts\run_v0_6D1_R3_8_checkpoint_validation.py") --restart-end-age-ma $RestartEndAgeMa
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
