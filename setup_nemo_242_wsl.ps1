param([string]$CondaEnv = "arcana-nemo242")
$ErrorActionPreference = "Stop"
Write-Host "=== WSL preflight ==="
wsl bash -lc "uname -a"
if ($LASTEXITCODE -ne 0) { throw "WSL preflight failed" }

Write-Host "=== Conda preflight ==="
$CondaPath = (wsl bash -lc "command -v conda").Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($CondaPath)) { throw "Conda is not visible in WSL login shell" }
Write-Host $CondaPath

Write-Host "=== Install official NEMO channel build ==="
wsl bash -lc "conda create -y -n '$CondaEnv' -c conda-forge -c ecoevo nemo"
if ($LASTEXITCODE -ne 0) { throw "NEMO environment creation failed" }

Write-Host "=== Exact executable gate ==="
$NemoPath = (wsl bash -lc "conda run -n '$CondaEnv' which nemo2.4.2").Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($NemoPath)) { throw "nemo2.4.2 executable was not found in WSL env $CondaEnv" }
if ([System.IO.Path]::GetFileName($NemoPath) -ne "nemo2.4.2") { throw "Unexpected NEMO executable: $NemoPath" }
Write-Host $NemoPath
Write-Host "PASS: exact nemo2.4.2 executable is available in WSL env $CondaEnv"
