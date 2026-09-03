param(
  [Parameter(Mandatory=$true)][string]$D22Zip
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$Py = if (Test-Path ".venv\Scripts\python.exe") { (Resolve-Path ".venv\Scripts\python.exe").Path } else { "python" }
$env:PYTHONPATH = (Join-Path $Root "src")
& $Py scripts\verify_and_bind_d22_package_v0_6D1.py --d22-zip $D22Zip --workdir local_runs/v0_6D1/d22_bound
if ($LASTEXITCODE -ne 0) { throw "v0.6D1 D2.2 binding failed" }
Write-Host "D2.2 canonical binding + Deep-OFF RAW parity: PASS"
Write-Host "Report: local_runs\v0_6D1\d22_bound\D22_BINDING_REPORT_v0_6D1.json"
Write-Host "Historical Deep-ON pilot remains fail-closed until D1/D2 pre-CHA1 executable state is supplied."
