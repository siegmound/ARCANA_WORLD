param(
    [string]$Python="python",
    [string]$GeonomicsWslPython="/home/jose/miniforge3/envs/arcana-geonomics-149/bin/python"
)
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r437"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.37 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_37_source_manifest.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.37 regression ==="
& $Python -m pytest -q ".\tests\test_r437_geonomics_canonical_layer_binding_exact_state_injection_dry_run.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.37 governed Geonomics 1.4.9 WSL runtime preflight ==="
$VersionOutput = & wsl.exe -e $GeonomicsWslPython -c "import geonomics as gnx; print(gnx.__version__)"
if($LASTEXITCODE -ne 0){exit 20}
$VersionLines=@($VersionOutput|ForEach-Object{"$_".Trim()}|Where-Object{$_ -ne ""})
$ResolvedVersion=if($VersionLines.Count -gt 0){$VersionLines[-1]}else{""}
if($ResolvedVersion -ne "1.4.9"){
    Write-Host "R4.37 BLOCKED: expected Geonomics 1.4.9, got '$ResolvedVersion'"
    exit 21
}

$WslRoot=(& wsl.exe -e wslpath -a $Root).Trim()
if($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($WslRoot)){exit 22}
$WslSrc="$WslRoot/src"
$WslScript="$WslRoot/scripts/run_v0_6D1_R4_37.py"

Write-Host "=== R4.37 canonical layer binding + exact-state public-API mechanical dry run ==="
$Cmd="cd '$WslRoot' && PYTHONPATH='$WslSrc' '$GeonomicsWslPython' '$WslScript'"
& wsl.exe -e bash -lc $Cmd
if($LASTEXITCODE -ne 0){
    Write-Host "R4.37 BLOCKED"
    exit $LASTEXITCODE
}

Write-Host "=== R4.37 final fail-closed seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_37_seal.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "PASS_R437_INTEGRATED_AND_FINAL_SEAL_RUN"
