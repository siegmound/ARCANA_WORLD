param(
  [string]$OutputPath = ""
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LocalEngineBindings = Join-Path $Root "set_r40_engine_env.local.ps1"
if (Test-Path $LocalEngineBindings) { . $LocalEngineBindings }
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
  $OutputPath = Join-Path $Root "outputs\v0_6D1_R4_0\R4_0_HOST_RUNTIME_EVIDENCE.json"
}

function Assert-ShellSafeValue {
  param([Parameter(Mandatory=$true)][string]$Value, [Parameter(Mandatory=$true)][string]$Name)
  if ($Value.Contains("'")) { throw "$Name contains an unsupported single quote for governed WSL bridge: $Value" }
  return "'$Value'"
}

$WslExe = $env:ARCANA_WSL_EXE
if ([string]::IsNullOrWhiteSpace($WslExe)) {
  $cmd = Get-Command wsl.exe -ErrorAction SilentlyContinue
  if ($null -eq $cmd) { throw "wsl.exe not found by PowerShell host runtime bridge" }
  $WslExe = $cmd.Source
}
if (-not (Test-Path $WslExe)) { throw "Governed WSL executable does not exist: $WslExe" }

$CondaPath = $env:ARCANA_WSL_CONDA
if ([string]::IsNullOrWhiteSpace($CondaPath)) { $CondaPath = "conda" }
$NemoEnv = if ($env:ARCANA_NEMO_CONDA_ENV) { $env:ARCANA_NEMO_CONDA_ENV } else { "arcana-nemo242" }
$GeonomicsEnv = if ($env:ARCANA_GEONOMICS_CONDA_ENV) { $env:ARCANA_GEONOMICS_CONDA_ENV } else { "arcana-geonomics-149" }
$REnv = if ($env:ARCANA_R40_R_CONDA_ENV) { $env:ARCANA_R40_R_CONDA_ENV } else { "arcana-r40-r" }
$CDMetaPOPEnv = if ($env:ARCANA_CDMETAPOP_CONDA_ENV) { $env:ARCANA_CDMETAPOP_CONDA_ENV } else { "arcana-cdmetapop-308" }
$SlimEnv = if ($env:ARCANA_SLIM_CONDA_ENV) { $env:ARCANA_SLIM_CONDA_ENV } else { "arcana-slim52" }

$CondaQ = Assert-ShellSafeValue $CondaPath "ARCANA_WSL_CONDA"
$NemoQ = Assert-ShellSafeValue $NemoEnv "ARCANA_NEMO_CONDA_ENV"
$GeoQ = Assert-ShellSafeValue $GeonomicsEnv "ARCANA_GEONOMICS_CONDA_ENV"
$RQ = Assert-ShellSafeValue $REnv "ARCANA_R40_R_CONDA_ENV"
$CdQ = Assert-ShellSafeValue $CDMetaPOPEnv "ARCANA_CDMETAPOP_CONDA_ENV"
$SlimQ = Assert-ShellSafeValue $SlimEnv "ARCANA_SLIM_CONDA_ENV"

function Convert-ArcanaWindowsPathToWsl {
  param([Parameter(Mandatory=$true)][string]$Path)
  $full = [System.IO.Path]::GetFullPath($Path)
  if ($full -match '^([A-Za-z]):\\(.*)$') {
    $drive = $Matches[1].ToLowerInvariant()
    $rest = $Matches[2] -replace '\\','/'
    return "/mnt/$drive/$rest"
  }
  throw "Unsupported ARCANA Windows path for WSL evidence bridge: $full"
}

function Invoke-WslScript {
  param([Parameter(Mandatory=$true)][string]$Script)
  $psi = [System.Diagnostics.ProcessStartInfo]::new()
  $psi.FileName = $WslExe
  $psi.Arguments = "bash -s"
  $psi.UseShellExecute = $false
  $psi.RedirectStandardInput = $true
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.CreateNoWindow = $true
  $p = [System.Diagnostics.Process]::new()
  $p.StartInfo = $psi
  if (-not $p.Start()) { throw "Could not start governed WSL evidence probe" }
  $p.StandardInput.Write($Script)
  $p.StandardInput.Close()
  $stdout = $p.StandardOutput.ReadToEnd()
  $stderr = $p.StandardError.ReadToEnd()
  $p.WaitForExit()
  [pscustomobject]@{ ExitCode = $p.ExitCode; Stdout = $stdout; Stderr = $stderr }
}

# Resolve an absolute Conda executable inside WSL.  The persisted binding may
# legitimately be the shell name `conda` because provisioning used `bash -lc`;
# this bridge deliberately uses stdin (`bash -s`) to avoid command-line quoting,
# so it must not depend on login-shell initialization.
$CondaCandidateQ = Assert-ShellSafeValue $CondaPath "ARCANA_WSL_CONDA"
$resolveCondaScript = @"
set -e
candidate=$CondaCandidateQ
if command -v "`$candidate" >/dev/null 2>&1; then
  command -v "`$candidate"
  exit 0
fi
if [ -x "`$candidate" ]; then
  printf '%s\n' "`$candidate"
  exit 0
fi
for p in "`$HOME/miniforge3/bin/conda" "`$HOME/mambaforge/bin/conda" "`$HOME/miniconda3/bin/conda" "`$HOME/anaconda3/bin/conda" /opt/conda/bin/conda /opt/miniforge3/bin/conda /opt/miniconda3/bin/conda; do
  if [ -x "`$p" ]; then printf '%s\n' "`$p"; exit 0; fi
done
exit 127
"@
$resolvedConda = Invoke-WslScript $resolveCondaScript
$resolvedCondaLines = @($resolvedConda.Stdout -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
if ($resolvedConda.ExitCode -ne 0 -or $resolvedCondaLines.Count -eq 0) {
  throw "Fresh host runtime evidence bridge could not resolve Conda inside WSL."
}
$CondaPath = ([string]$resolvedCondaLines[0]).Trim()
$CondaQ = Assert-ShellSafeValue $CondaPath "resolved WSL Conda"

function New-EngineEvidence {
  param(
    [string]$Engine,[string]$Expected,[string]$Confirmed,[string]$Invocation,
    [int]$ReturnCode,[string]$Stdout,[string]$Stderr,[bool]$Ready
  )
  [ordered]@{
    engine = $Engine
    expected_version = $Expected
    confirmed_version = if ($Ready) { $Confirmed } else { $null }
    status = if ($Ready) { "READY" } else { "PROBE_FAILED" }
    invocation = $Invocation
    returncode = $ReturnCode
    stdout = $Stdout
    stderr = $Stderr
  }
}

Write-Host "=== R4.0 fresh PowerShell-owned host runtime evidence ==="
Write-Host "WSL: $WslExe"
Write-Host "Conda binding: $CondaPath"

# NEMO 2.4.2
$nemoScript = @"
set -o pipefail
CONDA_EXE=$CondaQ
NEMO_ENV=$NemoQ
"`$CONDA_EXE" run -n "`$NEMO_ENV" bash -lc 'command -v nemo2.4.2' || exit `$?
"`$CONDA_EXE" list -n "`$NEMO_ENV" nemo
"@
$nemo = Invoke-WslScript $nemoScript
$nemoReady = ($nemo.ExitCode -eq 0 -and ($nemo.Stdout -match '(?m)^nemo\s+2\.4\.2\s'))
$eNemo = New-EngineEvidence "NEMO" "2.4.2" "2.4.2" "PowerShell->WSL conda:$NemoEnv/nemo2.4.2" $nemo.ExitCode $nemo.Stdout $nemo.Stderr $nemoReady
Write-Host "NEMO: $($eNemo.status) $($eNemo.confirmed_version)"

# Geonomics 1.4.9
$geoScript = @"
set -e
CONDA_EXE=$CondaQ
GEO_ENV=$GeoQ
"`$CONDA_EXE" run -n "`$GEO_ENV" python -c 'import importlib.metadata as m, geonomics; print(m.version("geonomics"))'
"@
$geo = Invoke-WslScript $geoScript
$geoVersion = (($geo.Stdout -split "`r?`n") | Where-Object { $_ -match '^1\.4\.9$' } | Select-Object -First 1)
$geoReady = ($geo.ExitCode -eq 0 -and $geoVersion -eq '1.4.9')
$eGeo = New-EngineEvidence "Geonomics" "1.4.9" "1.4.9" "PowerShell->WSL conda:$GeonomicsEnv/python" $geo.ExitCode $geo.Stdout $geo.Stderr $geoReady
Write-Host "Geonomics: $($eGeo.status) $($eGeo.confirmed_version)"

# Shared R runtime prefix.
$rPrefixScript = @"
set -e
CONDA_EXE=$CondaQ
R_ENV=$RQ
"`$CONDA_EXE" run -n "`$R_ENV" env | sed -n 's/^CONDA_PREFIX=//p' | head -n 1
"@
$rPrefixResult = Invoke-WslScript $rPrefixScript
$rPrefixLine = @(($rPrefixResult.Stdout -split "`r?`n") | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
$rPrefix = if ($rPrefixLine.Count -gt 0) { ([string]$rPrefixLine[0]).Trim() } else { "" }
if ($rPrefixResult.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($rPrefix)) {
  $rPrefix = ""
}
$rPrefixQ = if ($rPrefix) { Assert-ShellSafeValue $rPrefix "R_CONDA_PREFIX" } else { "''" }

# MadingleyR 1.0.6 + C++ 2.02
$madingleyScript = @"
set -e
CONDA_EXE=$CondaQ
R_ENV=$RQ
R_PREFIX=$rPrefixQ
"`$CONDA_EXE" run -n "`$R_ENV" env LD_LIBRARY_PATH="`$R_PREFIX/lib" Rscript -e 'if(!requireNamespace("MadingleyR",quietly=TRUE)) quit(status=12); library(MadingleyR); cat(as.character(packageVersion("MadingleyR")),"\n"); madingley_version()'
"@
$mad = Invoke-WslScript $madingleyScript
$madReady = ($mad.ExitCode -eq 0 -and $mad.Stdout -match '(?m)^1\.0\.6\s*$' -and $mad.Stdout -match '2\.02')
$eMad = New-EngineEvidence "Madingley" "MadingleyR-1.0.6__CPP-2.02" "MadingleyR-1.0.6__CPP-2.02" "PowerShell->WSL conda:$REnv/Rscript+runtime-libs" $mad.ExitCode $mad.Stdout $mad.Stderr $madReady
Write-Host "Madingley: $($eMad.status) $($eMad.confirmed_version)"

# RangeShiftR 3.0.1
$rangeScript = @"
set -e
CONDA_EXE=$CondaQ
R_ENV=$RQ
R_PREFIX=$rPrefixQ
"`$CONDA_EXE" run -n "`$R_ENV" env LD_LIBRARY_PATH="`$R_PREFIX/lib" Rscript -e 'if(!requireNamespace("RangeShiftR",quietly=TRUE)) quit(status=12); suppressPackageStartupMessages(library(RangeShiftR)); cat(as.character(packageVersion("RangeShiftR")),"\n")'
"@
$range = Invoke-WslScript $rangeScript
$rangeReady = ($range.ExitCode -eq 0 -and $range.Stdout -match '(?m)^3\.0\.1\s*$')
$eRange = New-EngineEvidence "RangeShifter" "3.0.1" "3.0.1" "PowerShell->WSL conda:$REnv/RangeShiftR" $range.ExitCode $range.Stdout $range.Stderr $rangeReady
Write-Host "RangeShifter: $($eRange.status) $($eRange.confirmed_version)"

# CDMetaPOP 3.08 source + Python 3.8 runtime.
$CdRootWindows = if ($env:ARCANA_CDMETAPOP_ROOT) { $env:ARCANA_CDMETAPOP_ROOT } else { Join-Path $Root '.arcana_engines\CDMetaPOP-3.08' }
$CdRootWsl = Convert-ArcanaWindowsPathToWsl $CdRootWindows
$CdRootQ = Assert-ShellSafeValue $CdRootWsl "ARCANA_CDMETAPOP_ROOT"
$cdScript = @"
set -e
CONDA_EXE=$CondaQ
CD_ENV=$CdQ
CD_ROOT=$CdRootQ
commit=`$("`$CONDA_EXE" run -n "`$CD_ENV" git -C "`$CD_ROOT" rev-parse HEAD)
"`$CONDA_EXE" run -n "`$CD_ENV" python -c 'import sys,numpy,scipy; print(sys.version.split()[0]); print(numpy.__version__); print(scipy.__version__)'
echo "COMMIT=`$commit"
"@
$cd = Invoke-WslScript $cdScript
$cdCommit = '3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118'
$cdReady = ($cd.ExitCode -eq 0 -and $cd.Stdout -match '(?m)^3\.8\.' -and $cd.Stdout -match "COMMIT=$cdCommit")
$eCd = New-EngineEvidence "CDMetaPOP" "3.08" "3.08" "PowerShell->WSL conda:$CDMetaPOPEnv + source:$CdRootWsl@$cdCommit" $cd.ExitCode $cd.Stdout $cd.Stderr $cdReady
Write-Host "CDMetaPOP: $($eCd.status) $($eCd.confirmed_version)"

# SLiM 5.2 + required tree-sequence stack.
$slimScript = @"
set -e
CONDA_EXE=$CondaQ
SLIM_ENV=$SlimQ
"`$CONDA_EXE" run -n "`$SLIM_ENV" slim -v
"`$CONDA_EXE" run -n "`$SLIM_ENV" python -c 'import tskit,msprime,pyslim; print("tskit="+tskit.__version__); print("msprime="+msprime.__version__); print("pyslim="+pyslim.__version__)'
"@
$slim = Invoke-WslScript $slimScript
# Use explicit semantic minimum checks for the tree-sequence dependencies.
function Test-VersionAtLeast([string]$Found,[string]$Minimum) {
  try { return ([version]$Found -ge [version]$Minimum) } catch { return $false }
}
$tskitV = [regex]::Match($slim.Stdout,'tskit=([0-9.]+)').Groups[1].Value
$msprimeV = [regex]::Match($slim.Stdout,'msprime=([0-9.]+)').Groups[1].Value
$pyslimV = [regex]::Match($slim.Stdout,'pyslim=([0-9.]+)').Groups[1].Value
$slimReady = ($slim.ExitCode -eq 0 -and $slim.Stdout -match 'SLiM version 5\.2' -and (Test-VersionAtLeast $tskitV '1.0.2') -and (Test-VersionAtLeast $msprimeV '1.4.1') -and (Test-VersionAtLeast $pyslimV '1.1.1'))
$eSlim = New-EngineEvidence "SLiM" "5.2" "5.2" "PowerShell->WSL conda:$SlimEnv/slim+python" $slim.ExitCode $slim.Stdout $slim.Stderr $slimReady
Write-Host "SLiM: $($eSlim.status) $($eSlim.confirmed_version) (tskit=$tskitV msprime=$msprimeV pyslim=$pyslimV)"

$engines = @($eNemo,$eGeo,$eMad,$eRange,$eCd,$eSlim)
$ready = @($engines | Where-Object { $_.status -eq 'READY' } | ForEach-Object { $_.engine })
$result = [ordered]@{
  stage = 'v0.6D1-R4.0'
  evidence_type = 'HOST_RUNTIME_IDENTITY_EVIDENCE'
  generated_by = 'capture_v0_6D1_R4_0_runtime_evidence.ps1'
  generated_at_utc = [DateTime]::UtcNow.ToString('o')
  root = $Root
  wsl_executable = $WslExe
  conda_binding = $CondaPath
  all_required_engines_ready = ($ready.Count -eq 6)
  ready_engines = @($ready | Sort-Object)
  engines = $engines
}
$outDir = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $OutputPath
Write-Host "Host runtime evidence: $OutputPath"
Write-Host "Ready engines: $($ready.Count)/6"
if ($ready.Count -ne 6) { exit 3 }
exit 0
