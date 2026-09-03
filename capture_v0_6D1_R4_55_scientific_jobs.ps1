param(
  [string]$Python = "python",
  [string]$RuntimeIdentityEvidence = "",
  [switch]$NoResume
)

$ErrorActionPreference = "Stop"
$Root = (Get-Location).Path
$env:PYTHONPATH = Join-Path $Root "src"

if ([string]::IsNullOrWhiteSpace($RuntimeIdentityEvidence)) {
  $RuntimeIdentityEvidence = Join-Path $Root "outputs\v0_6D1_R4_55\R4_55_RUNTIME_IDENTITY_EVIDENCE.json"
}

$ManifestPath = Join-Path $Root "outputs\v0_6D1_R4_55\R4_55_EXECUTION_MANIFEST.json"
$Manifest = Get-Content -Raw $ManifestPath | ConvertFrom-Json
$Runtime = Get-Content -Raw $RuntimeIdentityEvidence | ConvertFrom-Json

if (-not $Runtime.all_required_engines_ready) {
  throw "R4.55 requires fresh READY runtime evidence"
}

$WslExe = [string]$Runtime.wsl_executable
$CondaPath = [string]$Runtime.conda_binding

if ([string]::IsNullOrWhiteSpace($WslExe) -or -not (Test-Path $WslExe)) {
  throw "invalid WSL binding"
}

$CondaBasePython = $CondaPath -replace '/bin/conda$', '/bin/python'
if ($CondaBasePython -eq $CondaPath) {
  throw "cannot derive governed Conda base Python"
}

function Convert-WslPath([string]$Path) {
  $full = [IO.Path]::GetFullPath($Path)
  if ($full -match '^([A-Za-z]):\\(.*)$') {
    return "/mnt/$($Matches[1].ToLowerInvariant())/$($Matches[2] -replace '\\','/')"
  }
  throw "unsupported path $full"
}

function Quote-Bash([string]$Value, [string]$Name) {
  if ($Value.Contains("'")) {
    throw "$Name unsafe"
  }
  return "'$Value'"
}

function Invoke-WslScript(
  [string]$Script,
  [string]$Label,
  [int]$TimeoutSeconds = 3600
) {
  $psi = [Diagnostics.ProcessStartInfo]::new()
  $psi.FileName = $WslExe
  $psi.Arguments = "bash -s"
  $psi.UseShellExecute = $false
  $psi.RedirectStandardInput = $true
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.CreateNoWindow = $true

  $proc = [Diagnostics.Process]::new()
  $proc.StartInfo = $psi

  if (-not $proc.Start()) {
    throw "WSL start failed for $Label"
  }

  $stdoutTask = $proc.StandardOutput.ReadToEndAsync()
  $stderrTask = $proc.StandardError.ReadToEndAsync()
  $proc.StandardInput.Write($Script)
  $proc.StandardInput.Close()

  $sw = [Diagnostics.Stopwatch]::StartNew()
  $timedOut = $false

  while (-not $proc.WaitForExit(1000)) {
    if ($sw.Elapsed.TotalSeconds -ge $TimeoutSeconds) {
      $timedOut = $true
      try {
        $proc.Kill($true)
      } catch {
        try {
          $proc.Kill()
        } catch {
        }
      }
      break
    }
  }

  if ($timedOut) {
    $proc.WaitForExit()
  }

  return [pscustomobject]@{
    ExitCode = if ($timedOut) { 124 } else { $proc.ExitCode }
    Stdout = $stdoutTask.GetAwaiter().GetResult()
    Stderr = $stderrTask.GetAwaiter().GetResult()
    TimedOut = $timedOut
  }
}

function Archive-Partial([string]$JobId, [string]$JobDir) {
  if (-not (Test-Path $JobDir)) {
    return
  }

  $history = Join-Path $Root "outputs\v0_6D1_R4_55\repair_history"
  New-Item -ItemType Directory -Force -Path $history | Out-Null

  $index = 0
  do {
    $destination = Join-Path $history ("PARTIAL_" + $JobId + "_" + ("{0:D3}" -f $index))
    $index++
  } while (Test-Path $destination)

  Move-Item -Force -Path $JobDir -Destination $destination
  Write-Host "Archived partial: $destination"
}

function Write-BridgeFailure(
  [string]$RawPath,
  [object]$Job,
  [object]$Execution
) {
  $obj = [ordered]@{
    stage = "v0.6D1-R4.55"
    job_id = [string]$Job.job_id
    engine = [string]$Job.engine
    adapter_status = "ENGINE_EXECUTION_FAILURE"
    replicates = @()
    bridge_returncode = [int]$Execution.ExitCode
    timed_out = [bool]$Execution.TimedOut
    stdout_tail = [string]$Execution.Stdout
    stderr_tail = [string]$Execution.Stderr
    error = "Authorized adapter produced no RAW_ENGINE_EVIDENCE.json"
    canonical_write = $false
  }
  $obj | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -Path $RawPath
}

$RootQ = Quote-Bash (Convert-WslPath $Root) "root"
$CondaQ = Quote-Bash $CondaPath "conda"
$BasePyQ = Quote-Bash $CondaBasePython "basepy"

$REnv = if ($env:ARCANA_R40_R_CONDA_ENV) {
  $env:ARCANA_R40_R_CONDA_ENV
} else {
  "arcana-r40-r"
}

$NemoEnv = if ($env:ARCANA_NEMO_CONDA_ENV) {
  $env:ARCANA_NEMO_CONDA_ENV
} else {
  "arcana-nemo242"
}

$CdEnv = if ($env:ARCANA_CDMETAPOP_CONDA_ENV) {
  $env:ARCANA_CDMETAPOP_CONDA_ENV
} else {
  "arcana-cdmetapop-308"
}

$SlimEnv = if ($env:ARCANA_SLIM_CONDA_ENV) {
  $env:ARCANA_SLIM_CONDA_ENV
} else {
  "arcana-slim52"
}

$CdRoot = if ($env:ARCANA_CDMETAPOP_ROOT) {
  $env:ARCANA_CDMETAPOP_ROOT
} else {
  Join-Path $Root ".arcana_engines\CDMetaPOP-3.08"
}
$CdRootQ = Quote-Bash (Convert-WslPath $CdRoot) "cdroot"

$jobs = @($Manifest.jobs)
$jobIndex = 0

foreach ($job in $jobs) {
  $jobIndex++
  $jobId = [string]$job.job_id
  $engine = [string]$job.engine
  $jobDir = Join-Path $Root ("outputs\v0_6D1_R4_55\jobs\" + $jobId)

  if (-not $NoResume) {
    & $Python ".\scripts\check_v0_6D1_R4_55_job_resume.py" --job-id $jobId | Out-Null
    $resumeStatus = $LASTEXITCODE

    if ($resumeStatus -eq 0) {
      Write-Host "[$jobIndex/$($jobs.Count)] $jobId / $engine -- RESUME VALID, SKIP"
      continue
    } elseif ($resumeStatus -eq 11) {
      Archive-Partial $jobId $jobDir
    } elseif ($resumeStatus -eq 12) {
      Write-Host "R4.55 BLOCKED: completed evidence exists but fails resume integrity for $jobId"
      exit 12
    }
  } elseif (Test-Path $jobDir) {
    Archive-Partial $jobId $jobDir
  }

  New-Item -ItemType Directory -Force -Path $jobDir | Out-Null

  $rawPath = Join-Path $jobDir "RAW_ENGINE_EVIDENCE.json"
  $stdoutPath = Join-Path $jobDir "STDOUT.log"
  $stderrPath = Join-Path $jobDir "STDERR.log"
  $workDir = Join-Path $jobDir "runtime_work"
  New-Item -ItemType Directory -Force -Path $workDir | Out-Null

  $contractPath = Join-Path $Root ([string]$job.contract_path)
  $contractQ = Quote-Bash (Convert-WslPath $contractPath) "contract"
  $rawQ = Quote-Bash (Convert-WslPath $rawPath) "raw"
  $workQ = Quote-Bash (Convert-WslPath $workDir) "work"

  Write-Host "[$jobIndex/$($jobs.Count)] $jobId / $engine -- SCIENTIFIC EXECUTION"

  switch ($engine) {
    "Madingley" {
      $configPath = Join-Path $Root ([string]$job.engine_config_path)
      $configQ = Quote-Bash (Convert-WslPath $configPath) "config"
      $script = "set -euo pipefail`nCONDA_EXE=$CondaQ`n`"`$CONDA_EXE`" run -n '$REnv' bash $RootQ/benchmarks/r41/run_r_with_conda_libs.sh $RootQ/benchmarks/r43/madingley_r43.R $configQ $rawQ $workQ"
      $timeout = 3600
    }

    "RangeShifter" {
      $configPath = Join-Path $Root ([string]$job.engine_config_path)
      $configQ = Quote-Bash (Convert-WslPath $configPath) "config"
      $script = "set -euo pipefail`nCONDA_EXE=$CondaQ`n`"`$CONDA_EXE`" run -n '$REnv' bash $RootQ/benchmarks/r41/run_r_with_conda_libs.sh $RootQ/benchmarks/r43/rangeshiftr_r43.R $configQ $rawQ $workQ"
      $timeout = 3600
    }

    "NEMO" {
      $script = "set -euo pipefail`nCONDA_EXE=$CondaQ`n`"`$CONDA_EXE`" run -n '$NemoEnv' $BasePyQ $RootQ/benchmarks/r421/nemo_r421.py $contractQ $rawQ $workQ"
      $timeout = 3600
    }

    "SLiM" {
      $script = "set -euo pipefail`nCONDA_EXE=$CondaQ`n`"`$CONDA_EXE`" run -n '$SlimEnv' python $RootQ/benchmarks/r421/slim_r421.py $contractQ $rawQ $workQ"
      $timeout = 3600
    }

    "CDMetaPOP" {
      $profilePath = Join-Path $Root ([string]$job.repair_profile_path)
      $profileQ = Quote-Bash (Convert-WslPath $profilePath) "profile"
      $script = "set -euo pipefail`nCONDA_EXE=$CondaQ`n`"`$CONDA_EXE`" run -n '$CdEnv' python $RootQ/benchmarks/r421/cdmetapop_r421_matched.py $contractQ $profileQ $rawQ $workQ $CdRootQ"
      $timeout = 5400
    }

    default {
      throw "unauthorized engine $engine"
    }
  }

  $execution = Invoke-WslScript $script $jobId $timeout

  Set-Content -Encoding UTF8 -Path $stdoutPath -Value ([string]$execution.Stdout)
  Set-Content -Encoding UTF8 -Path $stderrPath -Value ([string]$execution.Stderr)

  if (-not (Test-Path $rawPath)) {
    Write-BridgeFailure $rawPath $job $execution
  }

  if ($execution.ExitCode -ne 0) {
    Write-Host "R4.55 BLOCKED: $jobId rc=$($execution.ExitCode). Prior jobs remain resumable."
    exit $execution.ExitCode
  }

  if ($engine -eq "SLiM") {
    $extractScript = "set -euo pipefail`nCONDA_EXE=$CondaQ`ncd $RootQ`nPYTHONPATH=$RootQ/src `"`$CONDA_EXE`" run -n '$SlimEnv' python $RootQ/scripts/extract_v0_6D1_R4_55_job.py --job-id '$jobId' --slim"
    $extractExecution = Invoke-WslScript $extractScript ($jobId + "_extract") 1800

    Add-Content -Encoding UTF8 -Path $stdoutPath -Value ([string]$extractExecution.Stdout)
    Add-Content -Encoding UTF8 -Path $stderrPath -Value ([string]$extractExecution.Stderr)

    if ($extractExecution.ExitCode -ne 0) {
      exit $extractExecution.ExitCode
    }
  } else {
    & $Python ".\scripts\extract_v0_6D1_R4_55_job.py" --job-id $jobId
    if ($LASTEXITCODE -ne 0) {
      exit $LASTEXITCODE
    }
  }
}

Write-Host "PASS_R455_ALL_20_JOBS_80_STREAMS_EXECUTION_AND_JOB_EVIDENCE_CAPTURE"
