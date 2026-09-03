$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$ROOT\src"
python "$ROOT\scripts\run_v0_6D1_R3_22_functional_phenotype_spec.py" --root "$ROOT"
if ($LASTEXITCODE -ne 0) { throw "R3.22 functional phenotype specification failed closed." }
