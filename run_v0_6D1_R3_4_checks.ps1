$ErrorActionPreference='Stop'
$env:PYTHONPATH = Join-Path $PSScriptRoot 'src'
python -m pytest -q tests
if ($LASTEXITCODE -ne 0) { throw 'R3.4 tests failed' }
python .\scripts\headroom_audit_v0_6D1_R3_4.py | Out-File -Encoding utf8 .\outputs\v0_6D1_R3_4\HEADROOM_AUDIT_STDOUT_v0_6D1_R3_4.txt
if ($LASTEXITCODE -ne 0) { throw 'R3.4 headroom audit failed' }
python .\scripts\audit_v0_6D1_R3_4.py | Out-File -Encoding utf8 .\outputs\v0_6D1_R3_4\FORMAL_AUDIT_STDOUT_v0_6D1_R3_4.txt
if ($LASTEXITCODE -ne 0) { throw 'R3.4 formal audit failed' }
