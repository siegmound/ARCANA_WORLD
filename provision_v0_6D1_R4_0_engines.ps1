param(
  [switch]$ForceReinstall,
  [string]$NemoEnv = "arcana-nemo242",
  [string]$GeonomicsEnv = "arcana-geonomics-149",
  [string]$REnv = "arcana-r40-r",
  [string]$CDMetaPOPEnv = "arcana-cdmetapop-308",
  [string]$SlimEnv = "arcana-slim52"
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Invoke-WslBash {
  param([Parameter(Mandatory=$true)][string]$Command, [switch]$AllowFailure)
  & wsl.exe bash -lc $Command
  $code = $LASTEXITCODE
  if (-not $AllowFailure -and $code -ne 0) { throw "WSL command failed ($code): $Command" }
  return $code
}

function Invoke-WslCaptureFirstLine {
  param([Parameter(Mandatory=$true)][string]$Command)
  # Always materialize stdout as an array.  A command with no stdout therefore
  # becomes @() rather than $null, avoiding `.Trim()` on a null expression.
  $lines = @(& wsl.exe bash -lc $Command 2>$null)
  $code = $LASTEXITCODE
  $first = $null
  foreach ($line in $lines) {
    if ($null -eq $line) { continue }
    $text = [string]$line
    if (-not [string]::IsNullOrWhiteSpace($text)) {
      $first = $text.Trim()
      break
    }
  }
  [pscustomobject]@{ ExitCode = $code; FirstLine = $first; Lines = $lines }
}

function Convert-ArcanaWindowsPathToWsl {
  param([Parameter(Mandatory=$true)][string]$Path)
  # Do not depend on `wslpath` for a path we already know is a Windows drive
  # path.  This also removes a second possible null-output `.Trim()` failure.
  $full = [System.IO.Path]::GetFullPath($Path)
  if ($full -match '^([A-Za-z]):\\(.*)$') {
    $drive = $Matches[1].ToLowerInvariant()
    $rest = $Matches[2] -replace '\\','/'
    return "/mnt/$drive/$rest"
  }
  throw "R4.0 governed WSL provisioning requires a Windows drive path; unsupported ARCANA root: $full"
}

Write-Host "=== R4.0 provisioning preflight ==="
& wsl.exe bash -lc "uname -a"
if ($LASTEXITCODE -ne 0) { throw "WSL2 is required for the governed R4.0 provisioning path." }

$FindConda = @'
set +e
if command -v conda >/dev/null 2>&1; then
  command -v conda
  exit 0
fi
for p in \
  "$HOME/miniforge3/bin/conda" \
  "$HOME/mambaforge/bin/conda" \
  "$HOME/miniconda3/bin/conda" \
  "$HOME/anaconda3/bin/conda" \
  "$HOME/miniforge/bin/conda" \
  "$HOME/miniconda/bin/conda" \
  "/opt/conda/bin/conda" \
  "/opt/miniforge3/bin/conda" \
  "/opt/miniconda3/bin/conda"; do
  if [ -x "$p" ]; then
    printf '%s\n' "$p"
    exit 0
  fi
done
# Historical ARCANA NEMO environments may live under a Conda installation
# that is no longer exported by the login shell.  Search only a few governed
# roots and stop at the first executable rather than scanning the whole WSL fs.
for base in "$HOME" /opt /usr/local; do
  [ -d "$base" ] || continue
  found="$(find "$base" -maxdepth 6 -type f -path '*/bin/conda' -print -quit 2>/dev/null)"
  if [ -n "$found" ] && [ -x "$found" ]; then
    printf '%s\n' "$found"
    exit 0
  fi
done
exit 127
'@
$CondaProbe = Invoke-WslCaptureFirstLine $FindConda
$CondaPath = $CondaProbe.FirstLine
if ($CondaProbe.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($CondaPath)) {
  throw @"
Conda was not found inside WSL after checking the login PATH, common
Miniforge/Miniconda/Anaconda locations, and a bounded search under HOME,/opt,/usr/local.
The previous NEMO setup used WSL Conda.  Run this diagnostic and paste the output:
  wsl bash -lc 'echo HOME=`$HOME; command -v conda || true; find `$HOME /opt /usr/local -maxdepth 6 -type f -path "*/bin/conda" -print 2>/dev/null | head -20'
"@
}
Write-Host "WSL Conda: $CondaPath"
$WslExePath = (Get-Command wsl.exe -ErrorAction Stop).Source
Write-Host "WSL executable binding: $WslExePath"

function Conda-EnvExists([string]$EnvName) {
  # Do not parse `conda env list`: shell formatting/function wrappers can make
  # name-column parsing unreliable under WSL login shells.  `conda run` is the
  # authoritative test that a named environment exists and is runnable.
  $cmd = "'$CondaPath' run -n '$EnvName' /bin/true >/dev/null 2>&1"
  & wsl.exe bash -lc $cmd | Out-Null
  return ($LASTEXITCODE -eq 0)
}

function Test-CondaRun {
  param([string]$EnvName, [string]$Command)
  & wsl.exe bash -lc "'$CondaPath' run -n '$EnvName' $Command >/dev/null 2>&1" | Out-Null
  return ($LASTEXITCODE -eq 0)
}
function Ensure-CondaEnv {
  param([string]$EnvName, [string]$CreateArgs)
  if ($ForceReinstall -and (Conda-EnvExists $EnvName)) {
    Write-Host "Removing existing env $EnvName"
    Invoke-WslBash "'$CondaPath' env remove -y -n '$EnvName'"
  }
  if (-not (Conda-EnvExists $EnvName)) {
    Write-Host "Creating env $EnvName"
    Invoke-WslBash "'$CondaPath' create -y -n '$EnvName' $CreateArgs"
  } else {
    Write-Host "Reusing env $EnvName"
  }
}
function Conda-Run {
  param([string]$EnvName, [string]$Command)
  Invoke-WslBash "'$CondaPath' run -n '$EnvName' $Command"
}

# 1) NEMO 2.4.2 — reuse the exact governed env from R3.6D when present.
Write-Host "`n=== NEMO 2.4.2 ==="
Ensure-CondaEnv $NemoEnv "-c conda-forge -c ecoevo nemo=2.4.2"
Write-Host "Validating NEMO executable and package pin"
Conda-Run $NemoEnv "bash -lc 'command -v nemo2.4.2'"
Invoke-WslBash "'$CondaPath' list -n '$NemoEnv' nemo | tail -n +3"

# 2) Geonomics 1.4.9 — isolated landscape-genomics environment.
Write-Host "`n=== Geonomics 1.4.9 ==="
Ensure-CondaEnv $GeonomicsEnv "-c conda-forge python=3.11 pip numpy matplotlib pandas geopandas scipy scikit-learn statsmodels shapely bitarray rasterio msprime tskit psutil"
$GeonomicsVersionProbe = @'
python -c "import importlib.metadata as m, geonomics; raise SystemExit(0 if m.version('geonomics') == '1.4.9' else 9)"
'@
$GeonomicsVersionPrint = @'
python -c "import importlib.metadata as m, geonomics; print(m.version('geonomics'))"
'@
if (-not (Test-CondaRun $GeonomicsEnv $GeonomicsVersionProbe.Trim())) {
  Write-Host "Installing Geonomics 1.4.9 into $GeonomicsEnv"
  Conda-Run $GeonomicsEnv "python -m pip install --upgrade pip"
  Conda-Run $GeonomicsEnv "python -m pip install 'PyVCF3>=1.0.3' 'geonomics==1.4.9'"
} else {
  Write-Host "Geonomics 1.4.9 already present; skipping pip reinstall"
}
Conda-Run $GeonomicsEnv $GeonomicsVersionPrint.Trim()

# 3+4) R ecosystem: MadingleyR and RangeShiftR share one isolated R runtime.
Write-Host "`n=== R runtime: MadingleyR + RangeShiftR ==="
Ensure-CondaEnv $REnv "-c conda-forge r-base=4.5 r-remotes r-pak r-terra r-sf r-data.table r-rcpp r-codetools cxx-compiler make cmake pkg-config git"

# MadingleyR bundles a C++ executable. Under `conda run`, that child process
# does not reliably inherit a linker search path that includes the Conda env
# libraries on WSL. Resolve the environment prefix once and explicitly expose
# its lib directory to all governed R runtime probes.
$RPrefixProbe = Invoke-WslCaptureFirstLine "'$CondaPath' run -n '$REnv' env"
if ($RPrefixProbe.ExitCode -ne 0) {
  throw "Could not inspect governed R environment $REnv"
}
$RPrefixLine = @($RPrefixProbe.Lines | ForEach-Object { [string]$_ } | Where-Object { $_ -like 'CONDA_PREFIX=*' } | Select-Object -First 1)
if ($RPrefixLine.Count -eq 0) {
  throw "Could not resolve CONDA_PREFIX for governed R environment $REnv from conda run env"
}
$RPrefix = ([string]$RPrefixLine[0]).Substring('CONDA_PREFIX='.Length).Trim()
if ([string]::IsNullOrWhiteSpace($RPrefix)) {
  throw "Resolved empty CONDA_PREFIX for governed R environment $REnv"
}
$RLibPath = "$RPrefix/lib"
Write-Host "R runtime library path: $RLibPath"
& wsl.exe bash -lc "test -r '$RLibPath/libgomp.so.1'" | Out-Null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Installing/repairing libgomp in $REnv"
  Invoke-WslBash "'$CondaPath' install -y -n '$REnv' -c conda-forge libgomp"
}
& wsl.exe bash -lc "'$CondaPath' list -n '$REnv' r-codetools | grep -q '^r-codetools[[:space:]]'" | Out-Null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Installing recommended R codetools package"
  Invoke-WslBash "'$CondaPath' install -y -n '$REnv' -c conda-forge r-codetools"
}

function Conda-RunR {
  param([string]$EnvName, [string]$RCommand)
  # Explicitly pass the Conda runtime libraries to bundled/native child
  # executables launched from R (notably Madingley C++ -> libgomp.so.1).
  Conda-Run $EnvName "env LD_LIBRARY_PATH='$RLibPath' $RCommand"
}
# MadingleyR official installation route; vignette build disabled to avoid irrelevant documentation dependencies.
$MadingleyInstall = @'
Rscript -e "if(!requireNamespace('remotes',quietly=TRUE)) install.packages('remotes',repos='https://cloud.r-project.org'); remotes::install_github('MadingleyR/MadingleyR', subdir='Package', build_vignettes=FALSE, upgrade='never', force=TRUE)"
'@
$MadingleyCheck = @'
Rscript -e "if(!requireNamespace('MadingleyR',quietly=TRUE)) quit(status=12); library(MadingleyR); print(packageVersion('MadingleyR')); madingley_version()"
'@
$MadingleyVersionProbe = @'
Rscript -e "if(!requireNamespace('MadingleyR',quietly=TRUE)) quit(status=12); quit(status=ifelse(as.character(packageVersion('MadingleyR'))=='1.0.6',0,13))"
'@
Write-Host "Checking MadingleyR 1.0.6 / C++ 2.02"
if (-not (Test-CondaRun $REnv $MadingleyVersionProbe.Trim())) {
  Write-Host "Installing MadingleyR from governed upstream route"
  Conda-Run $REnv $MadingleyInstall.Trim()
} else {
  Write-Host "MadingleyR 1.0.6 already present; skipping reinstall"
}
Conda-RunR $REnv $MadingleyCheck.Trim()

# RangeShiftR official installation route. R4.0 will record the exact packageVersion returned.
$RangeInstall = @'
Rscript -e "if(!requireNamespace('pak',quietly=TRUE)) install.packages('pak',repos='https://cloud.r-project.org'); pak::pak('RangeShifter/RangeShiftR-pkg/RangeShiftR@d01f1b6')"
'@
$RangeCheck = @'
Rscript -e "if(!requireNamespace('RangeShiftR',quietly=TRUE)) quit(status=12); library(RangeShiftR); print(packageVersion('RangeShiftR'))"
'@
$RangeShiftRVersionProbe = @'
Rscript -e "if(!requireNamespace('RangeShiftR',quietly=TRUE)) quit(status=12); quit(status=ifelse(as.character(packageVersion('RangeShiftR'))=='3.0.1',0,13))"
'@
Write-Host "Checking RangeShiftR 3.0.1"
if (-not (Test-CondaRun $REnv $RangeShiftRVersionProbe.Trim())) {
  Write-Host "Installing RangeShiftR 3.0.1 from frozen official RangeShifter commit d01f1b6"
  Conda-Run $REnv $RangeInstall.Trim()
} else {
  Write-Host "RangeShiftR 3.0.1 already present; skipping reinstall"
}
Conda-RunR $REnv $RangeCheck.Trim()

# 5) CDMetaPOP 3.08 — exact released source commit + Python 3.8 runtime.
Write-Host "`n=== CDMetaPOP 3.08 ==="
Ensure-CondaEnv $CDMetaPOPEnv "-c conda-forge python=3.8 numpy scipy pandas git"
$WslRoot = Convert-ArcanaWindowsPathToWsl $Root
if ([string]::IsNullOrWhiteSpace($WslRoot)) { throw "Could not translate ARCANA root to WSL path." }
$CdRoot = "$WslRoot/.arcana_engines/CDMetaPOP-3.08"
$CdCommit = "3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118"
$CdCmd = @"
mkdir -p '$WslRoot/.arcana_engines'
if [ ! -d '$CdRoot/.git' ]; then
  '$CondaPath' run -n '$CDMetaPOPEnv' git clone https://github.com/ComputationalEcologyLab/CDMetaPOP.git '$CdRoot'
fi
cd '$CdRoot'
'$CondaPath' run -n '$CDMetaPOPEnv' git fetch --all --tags
'$CondaPath' run -n '$CDMetaPOPEnv' git checkout --detach '$CdCommit'
printf 'CDMetaPOP commit: '; '$CondaPath' run -n '$CDMetaPOPEnv' git rev-parse HEAD
"@
Invoke-WslBash $CdCmd
Conda-Run $CDMetaPOPEnv "python -c 'import sys,numpy,scipy; print(sys.version.split()[0]); print(numpy.__version__); print(scipy.__version__)'"

# 6) SLiM 5.2 + tree-sequence toolchain.
Write-Host "`n=== SLiM 5.2 + tskit/msprime/pyslim ==="
Ensure-CondaEnv $SlimEnv "-c conda-forge python=3.11 slim=5.2 'tskit>=1.0.2' 'msprime>=1.4.1' 'pyslim>=1.1.1'"
Conda-Run $SlimEnv "slim -v"
Conda-Run $SlimEnv "python -c 'import tskit,msprime,pyslim; print(tskit.__version__); print(msprime.__version__); print(pyslim.__version__)'"

# Write local environment selectors; they are optional because R4.0 probes these standard names automatically.
$EnvFile = Join-Path $Root "set_r40_engine_env.local.ps1"
@"
`$env:ARCANA_WSL_EXE = "$WslExePath"
`$env:ARCANA_WSL_CONDA = "$CondaPath"
`$env:ARCANA_NEMO_CONDA_ENV = "$NemoEnv"
`$env:ARCANA_GEONOMICS_CONDA_ENV = "$GeonomicsEnv"
`$env:ARCANA_R40_R_CONDA_ENV = "$REnv"
`$env:ARCANA_CDMETAPOP_CONDA_ENV = "$CDMetaPOPEnv"
`$env:ARCANA_CDMETAPOP_ROOT = "$(Join-Path $Root '.arcana_engines\CDMetaPOP-3.08')"
`$env:ARCANA_SLIM_CONDA_ENV = "$SlimEnv"
"@ | Set-Content -Encoding UTF8 $EnvFile

Write-Host "`n=== Provisioning complete; running R4.0 inventory/seal ==="
. $EnvFile
& "$Root\run_v0_6D1_R4_0.ps1"
exit $LASTEXITCODE
