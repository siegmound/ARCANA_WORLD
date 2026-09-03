param(
    [string]$Python="python",
    [string]$GeonomicsWslPython="/home/jose/miniforge3/envs/arcana-geonomics-149/bin/python"
)

$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r440"

if(Test-Path $Base){
    Remove-Item -Recurse -Force $Base
}

Write-Host "=== R4.40 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_40_source_manifest.py"
if($LASTEXITCODE -ne 0){
    exit $LASTEXITCODE
}

Write-Host "=== R4.40 regression ==="
& $Python -m pytest -q ".\tests\test_r440_geonomics_domain_specific_carrier_dynamics_authority_execution_queue.py" --basetemp $Base
if($LASTEXITCODE -ne 0){
    exit $LASTEXITCODE
}

Write-Host "=== R4.40 governed Geonomics 1.4.9 WSL authority preflight ==="
$VersionOutput=& wsl.exe -e $GeonomicsWslPython -c "import geonomics as gnx; print(gnx.__version__)"
if($LASTEXITCODE -ne 0){
    exit 20
}
$VersionLines=@(
    $VersionOutput |
    ForEach-Object { "$_".Trim() } |
    Where-Object { $_ -ne "" }
)
$ResolvedVersion=if($VersionLines.Count -gt 0){$VersionLines[-1]}else{""}
if($ResolvedVersion -ne "1.4.9"){
    Write-Host "R4.40 BLOCKED: expected Geonomics 1.4.9, got '$ResolvedVersion'"
    exit 21
}

$WslRoot=(& wsl.exe -e wslpath -a $Root).Trim()
if($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($WslRoot)){
    exit 22
}

Write-Host "=== R4.40 domain-specific carrier dynamics authority + execution queue preflight ==="
$Cmd="cd '$WslRoot' && PYTHONPATH='$WslRoot/src' '$GeonomicsWslPython' '$WslRoot/scripts/run_v0_6D1_R4_40.py'"
& wsl.exe -e bash -lc $Cmd
if($LASTEXITCODE -ne 0){
    Write-Host "R4.40 BLOCKED"
    exit $LASTEXITCODE
}

Write-Host "=== R4.40 final fail-closed seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_40_seal.py"
if($LASTEXITCODE -ne 0){
    exit $LASTEXITCODE
}

Write-Host "PASS_R440_INTEGRATED_AND_FINAL_SEAL_RUN"
