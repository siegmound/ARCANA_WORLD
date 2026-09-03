param(
  [Parameter(Mandatory=$true, Position=0)]
  [string[]]$Roots,
  [string]$Output = ".\outputs\LOCAL_RECOVERY_SCAN_v0_6D1_R0.json"
)
$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Py = "python"
$Script = Join-Path $Here "scripts\scan_arcana_historical_artifacts.py"
$OutPath = if ([System.IO.Path]::IsPathRooted($Output)) { $Output } else { Join-Path $Here $Output }
& $Py $Script @Roots --output $OutPath
if ($LASTEXITCODE -ne 0) { throw "Historical artifact scan failed." }
Write-Host "Recovery scan written to: $OutPath"
