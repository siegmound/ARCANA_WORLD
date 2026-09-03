param(
  [double]$EndAgeMa = 150,
  [ValidateSet(0.08,0.10)][double]$Ceiling = 0.08,
  [int]$Threads = 12
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:OMP_NUM_THREADS = "$Threads"
$env:MKL_NUM_THREADS = "$Threads"
$env:OPENBLAS_NUM_THREADS = "$Threads"
$env:NUMEXPR_NUM_THREADS = "$Threads"
$env:PYTHONPATH = Join-Path $Root 'src'
python (Join-Path $Root 'scripts/run_v0_6D1_R3_5_local.py') --end-age-ma $EndAgeMa --ceiling $Ceiling --threads $Threads
if ($LASTEXITCODE -ne 0) { throw "R3.5 run failed with exit code $LASTEXITCODE" }
