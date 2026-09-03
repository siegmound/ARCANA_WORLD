param([double]$EndAgeMa=150,[int]$Threads=12)
$ErrorActionPreference='Stop'
$env:OMP_NUM_THREADS="$Threads"; $env:MKL_NUM_THREADS="$Threads"; $env:OPENBLAS_NUM_THREADS="$Threads"; $env:NUMEXPR_NUM_THREADS="$Threads"
python .\scripts\run_v0_6D1_R3_4_local.py --end-age-ma $EndAgeMa --threads $Threads
if ($LASTEXITCODE -ne 0) { throw "R3.4 run failed" }
