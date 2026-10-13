param(
  [Parameter(Mandatory=$true)][ValidateSet("SelfTest","ProviderAudit","Run")][string]$Mode,
  [string]$PythonPath = "C:\Users\jose_\AppData\Local\Programs\Python\Python312\python.exe",
  [string]$RepositoryRoot = ".",
  [string]$OutputRelative = "outputs/r6_functional_development/INT0B_TF2B_5_11_R2_20261013_03",
  [string]$EvidenceDirectory = "outputs/r6_functional_development/INT0B_R2_SUPERVISION_20261013",
  [string]$ExpectedHead = ""
)
. "C:\Users\jose_\AppData\Local\ARCANA\r6-env.ps1"
$ErrorActionPreference = "Stop"
if ($PSVersionTable.PSVersion.Major -lt 7) { throw "POWERSHELL_7_REQUIRED_FOR_PROCESSSTARTINFO_ENVIRONMENT" }
$RepositoryRoot = (Resolve-Path -LiteralPath $RepositoryRoot).Path
Set-Location -LiteralPath $RepositoryRoot
if (-not (Test-Path -LiteralPath (Join-Path $RepositoryRoot "AGENTS.md"))) { throw "REPOSITORY_ROOT_INVALID" }
Add-Type -TypeDefinition @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public static class WinProcessTreeProbe {
  const uint TH32CS_SNAPPROCESS = 0x00000002;
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  struct PROCESSENTRY32 { public uint dwSize; public uint cntUsage; public uint th32ProcessID; public UIntPtr th32DefaultHeapID; public uint th32ModuleID; public uint cntThreads; public uint th32ParentProcessID; public int pcPriClassBase; public uint dwFlags; [MarshalAs(UnmanagedType.ByValTStr, SizeConst=260)] public string szExeFile; }
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr CreateToolhelp32Snapshot(uint flags, uint pid);
  [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool Process32FirstW(IntPtr snap, ref PROCESSENTRY32 entry);
  [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool Process32NextW(IntPtr snap, ref PROCESSENTRY32 entry);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool CloseHandle(IntPtr handle);
  public static int[] DescendantsAndRoot(int root) {
    IntPtr snap=CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS,0);
    if(snap==new IntPtr(-1)) throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
    try { var parent=new Dictionary<int,int>(); var entry=new PROCESSENTRY32(); entry.dwSize=(uint)Marshal.SizeOf(typeof(PROCESSENTRY32)); if(!Process32FirstW(snap,ref entry)) throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error()); do { parent[(int)entry.th32ProcessID]=(int)entry.th32ParentProcessID; } while(Process32NextW(snap,ref entry)); var found=new List<int>(); found.Add(root); for(int i=0;i<found.Count;i++) { int p=found[i]; foreach(var kv in parent) if(kv.Value==p && !found.Contains(kv.Key)) found.Add(kv.Key); } return found.ToArray(); } finally { CloseHandle(snap); }
  }
}
"@
function Get-TreeSnapshot([int]$RootPid) {
  $items = @()
  $ids = [WinProcessTreeProbe]::DescendantsAndRoot($RootPid)
  foreach ($id in $ids) {
    try {
      $p = [Diagnostics.Process]::GetProcessById($id)
      if ($p.HasExited) { continue }
      $items += [pscustomobject]@{
        pid = $id
        image = $p.ProcessName
        executable = $p.MainModule.FileName
        start_time_utc = $p.StartTime.ToUniversalTime().ToString("o")
        working_set_bytes = [int64]$p.WorkingSet64
      }
    } catch [System.ArgumentException] { }
  }
  return ,$items
}
function Get-TreeWorkingSet($Items) {
  $total = [int64]0
  foreach ($item in $Items) { $value = [int64]$item.working_set_bytes; if ($value -gt ([long]::MaxValue - $total)) { throw "MONITOR_WORKING_SET_SUM_OVERFLOW" }; $total += $value }
  return $total
}
function Get-OutputBytes([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return [int64]0 }
  $total = [int64]0
  foreach ($file in Get-ChildItem -LiteralPath $Path -File -Recurse -Force -ErrorAction Stop) {
    $value = [int64]$file.Length; if ($value -gt ([long]::MaxValue - $total)) { throw "MONITOR_OUTPUT_SUM_OVERFLOW" }; $total += $value
  }
  return $total
}
function Invoke-Monitored([string]$Label, [string[]]$CommandArguments, [string]$OutputPath,
                          [string]$TracePath, [double]$WallSeconds, [int64]$WorkingSetLimit,
                          [int64]$OutputLimit, [int]$PollMilliseconds = 100,
                          [switch]$TestOnlyRetainGitObjectEnvironment) {
  $psi = [Diagnostics.ProcessStartInfo]::new()
  $psi.FileName = [IO.Path]::GetFullPath($PythonPath)
  $psi.WorkingDirectory = (Get-Location).Path
  $psi.UseShellExecute = $false
  foreach ($argument in $CommandArguments) { $psi.ArgumentList.Add([string]$argument) }
  $removedGitVariables = @()
  if (-not $TestOnlyRetainGitObjectEnvironment) {
    foreach ($name in @("GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES")) {
      if ($psi.Environment.ContainsKey($name)) { [void]$psi.Environment.Remove($name); $removedGitVariables += $name }
    }
  }
  # Final child-environment mutation: preserve runtime variables, remove only proven corruptors.
  $proc = [Diagnostics.Process]::new()
  $proc.StartInfo = $psi
  if (-not $proc.Start()) { throw "SUPERVISOR_PROCESS_START_FAILED" }
  $root = $proc.Id
  $clock = [Diagnostics.Stopwatch]::StartNew()
  $peakWs = [int64]0
  $peakOutput = [int64]0
  $sampleCount = 0
  $lastItems = @()
  $stopReason = "NATURAL_EXIT"
  $trace = [IO.StreamWriter]::new([IO.Path]::GetFullPath($TracePath), $false, [Text.UTF8Encoding]::new($false))
  $trace.AutoFlush = $true
  try {
    while (-not $proc.HasExited) {
      $items = Get-TreeSnapshot $root
      if (-not ($items | Where-Object pid -eq $root)) {
        $stopReason = "MONITOR_ROOT_IDENTITY_LOST"
        break
      }
      $lastItems = $items
      $ws = Get-TreeWorkingSet $items
      $bytes = Get-OutputBytes $OutputPath
      if ($ws -gt $peakWs) { $peakWs = $ws }
      if ($bytes -gt $peakOutput) { $peakOutput = $bytes }
      $sampleCount++
      $sample = [pscustomobject]@{
        elapsed_seconds = [Math]::Round($clock.Elapsed.TotalSeconds, 6)
        root_pid = $root
        process_tree = $items
        process_tree_working_set_bytes = $ws
        output_bytes = $bytes
      }
      $trace.WriteLine(($sample | ConvertTo-Json -Depth 8 -Compress))
      if ($clock.Elapsed.TotalSeconds -ge $WallSeconds) { $stopReason = "WALL_TIME_LIMIT"; break }
      if ($ws -ge $WorkingSetLimit) { $stopReason = "PROCESS_TREE_WORKING_SET_LIMIT"; break }
      if ($bytes -ge $OutputLimit) { $stopReason = "CUMULATIVE_OUTPUT_LIMIT"; break }
      Start-Sleep -Milliseconds $PollMilliseconds
    }
    if ($stopReason -ne "NATURAL_EXIT") {
      try { if (-not $proc.HasExited) { $proc.Kill($true) } } catch { }
      foreach ($item in $lastItems) {
        try {
          $left = [Diagnostics.Process]::GetProcessById([int]$item.pid)
          if (-not $left.HasExited) { $left.Kill($true) }
        } catch { }
      }
      if (-not $proc.WaitForExit(5000)) {
        & taskkill.exe /PID $root /T /F | Out-Null
        if (-not $proc.WaitForExit(5000)) { throw "SUPERVISOR_TERMINATION_TIMEOUT" }
      }
    } else {
      if (-not $proc.WaitForExit(5000)) { throw "SUPERVISOR_NATURAL_EXIT_WAIT_TIMEOUT" }
      $remaining = Get-TreeSnapshot $root
      if ($remaining.Count -gt 0) {
        $stopReason = "ORPHANED_DESCENDANT_AFTER_ROOT_EXIT"
        foreach ($item in $remaining) {
          try { $left = [Diagnostics.Process]::GetProcessById([int]$item.pid); if (-not $left.HasExited) { $left.Kill($true) } } catch { }
        }
      }
    }
  } catch {
    $stopReason = "MONITOR_ERROR"
    try { if (-not $proc.HasExited) { $proc.Kill($true) } } catch { }
    foreach ($item in $lastItems) {
      try { $left = [Diagnostics.Process]::GetProcessById([int]$item.pid); if (-not $left.HasExited) { $left.Kill($true) } } catch { }
    }
    try { $proc.WaitForExit() } catch { }
    throw
  } finally {
    $clock.Stop()
    $trace.Dispose()
  }
  $proc.Refresh()
  $exit = if ($proc.HasExited) { $proc.ExitCode } else { $null }
  $record = [pscustomobject]@{
    label = $Label
    executable = $psi.FileName
    arguments = $CommandArguments
    working_directory = $psi.WorkingDirectory
    root_pid = $root
    root_image = [IO.Path]::GetFileName($psi.FileName)
    elapsed_seconds = [Math]::Round($clock.Elapsed.TotalSeconds, 6)
    peak_sampled_process_tree_working_set_bytes = $peakWs
    peak_sampled_output_bytes = $peakOutput
    final_output_bytes = Get-OutputBytes $OutputPath
    poll_milliseconds = $PollMilliseconds
    samples = $sampleCount
    stop_reason = $stopReason
    exit_code = $exit
    child_git_object_environment_removed = $removedGitVariables
    thresholds_are_sampled_not_os_enforced = $true
  }
  $record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath ($TracePath + ".summary.json") -Encoding utf8
  return $record
}
if ($Mode -eq "SelfTest") {
  if ($ExpectedHead -notmatch '^[0-9a-f]{40}$') { throw "SELFTEST_EXPECTED_HEAD_REQUIRED" }
  $env:ARCANA_EXTERNAL_ROOT = "F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\_ARCANA_EXTERNAL_SOURCES"
  $env:PYTHONPATH = "C:\Users\jose_\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages;src"
  $self = Join-Path $EvidenceDirectory ("selftest-" + [Guid]::NewGuid().ToString("N"))
  New-Item -ItemType Directory -Path $self -Force | Out-Null
  $probeOutput = Join-Path $self "git-probe-output"
  New-Item -ItemType Directory -Path $probeOutput | Out-Null
  $probePath = Join-Path $self "git_provenance_probe.py"
  $probeResult = Join-Path $probeOutput "probe-result.json"
  $probeCode = @"
import hashlib, json, os, pathlib, subprocess, sys
repo, expected_head, result_path, expected_pythonpath, expected_external, expected_path_sha = sys.argv[1:]
def git(*args):
    return subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True)
top = git("rev-parse", "--show-toplevel")
head = git("rev-parse", "HEAD")
obj = git("cat-file", "-t", expected_head)
try:
    import numpy
    numpy_version = numpy.__version__
except Exception as exc:
    numpy_version = "IMPORT_FAILED:" + type(exc).__name__
env = {key: os.environ.get(key) for key in os.environ if key.upper().startswith("GIT_")}
data = {"pid": os.getpid(), "python_executable": sys.executable, "python_version": sys.version.split()[0],
        "numpy_version": numpy_version, "git_environment": env,
        "pythonpath_preserved": os.environ.get("PYTHONPATH") == expected_pythonpath,
        "external_root_preserved": os.environ.get("ARCANA_EXTERNAL_ROOT") == expected_external,
        "path_preserved": hashlib.sha256(os.environ.get("PATH", "").encode()).hexdigest() == expected_path_sha,
        "git_top_level": top.stdout.strip(), "git_top_level_returncode": top.returncode,
        "git_head": head.stdout.strip(), "git_head_returncode": head.returncode,
        "expected_head": expected_head, "object_type": obj.stdout.strip(), "object_returncode": obj.returncode,
        "git_errors": [x.stderr.strip() for x in (top, head, obj) if x.returncode]}
pathlib.Path(result_path).write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
same_repo = os.path.normcase(os.path.realpath(data["git_top_level"])) == os.path.normcase(os.path.realpath(repo)) if data["git_top_level"] else False
ok = (top.returncode == 0 and head.returncode == 0 and obj.returncode == 0 and same_repo
      and data["git_head"] == expected_head and data["object_type"] == "commit"
      and data["pythonpath_preserved"] and data["external_root_preserved"] and data["path_preserved"]
      and "GIT_OBJECT_DIRECTORY" not in env and "GIT_ALTERNATE_OBJECT_DIRECTORIES" not in env
      and numpy_version == "2.3.5" and data["python_version"] == "3.12.10")
raise SystemExit(0 if ok else 42)
"@
  Set-Content -LiteralPath $probePath -Value $probeCode -Encoding utf8
  $expectedPathSha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($env:PATH))).ToLowerInvariant()
  $probeArgs = @($probePath, $RepositoryRoot, $ExpectedHead, $probeResult, $env:PYTHONPATH,
    $env:ARCANA_EXTERNAL_ROOT, $expectedPathSha)
  $badObjectDir = Join-Path $self "invalid-git-objects"
  $badAlternateDir = Join-Path $self "invalid-git-alternates"
  $env:GIT_OBJECT_DIRECTORY = $badObjectDir
  $env:GIT_ALTERNATE_OBJECT_DIRECTORIES = $badAlternateDir
  $unsanitized = Invoke-Monitored "expected_environment_failure_without_sanitization" $probeArgs $probeOutput (Join-Path $self "unsanitized.ndjson") 30 2147483648 536870912 100 -TestOnlyRetainGitObjectEnvironment
  $unsanitizedReport = Get-Content -LiteralPath $probeResult -Raw | ConvertFrom-Json
  if ($unsanitized.exit_code -eq 0 -or $unsanitizedReport.git_head_returncode -eq 0 -or
      $unsanitizedReport.git_environment.GIT_OBJECT_DIRECTORY -ne $badObjectDir -or
      $unsanitizedReport.git_environment.GIT_ALTERNATE_OBJECT_DIRECTORIES -ne $badAlternateDir) {
    throw "UNSANITIZED_FAILURE_REPRODUCTION_FAILED"
  }
  Remove-Item -LiteralPath $probeResult -Force
  $sanitized = Invoke-Monitored "sanitized_child_git_provenance" $probeArgs $probeOutput (Join-Path $self "sanitized.ndjson") 30 2147483648 536870912 100
  if ($sanitized.stop_reason -ne "NATURAL_EXIT" -or $sanitized.exit_code -ne 0 -or
      $sanitized.child_git_object_environment_removed.Count -ne 2) { throw "SANITIZED_CHILD_GIT_PROVENANCE_FAILED" }
  $sanitizedReport = Get-Content -LiteralPath $probeResult -Raw | ConvertFrom-Json
  if ($sanitizedReport.pid -ne $sanitized.root_pid -or $sanitizedReport.git_head -ne $ExpectedHead -or
      $sanitizedReport.object_type -ne "commit" -or $sanitizedReport.git_environment.GIT_OBJECT_DIRECTORY -or
      $sanitizedReport.git_environment.GIT_ALTERNATE_OBJECT_DIRECTORIES -or
      -not $sanitizedReport.pythonpath_preserved -or -not $sanitizedReport.external_root_preserved -or
      -not $sanitizedReport.path_preserved) { throw "SANITIZED_CHILD_IDENTITY_OR_ENVIRONMENT_FAILED" }
  $env:GIT_OBJECT_DIRECTORY = "C:\Users\jose_\AppData\Local\ARCANA\git-objects\r6"
  $env:GIT_ALTERNATE_OBJECT_DIRECTORIES = "F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\ARCANA_WORLD1_v0_6D1_R3_11_POST_CHA1_H0_RECOVERY_ADAPTIVE_RADIATION_RESTART_CANDIDATE\.git\objects"
  $childTrace = Join-Path $self "tree.ndjson"
  $code = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); time.sleep(60)"
  $tree = Invoke-Monitored "tree_wall_limit" @("-c",$code) (Join-Path $self "tree-output") $childTrace 0.8 2147483648 99999999 50
  if ($tree.stop_reason -ne "WALL_TIME_LIMIT" -or $tree.exit_code -eq 0) { throw "SUPERVISOR_WALL_TEST_FAILED" }
  $traceRows = @(Get-Content $childTrace | ForEach-Object { $_ | ConvertFrom-Json })
  $maxProcesses = ($traceRows | ForEach-Object { $_.process_tree.Count } | Measure-Object -Maximum).Maximum
  if ($maxProcesses -lt 2) { throw "SUPERVISOR_DESCENDANT_DISCOVERY_TEST_FAILED" }
  $treePids = @($traceRows | ForEach-Object { $_.process_tree } | ForEach-Object { [int]$_.pid } | Sort-Object -Unique)
  $survivors = @()
  foreach ($processId in $treePids) {
    try { $candidate = [Diagnostics.Process]::GetProcessById($processId); if (-not $candidate.HasExited) { $survivors += $processId } }
    catch [System.ArgumentException] { }
  }
  if ($survivors.Count -gt 0) { throw "SUPERVISOR_PROCESS_TREE_TERMINATION_FAILED:$($survivors -join ',')" }
  $memCode = "import time; x=bytearray(67108864); [x.__setitem__(i,1) for i in range(0,len(x),4096)]; time.sleep(60)"
  $memory = Invoke-Monitored "working_set_limit" @("-c",$memCode) (Join-Path $self "memory-output") (Join-Path $self "memory.ndjson") 60 33554432 99999999 50
  if ($memory.stop_reason -ne "PROCESS_TREE_WORKING_SET_LIMIT" -or $memory.exit_code -eq 0) { throw "SUPERVISOR_MEMORY_TEST_FAILED" }
  $outCode = "import pathlib,sys,time; pathlib.Path(sys.argv[1]).write_bytes(b'x'*65536); time.sleep(60)"
  $outTarget = Join-Path $self "output-test"
  New-Item -ItemType Directory -Path $outTarget | Out-Null
  $output = Invoke-Monitored "output_limit" @("-c",$outCode,(Join-Path $outTarget "payload.bin")) $outTarget (Join-Path $self "output.ndjson") 60 2147483648 32768 50
  if ($output.stop_reason -ne "CUMULATIVE_OUTPUT_LIMIT" -or $output.final_output_bytes -lt 32768) { throw "SUPERVISOR_OUTPUT_TEST_FAILED" }
  $exitCode = Invoke-Monitored "exit_code_propagation" @("-c","raise SystemExit(23)") (Join-Path $self "exit-output") (Join-Path $self "exit.ndjson") 60 2147483648 99999999 50
  if ($exitCode.stop_reason -ne "NATURAL_EXIT" -or $exitCode.exit_code -ne 23) { throw "SUPERVISOR_EXIT_PROPAGATION_TEST_FAILED" }
  @($unsanitized,$sanitized,$tree,$memory,$output,$exitCode) | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $self "selftest-results.json") -Encoding utf8
  $sanitizedReport | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $self "git-provenance-result.json") -Encoding utf8
  "SUPERVISOR_SELFTEST_PASS"
  return
}
if ($Mode -eq "ProviderAudit") {
  if ($ExpectedHead -notmatch '^[0-9a-f]{40}$') { throw "PROVIDER_AUDIT_EXPECTED_HEAD_REQUIRED" }
  $env:ARCANA_EXTERNAL_ROOT = "F:\corsiiuu\Magistrale\Arcana\ArcanaWorld\_ARCANA_EXTERNAL_SOURCES"
  $env:PYTHONPATH = "C:\Users\jose_\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages;src"
  if (Test-Path -LiteralPath $EvidenceDirectory) { throw "REFUSE_EXISTING_EVIDENCE_DIRECTORY:$EvidenceDirectory" }
  New-Item -ItemType Directory -Path $EvidenceDirectory -ErrorAction Stop | Out-Null
  $auditDir = Join-Path $EvidenceDirectory "provider-audit"
  New-Item -ItemType Directory -Path $auditDir -ErrorAction Stop | Out-Null
  $auditScript = Join-Path $auditDir "audit_pair_5_11.py"
  $auditResult = Join-Path $auditDir "provider-audit-result.json"
  $auditCode = @"
import json, pathlib, sys
from arcana_worldsim.r6.functional_spatial_support import audit_pair_5_11
root, expected_branch, expected_head, result_path = sys.argv[1:]
result = audit_pair_5_11(root, expected_branch=expected_branch)
if result.get("source_head") != expected_head:
    raise SystemExit("PROVIDER_AUDIT_HEAD_MISMATCH")
pathlib.Path(result_path).write_text(json.dumps(result, sort_keys=True, indent=2), encoding="utf-8")
"@
  Set-Content -LiteralPath $auditScript -Value $auditCode -Encoding utf8
  $args = @($auditScript, $RepositoryRoot, "r6/si1-bandwidth-f2av", $ExpectedHead, $auditResult)
  $audit = Invoke-Monitored "provider_audit_sanitized_child_environment" $args $auditDir (Join-Path $auditDir "supervisor.ndjson") 180 2147483648 536870912 100
  $audit | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $auditDir "supervisor-summary.json") -Encoding utf8
  if ($audit.stop_reason -ne "NATURAL_EXIT" -or $audit.exit_code -ne 0 -or
      $audit.child_git_object_environment_removed.Count -ne 2) { throw "SANITIZED_PROVIDER_AUDIT_FAILED" }
  Get-Content -LiteralPath $auditResult -Raw
  return
}
if ($Mode -eq "Run") {
  $env:ARCANA_EXTERNAL_ROOT = "F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\_ARCANA_EXTERNAL_SOURCES"
  $env:PYTHONPATH = "C:\Users\jose_\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages;src"
  $outputPath = Join-Path $RepositoryRoot $OutputRelative
  if (Test-Path -LiteralPath $outputPath) { throw "REFUSE_EXISTING_CANDIDATE_OUTPUT:$outputPath" }
  if (Test-Path -LiteralPath $EvidenceDirectory) { throw "REFUSE_EXISTING_EVIDENCE_DIRECTORY:$EvidenceDirectory" }
  New-Item -ItemType Directory -Path $EvidenceDirectory -ErrorAction Stop | Out-Null
  $repo = [IO.Path]::GetFullPath($RepositoryRoot)
  $scriptPath = Join-Path $repo "scripts/r6_functional_development_t_f2b.py"
  $args = @($scriptPath,"--repository-root",".","--expected-branch","r6/si1-bandwidth-f2av","--output-relative",$OutputRelative.Replace('\','/') )
  $trace = Join-Path $EvidenceDirectory "run.ndjson"
  $result = Invoke-Monitored "INT0B_R1_SINGLE_ATTEMPT" $args $outputPath $trace 900 2147483648 536870912 100
  $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $EvidenceDirectory "run-summary.json") -Encoding utf8
  $result | Format-List
  if ($result.stop_reason -ne "NATURAL_EXIT") { exit 124 }
  if ($result.exit_code -ne 0) { exit $result.exit_code }
  exit 0
}
