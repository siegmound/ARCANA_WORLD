param(
  [string]$OutDir = "local_runs/v0_6D1_R3_6D",
  [int]$Replicates = 2,
  [int[]]$PopulationSizes = @(500,2000),
  [int]$LociPerTrait = 64,
  [int]$MacroIntervals = 1,
  [string]$CondaEnv = "arcana-nemo242",
  [int]$ParallelJobs = 6
)
$ErrorActionPreference="Stop"

function Convert-ArcanaWindowsPathToWsl {
  param([Parameter(Mandatory=$true)][string]$Path)
  $full = [System.IO.Path]::GetFullPath($Path)
  if ($full -match '^([A-Za-z]):\\(.*)$') {
    $drive = $Matches[1].ToLowerInvariant()
    $rest = $Matches[2] -replace '\\','/'
    return "/mnt/$drive/$rest"
  }
  throw "R3.6D supports Windows drive paths only for WSL execution; unsupported path: $full"
}

$env:PYTHONPATH="$PWD\src"
$popArgs = $PopulationSizes | ForEach-Object { "$_" }
python scripts/prepare_nemo_242_executable_suite_v0_6D1_R3_6D.py $OutDir --replicates $Replicates --loci-per-trait $LociPerTrait --macro-intervals $MacroIntervals --population-sizes $popArgs
if ($LASTEXITCODE -ne 0) { throw "R3.6D suite preparation failed with exit code $LASTEXITCODE" }

$WinOut=(Resolve-Path $OutDir).Path
$WslOut=Convert-ArcanaWindowsPathToWsl $WinOut
$WinScript=(Resolve-Path "scripts/run_nemo_242_suite_wsl.sh").Path
$WslScript=Convert-ArcanaWindowsPathToWsl $WinScript

Write-Host "=== WSL path binding ==="
Write-Host "Windows output: $WinOut"
Write-Host "WSL output:     $WslOut"
Write-Host "WSL runner:     $WslScript"

# Use a login shell so the user's Conda initialization is available.
$wslCommand = "bash '$WslScript' '$WslOut' '$CondaEnv' '$ParallelJobs'"
wsl bash -lc $wslCommand
if ($LASTEXITCODE -ne 0) { throw "R3.6D NEMO WSL suite failed with exit code $LASTEXITCODE" }

python scripts/collect_nemo_242_evidence_v0_6D1_R3_6D.py $OutDir
if ($LASTEXITCODE -ne 0) { throw "R3.6D evidence collection failed with exit code $LASTEXITCODE" }
