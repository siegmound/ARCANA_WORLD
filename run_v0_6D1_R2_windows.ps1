param(
  [string]$Python = "python",
  [int]$DtYears = 250000,
  [double]$TopologySwitchMa = 195.0,
  [string]$Output = ".\outputs\v0_6D1_R2\LOCAL_H0_210_180_STATE.npz"
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Common = Join-Path $Root "references\v0_6D1_R2\WORLD1_210Ma_REBASELINE_COMMON_STATE_PARENT_R1.npz"
$A1 = Join-Path $Root "references\v0_6D1_R2\A1_WORLD1_210_180_REFERENCE_v0_6D1_R2.npz"
$Meta = Join-Path $Root "references\v0_6D1_R2\D1_species_metadata_120.json"
$Script = Join-Path $Root "src\rebased_natural_control_runtime_v0_6D1_R2.py"
$OutPath = Join-Path $Root $Output
Write-Host "ARCANA v0.6D1-R2 H0 210->180 Ma"
& $Python $Script --common $Common --a1 $A1 --meta $Meta --dt $DtYears --switch $TopologySwitchMa --out $OutPath
if ($LASTEXITCODE -ne 0) { throw "R2 runtime failed with exit code $LASTEXITCODE" }
Write-Host "Output:" $OutPath
