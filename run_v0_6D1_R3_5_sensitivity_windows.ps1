param(
  [double]$EndAgeMa = 150,
  [int]$Threads = 12
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:OMP_NUM_THREADS = "$Threads"
$env:MKL_NUM_THREADS = "$Threads"
$env:OPENBLAS_NUM_THREADS = "$Threads"
$env:NUMEXPR_NUM_THREADS = "$Threads"
$env:PYTHONPATH = Join-Path $Root 'src'
$RunDir = Join-Path $Root 'local_runs/v0_6D1_R3_5'
python (Join-Path $Root 'scripts/run_v0_6D1_R3_5_local.py') --end-age-ma $EndAgeMa --ceiling 0.08 --threads $Threads --out-dir $RunDir
if ($LASTEXITCODE -ne 0) { throw "R3.5 q=0.08 run failed" }
python (Join-Path $Root 'scripts/run_v0_6D1_R3_5_local.py') --end-age-ma $EndAgeMa --ceiling 0.10 --threads $Threads --out-dir $RunDir
if ($LASTEXITCODE -ne 0) { throw "R3.5 q=0.10 run failed" }
python (Join-Path $Root 'scripts/compare_v0_6D1_R3_5_dynamic_sensitivity.py') --run-dir $RunDir --end-age-ma $EndAgeMa
if ($LASTEXITCODE -ne 0) { throw "R3.5 comparison failed" }
