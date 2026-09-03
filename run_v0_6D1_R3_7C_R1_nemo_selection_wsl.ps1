param(
  [int]$Replicates = 2,
  [int[]]$PopulationSizes = @(500,2000),
  [double[]]$SelectionVariances = @(1.0,4.0),
  [int]$LociPerTrait = 64,
  [double]$OptimumAmplitude = 0.6,
  [int]$ParallelChains = 4,
  [string]$CondaEnv = "arcana-nemo242"
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Out = Join-Path $Root "local_runs\v0_6D1_R3_7C_R1_SELECTION"
$env:PYTHONPATH = Join-Path $Root "src"
$popArgs = @(); foreach ($n in $PopulationSizes) { $popArgs += "$n" }
$selArgs = @(); foreach ($s in $SelectionVariances) { $selArgs += "$s" }
python (Join-Path $Root "scripts\run_nemo_r37c_r1_selection_chain.py") $Out `
  --replicates $Replicates `
  --population-sizes $popArgs `
  --selection-variances $selArgs `
  --loci-per-trait $LociPerTrait `
  --optimum-amplitude $OptimumAmplitude `
  --parallel-chains $ParallelChains `
  --conda-env $CondaEnv
if ($LASTEXITCODE -ne 0) { throw "R3.7C-R1 NEMO selection suite failed/effect gate rejected with exit code $LASTEXITCODE" }
