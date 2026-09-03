param(
  [int]$Replicates = 2,
  [int[]]$PopulationSizes = @(500,2000),
  [int]$LociPerTrait = 64,
  [int]$ParallelChains = 4,
  [string]$CondaEnv = "arcana-nemo242"
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Out = Join-Path $Root "local_runs\v0_6D1_R3_7A_B2"
$env:PYTHONPATH = Join-Path $Root "src"
$popArgs = @(); foreach ($n in $PopulationSizes) { $popArgs += "$n" }
python (Join-Path $Root "scripts\run_nemo_r37a_b2_chain.py") $Out `
  --replicates $Replicates `
  --population-sizes $popArgs `
  --loci-per-trait $LociPerTrait `
  --parallel-chains $ParallelChains `
  --conda-env $CondaEnv
if ($LASTEXITCODE -ne 0) { throw "R3.7A NEMO B2 chain suite failed with exit code $LASTEXITCODE" }
