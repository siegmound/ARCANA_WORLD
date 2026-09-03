param(
    [string]$Python="python",
    [string]$GeonomicsWslPython="/home/jose/miniforge3/envs/arcana-geonomics-149/bin/python"
)
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r436"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.36 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_36_source_manifest.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.36 regression (project-local pytest basetemp) ==="
& $Python -m pytest -q ".\tests\test_r436_geonomics_native_parameter_model_construction_injection_preflight.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.36 Geonomics SEALED WSL host-runtime bridge preflight ==="
$VersionOutput = & wsl.exe -e $GeonomicsWslPython -c "import geonomics as gnx; print(gnx.__version__)"
if($LASTEXITCODE -ne 0){
    Write-Host "R4.36 BLOCKED: governed Geonomics WSL runtime is not executable"
    exit 20
}
$VersionLines = @($VersionOutput | ForEach-Object { "$_".Trim() } | Where-Object { $_ -ne "" })
$ResolvedVersion = if($VersionLines.Count -gt 0){$VersionLines[-1]}else{""}
if($ResolvedVersion -ne "1.4.9"){
    Write-Host "R4.36 BLOCKED: expected Geonomics 1.4.9, got '$ResolvedVersion'"
    exit 21
}

$WslRoot = (& wsl.exe -e wslpath -a $Root).Trim()
if($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($WslRoot)){
    Write-Host "R4.36 BLOCKED: cannot translate project root through WSL"
    exit 22
}
$WslScript = "$WslRoot/scripts/run_v0_6D1_R4_36.py"
$WslSrc = "$WslRoot/src"

$BridgeEvidenceDir = Join-Path $Root "outputs\v0_6D1_R4_36"
New-Item -ItemType Directory -Path $BridgeEvidenceDir -Force | Out-Null
$BridgeEvidence = [ordered]@{
    stage = "v0.6D1-R4.36-R1"
    status = "PASS_R436_R1_GOVERNED_GEONOMICS_WSL_RUNTIME_BRIDGE_PREFLIGHT"
    boundary = "WINDOWS_POWERSHELL_TO_WSL_GOVERNED_GEONOMICS_RUNTIME"
    wsl_python = $GeonomicsWslPython
    geonomics_version = $ResolvedVersion
    windows_project_root = $Root
    wsl_project_root = $WslRoot
    reinstall_performed = $false
    new_environment_created = $false
    scientific_execution_performed = $false
    target_numeric_execution_performed = $false
    canonical_state_changed = $false
}
$BridgeEvidence | ConvertTo-Json -Depth 8 | Set-Content `
    -Path (Join-Path $BridgeEvidenceDir "R4_36_R1_HOST_RUNTIME_BRIDGE_PREFLIGHT.json") `
    -Encoding UTF8

Write-Host "=== R4.36 native params + make_model construction + exact-state injection preflight (governed WSL Geonomics 1.4.9) ==="
$BashCmd = "cd '$WslRoot' && PYTHONPATH='$WslSrc' '$GeonomicsWslPython' '$WslScript'"
& wsl.exe -e bash -lc $BashCmd
if($LASTEXITCODE -ne 0){
  Write-Host "R4.36 BLOCKED"
  exit $LASTEXITCODE
}

Write-Host "=== R4.36 final fail-closed seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_36_seal.py"
if($LASTEXITCODE -ne 0){
  Write-Host "R4.36 FINAL SEAL BLOCKED"
  exit $LASTEXITCODE
}

Write-Host "PASS_R436_INTEGRATED_AND_FINAL_SEAL_RUN"
