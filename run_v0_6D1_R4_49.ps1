param(
    [string]$Python="python",
    [string]$GeonomicsWslPython="/home/jose/miniforge3/envs/arcana-geonomics-149/bin/python",
    [int]$ParallelJobs=2
)

$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r449"

if(Test-Path $Base){
    Remove-Item -Recurse -Force $Base
}

Write-Host "=== R4.49 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_49_source_manifest.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.49 regression ==="
& $Python -m pytest -q ".\tests\test_r449_geonomics_j14_j18_full_job_revalidation_coverage_expansion_execution_evidence_capture.py" --basetemp $Base
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.49 governed Geonomics 1.4.9 full-coverage expansion execution ==="
$VersionOutput=& wsl.exe -e $GeonomicsWslPython -c "import geonomics as gnx; print(gnx.__version__)"
if($LASTEXITCODE -ne 0){ exit 20 }
$VersionLines=@(
    $VersionOutput |
    ForEach-Object { "$_".Trim() } |
    Where-Object { $_ -ne "" }
)
$ResolvedVersion=if($VersionLines.Count -gt 0){$VersionLines[-1]}else{""}
if($ResolvedVersion -ne "1.4.9"){
    Write-Host "R4.49 BLOCKED: expected Geonomics 1.4.9, got '$ResolvedVersion'"
    exit 21
}

$WslRoot=(& wsl.exe -e wslpath -a $Root).Trim()
if($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($WslRoot)){ exit 22 }

$Cmd="cd '$WslRoot' && PYTHONPATH='$WslRoot/src' '$GeonomicsWslPython' '$WslRoot/scripts/run_v0_6D1_R4_49.py' --parallel-jobs $ParallelJobs"
& wsl.exe -e bash -lc $Cmd
if($LASTEXITCODE -ne 0){
    Write-Host "R4.49 BLOCKED/PARTIAL. Completed valid shards are resumable and will be reused."
    exit $LASTEXITCODE
}

Write-Host "=== R4.49 final fail-closed evidence seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_49_seal.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "PASS_R449_INTEGRATED_AND_FINAL_SEAL_RUN"
