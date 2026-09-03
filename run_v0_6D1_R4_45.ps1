param(
    [string]$Python="python",
    [string]$GeonomicsWslPython="/home/jose/miniforge3/envs/arcana-geonomics-149/bin/python"
)

$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r445"

if(Test-Path $Base){
    Remove-Item -Recurse -Force $Base
}

Write-Host "=== R4.45 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_45_source_manifest.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.45 regression ==="
& $Python -m pytest -q ".\tests\test_r445_geonomics_scientific_execution_authorization_first_governed_revalidation_preflight.py" --basetemp $Base
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.45 governed Geonomics 1.4.9 WSL execution-authorization preflight ==="
$VersionOutput=& wsl.exe -e $GeonomicsWslPython -c "import geonomics as gnx; print(gnx.__version__)"
if($LASTEXITCODE -ne 0){ exit 20 }
$VersionLines=@(
    $VersionOutput |
    ForEach-Object { "$_".Trim() } |
    Where-Object { $_ -ne "" }
)
$ResolvedVersion=if($VersionLines.Count -gt 0){$VersionLines[-1]}else{""}
if($ResolvedVersion -ne "1.4.9"){
    Write-Host "R4.45 BLOCKED: expected Geonomics 1.4.9, got '$ResolvedVersion'"
    exit 21
}

$WslRoot=(& wsl.exe -e wslpath -a $Root).Trim()
if($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($WslRoot)){ exit 22 }

$Cmd="cd '$WslRoot' && PYTHONPATH='$WslRoot/src' '$GeonomicsWslPython' '$WslRoot/scripts/run_v0_6D1_R4_45.py'"
& wsl.exe -e bash -lc $Cmd
if($LASTEXITCODE -ne 0){
    Write-Host "R4.45 BLOCKED"
    exit $LASTEXITCODE
}

Write-Host "=== R4.45 final fail-closed seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_45_seal.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "PASS_R445_INTEGRATED_AND_FINAL_SEAL_RUN"
