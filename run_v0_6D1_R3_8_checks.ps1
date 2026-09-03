$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = (Join-Path $Root "src")
python -m pytest -q (Join-Path $Root "tests\test_r38_restartable_checkpoint.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$Checkpoint = Join-Path $Root "local_runs\v0_6D1_R3_8\WORLD1_150Ma_CANONICAL_CONTINUATION_CHECKPOINT_v0_6D1_R3_8.json"
if (Test-Path $Checkpoint) {
  python (Join-Path $Root "scripts\formal_audit_v0_6D1_R3_8_sealed.py")
} else {
  python (Join-Path $Root "scripts\formal_audit_v0_6D1_R3_8.py")
}
exit $LASTEXITCODE
