$ErrorActionPreference = "Stop"

# ============================================================================
# ARCANA R5.17
# Close B6 / Open B7 / Build reusable execution-reference index
#
# Intended usage:
#   1. Copy this file into the repository root.
#   2. Run it from PowerShell while inside the repository.
#   3. Review the staged diff.
#   4. Commit and push manually.
#
# This script DOES NOT commit or push automatically.
# ============================================================================

$Self = (Resolve-Path $MyInvocation.MyCommand.Path).Path
$SelfDir = Split-Path -Parent $Self

$RepoOutput = git -C $SelfDir rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($RepoOutput)) {
    throw "STOP: script must be located inside a Git repository. Script folder: $SelfDir"
}

$Repo = $RepoOutput.Trim()
Set-Location $Repo

# git rev-parse returns paths with "/" while Windows PowerShell resolves "\",
# so normalize both before comparing them.
$RepoNorm = [System.IO.Path]::GetFullPath($Repo.Replace("/", "\")).TrimEnd("\")
$SelfDirNorm = [System.IO.Path]::GetFullPath($SelfDir.Replace("/", "\")).TrimEnd("\")

if ($SelfDirNorm -ine $RepoNorm) {
    Write-Host "Repository root = $RepoNorm"
    Write-Host "Script folder   = $SelfDirNorm"
    throw "STOP: copy this script into the repository root before running it."
}

$SelfRel = Split-Path -Leaf $Self

Write-Host "============================================================"
Write-Host " ARCANA R5.17 - CLOSE B6 / OPEN B7 / BUILD REFERENCE INDEX"
Write-Host "============================================================"
Write-Host "Repository = $Repo"
Write-Host "Script     = $SelfRel"

# ----------------------------------------------------------------------------
# Git preflight
# ----------------------------------------------------------------------------

git fetch origin

$Head = (git rev-parse HEAD).Trim()
$Remote = (git rev-parse origin/main).Trim()

Write-Host ""
Write-Host "HEAD        = $Head"
Write-Host "origin/main = $Remote"

if ($Head -ne $Remote) {
    throw "STOP: local HEAD is not identical to origin/main. Synchronize first."
}

$StagedBefore = @(git diff --cached --name-only)
if ($StagedBefore.Count -gt 0) {
    Write-Host ""
    Write-Host "Pre-existing staged files:"
    $StagedBefore
    throw "STOP: index must be empty before this transition."
}

$TrackedNames = @(git diff --name-only)

if ($TrackedNames.Count -gt 0) {
    $OnlyCurrentState = (
        $TrackedNames.Count -eq 1 -and
        $TrackedNames[0] -eq "ARCANA_WORLD_CURRENT_STATE.md"
    )

    if (-not $OnlyCurrentState) {
        Write-Host ""
        Write-Host "Unexpected tracked working-tree changes:"
        git status --short --untracked-files=no
        throw "STOP: tracked working tree contains unrelated changes."
    }

    $CurrentStatePath = Join-Path $Repo "ARCANA_WORLD_CURRENT_STATE.md"
    $CurrentText = [System.IO.File]::ReadAllText(
        $CurrentStatePath,
        [System.Text.Encoding]::UTF8
    )
    $BeginDirty = "<!-- R517_B6_TO_B7_TRANSITION_BEGIN -->"
    $EndDirty = "<!-- R517_B6_TO_B7_TRANSITION_END -->"

    $BeginPos = $CurrentText.IndexOf($BeginDirty)
    $EndPos = $CurrentText.IndexOf($EndDirty)

    if ($BeginPos -lt 0 -or $EndPos -lt $BeginPos) {
        throw "STOP: current-state modification is not the known B6->B7 transition residue."
    }

    $TailStart = $EndPos + $EndDirty.Length
    $Tail = $CurrentText.Substring($TailStart)
    if ($Tail.Trim().Length -ne 0) {
        throw "STOP: current-state contains content after the known transition block."
    }

    $Prefix = $CurrentText.Substring(0, $BeginPos).TrimEnd()
    if (-not $Prefix.EndsWith("---", [System.StringComparison]::Ordinal)) {
        throw "STOP: current-state transition is not preceded by the expected separator."
    }
    $Prefix = $Prefix.Substring(0, $Prefix.Length - 3)
    while ($Prefix.Length -gt 0 -and [char]::IsWhiteSpace($Prefix[$Prefix.Length - 1])) {
        $Prefix = $Prefix.Substring(0, $Prefix.Length - 1)
    }

    $HeadTemp = Join-Path ([System.IO.Path]::GetTempPath()) ("arcana-head-current-state-{0}.md" -f ([guid]::NewGuid().ToString("N")))
    try {
        & cmd.exe /d /c "git show HEAD:ARCANA_WORLD_CURRENT_STATE.md > `"$HeadTemp`""
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to materialize HEAD current-state content for comparison."
        }
        $HeadText = [System.IO.File]::ReadAllText(
            $HeadTemp,
            [System.Text.Encoding]::UTF8
        )
    }
    finally {
        if (Test-Path $HeadTemp -PathType Leaf) {
            Remove-Item -LiteralPath $HeadTemp -Force
        }
    }

    $PrefixNorm = ($Prefix -replace "`r`n", "`n").TrimEnd()
    $HeadNorm = ($HeadText -replace "`r`n", "`n").TrimEnd()

    $KnownA1PrefixNorm = $HeadNorm
    $KnownA1PrefixNorm = [regex]::Replace(
        $KnownA1PrefixNorm,
        "(?m)^LATEST_COMPLETED_INTERNAL_STEP:.*$",
        "LATEST_COMPLETED_INTERNAL_STEP: R5.17-B7-A1",
        1
    )
    $KnownA1PrefixNorm = [regex]::Replace(
        $KnownA1PrefixNorm,
        "(?m)^LATEST_INTERNAL_VERDICT:.*$",
        "LATEST_INTERNAL_VERDICT: PASS_R517_B7_A1_NATURAL_FOOD_SUPPORT_AUTHORITY_SCHEMA_COVERAGE_PREFLIGHT",
        1
    )
    $KnownA1PrefixNorm = [regex]::Replace(
        $KnownA1PrefixNorm,
        "(?m)^ACTIVE_SUBPHASE:.*$",
        "ACTIVE_SUBPHASE: R5.17-B7",
        1
    )
    $KnownA1PrefixNorm = [regex]::Replace(
        $KnownA1PrefixNorm,
        "(?m)^ACTIVE_SUBPHASE_STATUS:.*$",
        "ACTIVE_SUBPHASE_STATUS: A1_PREFLIGHT_COMPLETE__A2_READY",
        1
    )
    $KnownA1PrefixNorm = [regex]::Replace(
        $KnownA1PrefixNorm,
        "(?m)^ACTIVE_SUBPHASE_SCOPE:.*$",
        "ACTIVE_SUBPHASE_SCOPE: NATURAL_BIOLOGICAL_FOOD_SUPPORT",
        1
    )
    $KnownA1PrefixNorm = [regex]::Replace(
        $KnownA1PrefixNorm,
        "(?m)^NEXT_ACTION:.*$",
        "NEXT_ACTION: RUN_B7_A2_SEMANTIC_BINDING_AND_TEMPORAL_COVERAGE_ADJUDICATION",
        1
    )

    if (-not [System.String]::Equals(
        $PrefixNorm,
        $HeadNorm,
        [System.StringComparison]::Ordinal
    ) -and -not [System.String]::Equals(
        $PrefixNorm,
        $KnownA1PrefixNorm,
        [System.StringComparison]::Ordinal
    )) {
        throw "STOP: current-state dirty content is not only the previously generated transition block."
    }

    Write-Host ""
    Write-Host "Known prior B6->B7 transition residue detected."
    Write-Host "Restoring ARCANA_WORLD_CURRENT_STATE.md to HEAD before clean regeneration."
    git restore --worktree -- "ARCANA_WORLD_CURRENT_STATE.md"

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to restore known current-state transition residue."
    }
}

$TrackedAfterRepair = @(git diff --name-only)
if ($TrackedAfterRepair.Count -gt 0) {
    throw "STOP: tracked working tree is still dirty after safe residue repair."
}

# ----------------------------------------------------------------------------
# Git object-database write preflight
# ----------------------------------------------------------------------------

Write-Host ""
Write-Host "============================================================"
Write-Host " GIT OBJECT DATABASE WRITE PREFLIGHT"
Write-Host "============================================================"

function Invoke-GitHashObjectProbe {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Payload
    )

    $GitExe = (Get-Command git.exe -ErrorAction Stop).Source
    $Token = [guid]::NewGuid().ToString("N")

    $InputPath = Join-Path $env:TEMP ("arcana_git_probe_in_" + $Token + ".txt")
    $StdoutPath = Join-Path $env:TEMP ("arcana_git_probe_out_" + $Token + ".txt")
    $StderrPath = Join-Path $env:TEMP ("arcana_git_probe_err_" + $Token + ".txt")

    try {
        [System.IO.File]::WriteAllText(
            $InputPath,
            $Payload,
            [System.Text.Encoding]::ASCII
        )

        $Proc = Start-Process `
            -FilePath $GitExe `
            -ArgumentList @("hash-object", "-w", "--stdin") `
            -WorkingDirectory $Repo `
            -RedirectStandardInput $InputPath `
            -RedirectStandardOutput $StdoutPath `
            -RedirectStandardError $StderrPath `
            -NoNewWindow `
            -Wait `
            -PassThru

        $OutText = ""
        $ErrText = ""

        if (Test-Path $StdoutPath) {
            $RawOut = [System.IO.File]::ReadAllText($StdoutPath)
            if ($null -ne $RawOut) {
                $OutText = $RawOut.Trim()
            }
        }

        if (Test-Path $StderrPath) {
            $RawErr = [System.IO.File]::ReadAllText($StderrPath)
            if ($null -ne $RawErr) {
                $ErrText = $RawErr.Trim()
            }
        }

        return [pscustomobject]@{
            ExitCode = $Proc.ExitCode
            Stdout = $OutText
            Stderr = $ErrText
        }
    }
    finally {
        Remove-Item $InputPath -Force -ErrorAction SilentlyContinue
        Remove-Item $StdoutPath -Force -ErrorAction SilentlyContinue
        Remove-Item $StderrPath -Force -ErrorAction SilentlyContinue
    }
}

$GitObjectProbeSucceeded = $false
$GitObjectProbeHash = $null
$GitObjectProbePayloadBase = "ARCANA_GIT_OBJECT_WRITE_PROBE_V4"

$ProbeDelays = @(2, 4, 8, 15, 30)

for ($Attempt = 1; $Attempt -le 6; $Attempt++) {
    $UniquePayload = (
        $GitObjectProbePayloadBase +
        "_" +
        [guid]::NewGuid().ToString("N")
    )

    $Probe = Invoke-GitHashObjectProbe -Payload $UniquePayload

    if ($Probe.ExitCode -eq 0 -and -not [string]::IsNullOrWhiteSpace($Probe.Stdout)) {
        $CandidateHash = $Probe.Stdout.Trim()

        $OldEA = $ErrorActionPreference
        $ErrorActionPreference = "Continue"

        git cat-file -e $CandidateHash 2>$null
        $CatExit = $LASTEXITCODE

        $ErrorActionPreference = $OldEA

        if ($CatExit -eq 0) {
            $GitObjectProbeSucceeded = $true
            $GitObjectProbeHash = $CandidateHash
            break
        }
    }

    Write-Host "Git NEW-object write attempt $Attempt/6 failed."

    if (-not [string]::IsNullOrWhiteSpace($Probe.Stderr)) {
        Write-Host $Probe.Stderr
    }

    if ($Attempt -lt 6) {
        $Delay = $ProbeDelays[$Attempt - 1]
        Write-Host "Waiting $Delay seconds before a new-object retry."
        Start-Sleep -Seconds $Delay
    }
}

if (-not $GitObjectProbeSucceeded) {
    throw "STOP: Git failed 6 independent NEW-object writes. Do not continue with repository staging."
}

Write-Host "PASS: Git object database is writable."
Write-Host "Probe object = $GitObjectProbeHash"

# ----------------------------------------------------------------------------
# Verify B6 terminal authority
# ----------------------------------------------------------------------------

Write-Host ""
Write-Host "============================================================"
Write-Host " VERIFY B6 TERMINAL AUTHORITY"
Write-Host "============================================================"

$D4 = Join-Path $Repo "R5_17_B6_D4_FRESHWATER_ACCESS_AND_RELIABILITY.json"

if (-not (Test-Path $D4 -PathType Leaf)) {
    throw "Missing B6 D4 terminal artifact: $D4"
}

$D4Doc = Get-Content $D4 -Raw | ConvertFrom-Json

$RequiredD4Status = "PASS_R517_B6_D4_FRESHWATER_ACCESS_AND_RELIABILITY_MATERIALIZED"

if ($D4Doc.status -ne $RequiredD4Status) {
    throw "Unexpected D4 status: $($D4Doc.status)"
}

if ($D4Doc.freshwater_support_materialized -ne $true) {
    throw "D4 does not confirm freshwater_support_materialized=true."
}

if ($D4Doc.hydrological_reliability_materialized -ne $true) {
    throw "D4 does not confirm hydrological_reliability_materialized=true."
}

if ($D4Doc.k_materialized -ne $false) {
    throw "D4 does not preserve k_materialized=false."
}

Write-Host "PASS: freshwater support materialized."
Write-Host "PASS: hydrological reliability materialized."
Write-Host "PASS: K(x,t) remains unmaterialized."

# ----------------------------------------------------------------------------
# Dynamic B6 tracked inventory
# ----------------------------------------------------------------------------

$AllVisiblePaths = @(
    git ls-files --cached --others --exclude-standard
)

$B6Inventory = @(
    $AllVisiblePaths |
        Where-Object {
            $_ -match "(?i)^R5[_-]17[_-]B6" -and
            $_ -notmatch "(?i)^R5_17_B6_CLOSE_B7_OPEN_AND_BUILD_REFERENCE_INDEX"
        } |
        Sort-Object -Unique
)

$B6InventoryText = if ($B6Inventory.Count -gt 0) {
    ($B6Inventory | ForEach-Object { "- $_" }) -join "`n"
}
else {
    "- [no B6 authority/evidence files discovered]"
}

# ----------------------------------------------------------------------------
# B6 completion register
# ----------------------------------------------------------------------------

$B6Register = Join-Path $Repo "R5_17_B6_COMPLETION_REGISTER.md"

@"
# R5.17-B6 - Freshwater / Paleohydrology Completion Register

## Status

STAGE: v0.6D1-R5.17
SUBPHASE: R5.17-B6
STATUS: COMPLETED
SEALED: false
CANONICAL_MUTATION: false
K_X_T_MATERIALIZED: false
NEXT_SUBPHASE: R5.17-B7

B6 is a substantive completed milestone inside active R5.17.
It is deliberately not promoted to a separate SEALED milestone.

## Scientific purpose

Recover and bind the physical hydrology required to derive natural
freshwater access and reliability without interpreting climate proxies,
forage fields, hazard indices, or human settlement states as freshwater
supply.

## Completed progression

### H1-H4 - native hydrology recovery and provenance

The B6 hydrology discovery/provenance chain recovered and adjudicated:

- native hydrology artifacts;
- root/source provenance;
- generator semantics;
- export sufficiency;
- the distinction between physical hydrology and environmental proxies.

### D1 - canonical hydrology replay contract

Established the governed replay contract for recovering native channel
hydrology instead of inventing a new water model.

### D2 family - canonical paleohydrology input binding

Bound and reconciled the paleoclimate, seasonal-climate, shoreline and
hydrology inputs required by the replay.

The D2 investigation included:

- seasonal-climate baseline identity and promotion;
- canonical seasonal reconstruction;
- shoreline land-mask recovery;
- replay diagnosis;
- source/stage-aligned reconstruction;
- no promotion by arbitrary replay tolerance.

Intermediate BLOCKED/diagnostic states are retained as provenance but are
superseded by the later successful replay path.

### D3 / D3R - canonical paleohydrology replay

The final replay path recovered the coast-state contract required by the
historical native hydrology generator and materialized governed
paleohydrology snapshots.

### D4 - freshwater access and reliability

Terminal B6 authority:

STATUS: $($D4Doc.status)
FRESHWATER_SUPPORT_MATERIALIZED: $($D4Doc.freshwater_support_materialized)
HYDROLOGICAL_RELIABILITY_MATERIALIZED: $($D4Doc.hydrological_reliability_materialized)
K_X_T_MATERIALIZED: $($D4Doc.k_materialized)

B6 therefore supplies the physical freshwater component needed by the
human-support foundation while keeping K(x,t) downstream.

## Semantic guardrails retained

The following equivalences remain forbidden:

wetland_forage               != freshwater supply
aridity_index                 != freshwater supply
freshwater_forcing_sv         != local freshwater access
precipitation alone           != freshwater access
R3.20 hydrological hazard     != freshwater availability
R3.20 flood/drying indices    != water quantity

R3.20 remains useful only as independent hydrological/hazard semantic
cross-validation.

## B6 -> B7 boundary

B6 does not materialize:

human-edible biological food
calories
persons/cell
K(x,t)
settlement density
agriculture
trade
polity
civilization

Those remain downstream.

## Tracked B6 authority surface at transition

$B6InventoryText

## Disposition

B6_COMPLETION_DECISION: AUTHORIZE_R5_17_B7
NEXT_SCOPE: NATURAL_BIOLOGICAL_FOOD_SUPPORT
MICRO_SEAL_CREATED: false
"@ | Set-Content -LiteralPath $B6Register -Encoding UTF8

# ----------------------------------------------------------------------------
# A1 forage provenance disposition
# ----------------------------------------------------------------------------

$A1Disposition = Join-Path $Repo "R5_17_B7_A1_FORAGE_PROVENANCE_DISPOSITION.md"

@"
# R5.17-B7 - A1 Forage Provenance Disposition

## Authority

ARTIFACT: references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz
SHA256: 9469118BFF69CFC4A5BBFE398F382224F887D81A69581E3A654D08EA11FC604F

REPOSITORY_INTRODUCTION_COMMIT:
15ef285e554658125744056ec9266d9b0ed4c0ba

INTRODUCTION_COMMIT_TYPE: ROOT_COMMIT
PARENT_COMMIT: NONE

The available repository history begins with the A1 artifact already
materialized. No earlier Git revision exists from which an original forage
generator can be recovered.

## Channels

browse_forage
low_forage
wetland_forage
total_edible_forage

The later ARCANA biological runtime demonstrates that these fields operate as
trophic-resource channels.

total_edible_forage is treated as a closure/summary of the component forage
channels, not as an independently calibrated human-food field.

## Scientific interpretation

CANONICAL_INHERITED_AUTHORITY: true
BIOLOGICALLY_OPERATIONAL: true

ORIGINAL_GENERATOR_RECOVERED: false
ORIGINAL_PHYSICAL_CALIBRATION_RECOVERED: false

AUTHORIZED_INTERPRETATION:
  TROPHIC_RESOURCE_PROXY: true

NOT_AUTHORIZED:
  PHYSICAL_BIOMASS: true
  HUMAN_EDIBLE_CALORIES: true
  PERSONS_PER_CELL: true
  CARRYING_CAPACITY_K: true

## Final provenance disposition

LEGACY_MATERIALIZED_AUTHORITY
GENERATOR_NOT_RECOVERABLE_FROM_AVAILABLE_REPOSITORY_HISTORY

This is a bounded provenance limitation. It is not authorization to invent
an undocumented historical generator.
"@ | Set-Content -LiteralPath $A1Disposition -Encoding UTF8

# ----------------------------------------------------------------------------
# B7 scientific contract
# ----------------------------------------------------------------------------

$B7Contract = Join-Path $Repo "R5_17_B7_BIOLOGICAL_FOOD_SUPPORT_CONTRACT.md"

@"
# R5.17-B7 - Natural Biological Food Support Contract

## Purpose

Materialize the natural/pre-management biological resource support available
to humans from already-authoritative ARCANA environment and biosphere state.

B7 is upstream of technology, managed resource systems, agriculture and
civilizational carrying capacity.

## Core separation

NATURAL BIOLOGICAL FOOD SUPPORT
        !=
HUMAN FOOD PRODUCTION
        !=
K(x,t)

B7 asks what biological food-resource opportunity exists in the simulated
natural world before human technology, processing, storage, management,
domestication or agriculture are applied.

## Candidate natural authorities

### A1 native forage vector

browse_forage
low_forage
wetland_forage
total_edible_forage

Authorized role:

native trophic / plant-resource substrate

Not authorized as:

physical biomass
human-edible calories
human carrying capacity

### R3.33 environmental resource state

Natural environmental components may be reused where their provenance is
independent of human readiness.

Human-conditioned readiness/contact fields must not enter the natural
baseline.

The R3.33 domestication-oriented candidate cohort must not be treated as an
exhaustive inventory of wild animal food resources.

### R3.34 pre-management producer landscape

Potentially useful pre-management fields include:

suitability
resource_abundance
harvest_return

harvest_return is a candidate refinement for human-accessible plant-resource
opportunity only where its temporal/domain semantics are valid.

propagation_opportunity is a management affordance and is excluded from the
natural B7 baseline unless separately justified.

Downstream producer coevolution/domestication outputs are excluded.

### H0 wild-animal state

B7 must inspect the complete relevant H0 fauna authority, guild structure,
spatial population/range state and trophic relationships.

A domestication-screening subset must not substitute for the natural fauna
resource layer.

### Aquatic / marine resources

Aquatic or marine support may be included only if an existing canonical
physical/biological authority is recovered.

If no adequate authority exists, the missing component remains an explicit
coverage gap. B7 must not invent marine productivity.

## Forbidden B7 inputs

R3.32 subsistence readiness
technology stocks
food processing
storage
landscape management
seasonal logistics
human-readiness-weighted contact opportunity
domestication trajectory
producer coevolution
agriculture
settlement
population target
city/state/polity target

## Initial component architecture

PLANT_TROPHIC_RESOURCE_SUPPORT
  source: A1/native ecological substrate

PLANT_HARVEST_OPPORTUNITY
  source: pre-management producer landscape where temporally valid

WILD_ANIMAL_RESOURCE_SUPPORT
  source: complete governed H0 fauna/ecology authority

AQUATIC_MARINE_RESOURCE_SUPPORT
  source: canonical authority if recovered
  otherwise: NOT_MATERIALIZED

Coverage masks, temporal domain, source identity and provenance must remain
attached to each component.

## Temporal guardrail

Authorities with different temporal domains must not be silently extended.

Deep-time A1 forage authority must not be confused with literal modern flora.
Recent producer models must not be backprojected into deep time as historical
species/resource states.

## B7-A1

First governed step:

SOURCE AUTHORITY + SCHEMA + COVERAGE PREFLIGHT

B7-A1 inventories actual materialized inputs and determines which natural
resource components can be bound without introducing a new biological model.

No scalar biological-food-support equation is authorized in B7-A1.

## B7 completion gate

NATURAL_PLANT_RESOURCE_SUPPORT: materialized_or_explicitly_bounded
NATURAL_WILD_ANIMAL_SUPPORT: materialized_or_explicitly_bounded
AQUATIC_MARINE_SUPPORT: materialized_or_explicitly_unavailable
HUMAN_MANAGEMENT_USED: false
POPULATION_TARGET_USED: false
K_X_T_MATERIALIZED: false
PROVENANCE_EXPLICIT: true
"@ | Set-Content -LiteralPath $B7Contract -Encoding UTF8

# ----------------------------------------------------------------------------
# Reusable repository reference-index builder
# ----------------------------------------------------------------------------

$ToolsDir = Join-Path $Repo "tools"
New-Item -ItemType Directory -Path $ToolsDir -Force | Out-Null

$IndexBuilder = Join-Path $ToolsDir "build_arcana_execution_reference_index.py"

@'
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MD_OUT = ROOT / "ARCANA_EXECUTION_REFERENCE_INDEX.md"
JSON_OUT = ROOT / "ARCANA_EXECUTION_REFERENCE_INDEX.json"

SELF_EXCLUDED = {
    "ARCANA_EXECUTION_REFERENCE_INDEX.md",
    "ARCANA_EXECUTION_REFERENCE_INDEX.json",
}


def run_git(*args: str) -> str:
    cp = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return cp.stdout


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def candidate_paths() -> list[str]:
    # Index only repository-authoritative paths: already tracked or staged in
    # the index. Untracked scratch/reconstruction residue is intentionally
    # excluded so the index never points at local-only files.
    cached = set(run_git("ls-files").splitlines())
    return sorted(cached - SELF_EXCLUDED)


def is_reference_surface(path: str) -> bool:
    p = path.replace("\\", "/")
    name = Path(p).name
    upper = name.upper()
    suffix = Path(p).suffix.lower()

    if p.startswith(".git/"):
        return False

    if upper.startswith("README"):
        return True

    if suffix == ".ps1":
        return True

    if any(
        token in upper
        for token in (
            "STATUS",
            "CONTRACT",
            "AUDIT",
            "SUMMARY",
            "MANIFEST",
            "AUTHORITY",
            "HANDOFF",
            "PROTOCOL",
            "PREFLIGHT",
            "EVIDENCE",
            "SEAL",
            "RECONCILIATION",
            "RECOVERY",
        )
    ):
        return True

    if p.startswith("configs/") and suffix == ".json":
        return True

    if re.search(r"(?i)^R5_17_B[67]_", p) and suffix in {".json", ".md", ".py", ".ps1"}:
        return True

    if p.startswith("benchmarks/") and suffix in {
        ".py", ".ps1", ".sh", ".r", ".ini"
    }:
        return True

    if suffix == ".py":
        if re.search(r"(?i)(^|/)(R[345][_-]\d+|run_|capture_|check_)", p):
            return True
        if "scientific_engines" in p:
            return True

    if p in {
        "SIMULATION_RESULTS/SEMANTIC_CATALOG.md",
        "ARCANA_WORLD_CURRENT_STATE.md",
    }:
        return True

    return False


def category(path: str) -> str:
    p = path.replace("\\", "/")
    name = Path(p).name
    upper = name.upper()
    suffix = Path(p).suffix.lower()

    if p == "ARCANA_WORLD_CURRENT_STATE.md":
        return "CURRENT_STATE"
    if p == "SIMULATION_RESULTS/SEMANTIC_CATALOG.md":
        return "SEMANTIC_CATALOG"
    if upper.startswith("README"):
        return "README"
    if suffix == ".ps1":
        return "POWERSHELL_RUNNER"
    if "CONTRACT" in upper or "PROTOCOL" in upper:
        return "CONTRACT_PROTOCOL"
    if "AUDIT" in upper:
        return "AUDIT"
    if "STATUS" in upper:
        return "STATUS"
    if "HANDOFF" in upper:
        return "HANDOFF"
    if "AUTHORITY" in upper and suffix == ".json":
        return "AUTHORITY_JSON"
    if "MANIFEST" in upper:
        return "MANIFEST"
    if "SUMMARY" in upper:
        return "RESULT_SUMMARY"
    if p.startswith("configs/"):
        return "CONFIG"
    if p.startswith("benchmarks/"):
        return "BENCHMARK_EXECUTOR"
    if suffix == ".py":
        return "PYTHON_RUNNER_SOURCE"
    return "REFERENCE"


def normalize_stage(raw: str) -> str:
    return raw.replace("_", ".").replace("-", ".")


def stage_key(path: str) -> str:
    text = path.replace("\\", "/")

    patterns = [
        r"(?i)R5[_-]17[_-]B\d+(?:[_-][A-Z]\d+[A-Z0-9]*)?",
        r"(?i)R5[_-]\d+(?:[_-][A-Z]\d+[A-Z0-9]*)?",
        r"(?i)R4[_-]\d+(?:[_-]R\d+[A-Z0-9]*)?",
        r"(?i)R3[_-]\d+[A-Z]?(?:[_-]R\d+[A-Z0-9]*)?",
    ]

    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return normalize_stage(m.group(0).upper())

    version = re.search(r"(?i)v0[_-]6D1(?:[_-]R\d+[A-Z0-9_]*)?", text)
    if version:
        return normalize_stage(version.group(0).upper())

    return "UNSCOPED"


def title_from_file(path: Path) -> str:
    if path.suffix.lower() not in {
        ".md", ".txt", ".ps1", ".py", ".json", ".r", ".sh", ".ini"
    }:
        return ""

    try:
        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return ""

    for line in text.splitlines()[:80]:
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
        if stripped.startswith("## "):
            return stripped[3:].strip()

    return ""


def git_blob_oid(path: str) -> str | None:
    try:
        out = run_git("ls-files", "-s", "--", path).strip()
    except subprocess.CalledProcessError:
        return None

    if not out:
        return None

    first = out.splitlines()[0].split()
    if len(first) >= 2:
        return first[1]

    return None


def build_record(path_str: str) -> dict[str, Any]:
    path = ROOT / path_str
    stat = path.stat()

    return {
        "path": path_str.replace("\\", "/"),
        "stage": stage_key(path_str),
        "category": category(path_str),
        "title": title_from_file(path),
        "extension": path.suffix.lower(),
        "size_bytes": stat.st_size,
        "git_blob_oid": git_blob_oid(path_str),
        "sha256": sha256_file(path),
    }


def md_escape(value: str) -> str:
    return (
        value.replace("|", r"\|")
        .replace("\n", " ")
        .strip()
    )


def main() -> int:
    head = run_git("rev-parse", "HEAD").strip()
    now = datetime.now(timezone.utc).isoformat()

    paths = [
        p
        for p in candidate_paths()
        if is_reference_surface(p)
        and (ROOT / p).is_file()
    ]

    records = [build_record(p) for p in paths]
    records.sort(
        key=lambda r: (
            r["stage"],
            r["category"],
            r["path"],
        )
    )

    category_counts = Counter(r["category"] for r in records)
    stage_counts = Counter(r["stage"] for r in records)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["stage"]].append(record)

    payload = {
        "schema": "ARCANA_EXECUTION_REFERENCE_INDEX_V1",
        "generated_utc": now,
        "repository_head": head,
        "purpose": (
            "Reusable lookup surface for README/status/contracts/audits, "
            "execution runners, configs, manifests and result summaries "
            "that may be required by future replay/regression tests."
        ),
        "record_count": len(records),
        "category_counts": dict(sorted(category_counts.items())),
        "stage_counts": dict(sorted(stage_counts.items())),
        "records": records,
    }

    JSON_OUT.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    lines: list[str] = []
    lines.append("# ARCANA Execution & Reference Index")
    lines.append("")
    lines.append(
        "Machine-readable companion: `ARCANA_EXECUTION_REFERENCE_INDEX.json`."
    )
    lines.append("")
    lines.append(f"- Repository HEAD at generation: `{head}`")
    lines.append(f"- Generated UTC: `{now}`")
    lines.append(f"- Indexed reference files: **{len(records)}**")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append(
        "This index links historical documentation and execution surfaces "
        "that may be needed for future replay, regression, provenance or "
        "semantic tests. It intentionally indexes README/status/contracts/"
        "audits together with PowerShell/Python runners, configs, manifests "
        "and compact result summaries."
    )
    lines.append("")
    lines.append(
        "The index is navigational evidence only. It does not promote an "
        "indexed file to scientific or canonical authority."
    )
    lines.append("")
    lines.append("## Category counts")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|---|---:|")
    for key, value in sorted(category_counts.items()):
        lines.append(f"| {md_escape(key)} | {value} |")
    lines.append("")
    lines.append("## Stage index")
    lines.append("")

    for stage in sorted(grouped):
        lines.append(f"### {stage}")
        lines.append("")
        lines.append("| Kind | Path | Title | Git blob | SHA256 |")
        lines.append("|---|---|---|---|---|")

        for r in grouped[stage]:
            blob = r["git_blob_oid"] or "UNTRACKED_AT_GENERATION"
            title = r["title"] or ""
            lines.append(
                "| "
                + md_escape(r["category"])
                + " | `"
                + r["path"]
                + "` | "
                + md_escape(title)
                + " | `"
                + blob
                + "` | `"
                + r["sha256"]
                + "` |"
            )

        lines.append("")

    lines.append("## Regeneration")
    lines.append("")
    lines.append(
        "Run `python tools/build_arcana_execution_reference_index.py` "
        "from the repository root after adding significant new execution "
        "or reference surfaces."
    )
    lines.append("")

    MD_OUT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": "PASS_ARCANA_EXECUTION_REFERENCE_INDEX_BUILT",
                "repository_head": head,
                "record_count": len(records),
                "markdown": str(MD_OUT),
                "json": str(JSON_OUT),
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'@ | Set-Content -LiteralPath $IndexBuilder -Encoding UTF8

# ----------------------------------------------------------------------------
# B7-A1 authority/schema/coverage preflight
# ----------------------------------------------------------------------------

$B7Runner = Join-Path $Repo "R5_17_B7_A1_NATURAL_FOOD_SUPPORT_PREFLIGHT.py"

@'
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "R5_17_B7_A1_NATURAL_FOOD_SUPPORT_AUTHORITY_PREFLIGHT.json"

A1 = ROOT / "references" / "v0_6D1_R3" / "FULL_A1_REFERENCE_210_0Ma.npz"
A1_SHA256 = "9469118bff69cfc4a5bbfe398f382224f887d81a69581e3a654d08ea11fc604f"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def git_paths() -> list[str]:
    cp = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return sorted(set(cp.stdout.splitlines()))


def path_group(
    paths: list[str],
    patterns: tuple[str, ...],
    suffixes: tuple[str, ...] | None = None,
) -> list[str]:
    out: list[str] = []

    for p in paths:
        low = p.lower()

        if suffixes is not None:
            if Path(low).suffix not in suffixes:
                continue

        if any(re.search(pattern, p, flags=re.IGNORECASE) for pattern in patterns):
            out.append(p)

    return sorted(set(out))


def summarize_paths(paths: list[str], limit: int = 250) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []

    for p in paths[:limit]:
        path = ROOT / p
        if not path.is_file():
            continue

        docs.append(
            {
                "path": p,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    return docs


def npz_schema(path: Path) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "path": rel(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "keys": [],
        "arrays": {},
    }

    with np.load(path, allow_pickle=False) as z:
        doc["keys"] = list(z.files)

        for key in z.files:
            arr = np.asarray(z[key])

            item: dict[str, Any] = {
                "shape": list(arr.shape),
                "dtype": str(arr.dtype),
                "size": int(arr.size),
            }

            if arr.size and np.issubdtype(arr.dtype, np.number):
                finite = np.isfinite(arr)
                item["finite"] = bool(finite.all())

                if finite.any():
                    vals = arr[finite].astype(np.float64, copy=False)
                    item["min"] = float(vals.min())
                    item["max"] = float(vals.max())

            doc["arrays"][key] = item

    return doc


def content_hits(
    paths: list[str],
    terms: tuple[str, ...],
    max_files: int = 400,
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []

    for p in paths:
        if len(hits) >= max_files:
            break

        path = ROOT / p

        if path.suffix.lower() not in {
            ".py", ".md", ".txt", ".json", ".csv", ".ps1"
        }:
            continue

        try:
            text = path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError:
            continue

        present = [
            term
            for term in terms
            if term.lower() in text.lower()
        ]

        if present:
            hits.append(
                {
                    "path": p,
                    "matched_terms": present,
                }
            )

    return hits


def main() -> int:
    paths = git_paths()
    checks: dict[str, bool] = {}

    # ------------------------------------------------------------------------
    # A1 inherited trophic resource authority
    # ------------------------------------------------------------------------

    checks["a1_present"] = A1.is_file()

    a1_doc: dict[str, Any] | None = None

    if A1.is_file():
        a1_doc = npz_schema(A1)

        checks["a1_known_sha"] = (
            a1_doc["sha256"].lower() == A1_SHA256
        )

        required = (
            "age_ma",
            "browse_forage",
            "low_forage",
            "wetland_forage",
            "total_edible_forage",
        )

        checks["a1_required_channels_present"] = all(
            key in a1_doc["keys"]
            for key in required
        )

        if checks["a1_required_channels_present"]:
            with np.load(A1, allow_pickle=False) as z:
                browse = np.asarray(z["browse_forage"], dtype=np.float64)
                low = np.asarray(z["low_forage"], dtype=np.float64)
                wet = np.asarray(z["wetland_forage"], dtype=np.float64)
                total = np.asarray(z["total_edible_forage"], dtype=np.float64)

                closure = browse + low + wet
                delta = total - closure

                max_abs = float(np.max(np.abs(delta)))

                checks["a1_forage_closure_consistent"] = bool(
                    np.allclose(
                        total,
                        closure,
                        rtol=1e-6,
                        atol=1e-6,
                    )
                )

                a1_doc["forage_closure"] = {
                    "max_abs_error": max_abs,
                    "rtol": 1e-6,
                    "atol": 1e-6,
                    "consistent": checks["a1_forage_closure_consistent"],
                }

                a1_doc["age_ma_values"] = (
                    np.asarray(z["age_ma"], dtype=float).tolist()
                )
    else:
        checks["a1_known_sha"] = False
        checks["a1_required_channels_present"] = False
        checks["a1_forage_closure_consistent"] = False

    # ------------------------------------------------------------------------
    # R3.33 environmental authority discovery
    # ------------------------------------------------------------------------

    r333 = path_group(
        paths,
        (
            r"R3[_-]33",
            r"r333",
            r"holocene.*environment.*domest",
        ),
    )

    checks["r333_authority_surface_found"] = bool(r333)

    # ------------------------------------------------------------------------
    # R3.34 producer authority discovery
    # ------------------------------------------------------------------------

    r334 = path_group(
        paths,
        (
            r"R3[_-]34",
            r"r334",
            r"producer.*domest",
        ),
    )

    checks["r334_authority_surface_found"] = bool(r334)

    # ------------------------------------------------------------------------
    # H0 wild-fauna / present-biology authority discovery
    # ------------------------------------------------------------------------

    h0 = path_group(
        paths,
        (
            r"R3[_-]19",
            r"R3[_-]21",
            r"R3[_-]22",
            r"R3[_-]23",
            r"H0.*PRESENT",
            r"PRESENT.*LINEAGE",
            r"FUNCTIONAL.*PHENOTYPE",
            r"FUNCTIONAL.*ENSEMBLE",
        ),
    )

    checks["h0_faunal_authority_surface_found"] = bool(h0)

    # ------------------------------------------------------------------------
    # Semantic source evidence
    # ------------------------------------------------------------------------

    forage_source_hits = content_hits(
        paths,
        (
            "browse_forage",
            "low_forage",
            "wetland_forage",
            "total_edible_forage",
        ),
    )

    producer_source_hits = content_hits(
        paths,
        (
            "resource_abundance",
            "harvest_return",
            "propagation_opportunity",
            "build_producer_landscape",
        ),
    )

    human_conditioning_hits = content_hits(
        paths,
        (
            "contact_opportunity",
            "subsistence readiness",
            "landscape management",
        ),
    )

    checks["forage_semantic_source_hits_found"] = bool(forage_source_hits)
    checks["producer_semantic_source_hits_found"] = bool(producer_source_hits)

    # ------------------------------------------------------------------------
    # Aquatic / marine discovery
    # ------------------------------------------------------------------------

    marine_name_hits = path_group(
        paths,
        (
            r"marine",
            r"aquatic",
            r"fish",
            r"ocean",
            r"coastal.*resource",
        ),
    )

    marine_content_hits = content_hits(
        paths,
        (
            "marine resource",
            "aquatic resource",
            "fish biomass",
            "marine productivity",
            "aquatic exploitation",
        ),
    )

    # ------------------------------------------------------------------------
    # Decision
    # ------------------------------------------------------------------------

    required_checks = (
        "a1_present",
        "a1_known_sha",
        "a1_required_channels_present",
        "a1_forage_closure_consistent",
        "r333_authority_surface_found",
        "r334_authority_surface_found",
        "h0_faunal_authority_surface_found",
    )

    core_ok = all(checks[name] for name in required_checks)

    if core_ok:
        status = (
            "PASS_R517_B7_A1_NATURAL_FOOD_SUPPORT_"
            "AUTHORITY_SCHEMA_COVERAGE_PREFLIGHT"
        )
        decision = (
            "AUTHORIZE_B7_A2_SEMANTIC_BINDING_"
            "AND_TEMPORAL_COVERAGE_ADJUDICATION"
        )
    else:
        status = (
            "BLOCKED_R517_B7_A1_REQUIRED_AUTHORITY_SURFACE_INCOMPLETE"
        )
        decision = (
            "RECOVER_OR_ADJUDICATE_MISSING_AUTHORITY_BEFORE_B7_A2"
        )

    result = {
        "schema": "ARCANA_R517_B7_A1_NATURAL_FOOD_SUPPORT_PREFLIGHT_V2",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B7-A1",
        "status": status,
        "decision": decision,
        "checks": checks,
        "a1_native_trophic_authority": a1_doc,
        "r333_authority_surface": summarize_paths(r333),
        "r334_authority_surface": summarize_paths(r334),
        "h0_faunal_authority_surface": summarize_paths(h0),
        "semantic_source_hits": {
            "forage": forage_source_hits,
            "producer": producer_source_hits,
            "human_conditioning": human_conditioning_hits,
        },
        "aquatic_marine_discovery": {
            "filename_hits": summarize_paths(marine_name_hits),
            "content_hits": marine_content_hits,
            "materialization_decision": (
                "UNADJUDICATED_SOURCE_DISCOVERY_ONLY"
            ),
        },
        "governance": {
            "natural_pre_management_only": True,
            "r332_readiness_used": False,
            "human_technology_used": False,
            "food_processing_used": False,
            "storage_used": False,
            "landscape_management_used": False,
            "domestication_used": False,
            "agriculture_used": False,
            "population_target_used": False,
            "k_x_t_materialized": False,
            "new_food_equation_materialized": False,
            "canonical_mutation": False,
            "external_engine_executed": False,
            "a1_forage_interpreted_as_physical_biomass": False,
            "a1_forage_interpreted_as_human_calories": False,
            "r333_domestication_candidate_subset_used_as_total_wild_fauna": False,
            "r334_propagation_opportunity_used_as_natural_food_support": False,
        },
    }

    OUT.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": status,
                "decision": decision,
                "checks_passed": sum(bool(v) for v in checks.values()),
                "checks_total": len(checks),
                "r333_surface_count": len(r333),
                "r334_surface_count": len(r334),
                "h0_surface_count": len(h0),
                "marine_filename_hits": len(marine_name_hits),
                "marine_content_hits": len(marine_content_hits),
                "output": str(OUT),
            },
            indent=2,
        )
    )

    return 0 if core_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
'@ | Set-Content -LiteralPath $B7Runner -Encoding UTF8

# ----------------------------------------------------------------------------
# Current-state transition
# ----------------------------------------------------------------------------

$CurrentState = Join-Path $Repo "ARCANA_WORLD_CURRENT_STATE.md"

if (-not (Test-Path $CurrentState -PathType Leaf)) {
    throw "Missing ARCANA_WORLD_CURRENT_STATE.md"
}

$StateText = [System.IO.File]::ReadAllText(
    $CurrentState,
    [System.Text.Encoding]::UTF8
)

$Begin = "<!-- R517_B6_TO_B7_TRANSITION_BEGIN -->"
$End   = "<!-- R517_B6_TO_B7_TRANSITION_END -->"

$Transition = @"
$Begin

## R5.17 authoritative subphase transition - B6 -> B7

This block supersedes earlier R5.17 subphase-status statements in this file.

STAGE: v0.6D1-R5.17
STAGE_STATUS: ACTIVE

R5_17_LATEST_COMPLETED_SUBPHASE: R5.17-B6
R5_17_B6_STATUS: COMPLETED
R5_17_B6_SEALED: false

FRESHWATER_SUPPORT_MATERIALIZED: true
HYDROLOGICAL_RELIABILITY_MATERIALIZED: true
K_X_T_MATERIALIZED: false

R5_17_ACTIVE_SUBPHASE: R5.17-B7
R5_17_ACTIVE_SCOPE: NATURAL_BIOLOGICAL_FOOD_SUPPORT
R5_17_B7_STATUS: AUTHORIZED_ACTIVE

NEXT_OPERATION:
  R5.17-B7-A1
  NATURAL_FOOD_SUPPORT_SOURCE_AUTHORITY_SCHEMA_COVERAGE_PREFLIGHT

EXECUTION_REFERENCE_INDEX:
  ARCANA_EXECUTION_REFERENCE_INDEX.md
  ARCANA_EXECUTION_REFERENCE_INDEX.json
  tools/build_arcana_execution_reference_index.py

MICRO_SEAL_CREATED: false
CANONICAL_MUTATION: false

B7 must construct the natural biological-resource layer before any application
of human technology, processing, storage, management, domestication,
agriculture or civilization dynamics.

The inherited A1 forage vector is authorized only as a trophic-resource proxy.
Its original generator is not recoverable from available repository Git
history and it must not be relabelled as physical biomass, human calories or
carrying capacity.

$End
"@

$Pattern = (
    "(?s)" +
    [regex]::Escape($Begin) +
    ".*?" +
    [regex]::Escape($End)
)

if ([regex]::IsMatch($StateText, $Pattern)) {
    $StateText = [regex]::Replace(
        $StateText,
        $Pattern,
        [System.Text.RegularExpressions.MatchEvaluator]{
            param($m)
            $Transition
        }
    )
}
else {
    $StateText = (
        $StateText.TrimEnd() +
        "`r`n`r`n---`r`n`r`n" +
        $Transition +
        "`r`n"
    )
}

Set-Content `
    -LiteralPath $CurrentState `
    -Value $StateText `
    -Encoding UTF8

# ----------------------------------------------------------------------------
# Run B7-A1
# ----------------------------------------------------------------------------

Write-Host ""
Write-Host "============================================================"
Write-Host " RUN R5.17-B7-A1"
Write-Host "============================================================"

python .\R5_17_B7_A1_NATURAL_FOOD_SUPPORT_PREFLIGHT.py
$B7Exit = $LASTEXITCODE

$B7Output = Join-Path `
    $Repo `
    "R5_17_B7_A1_NATURAL_FOOD_SUPPORT_AUTHORITY_PREFLIGHT.json"

if (-not (Test-Path $B7Output -PathType Leaf)) {
    throw "B7-A1 output missing."
}

$B7 = Get-Content $B7Output -Raw | ConvertFrom-Json

Write-Host ""
Write-Host "=== B7-A1 RESULT ==="

[pscustomobject]@{
    Status             = $B7.status
    Decision           = $B7.decision
    ChecksPassed       = @(
        $B7.checks.PSObject.Properties |
            Where-Object { $_.Value -eq $true }
    ).Count
    ChecksTotal        = @($B7.checks.PSObject.Properties).Count
    R333Surface        = @($B7.r333_authority_surface).Count
    R334Surface        = @($B7.r334_authority_surface).Count
    H0Surface          = @($B7.h0_faunal_authority_surface).Count
    MarineFilenameHits = @(
        $B7.aquatic_marine_discovery.filename_hits
    ).Count
    KMaterialized      = $B7.governance.k_x_t_materialized
} | Format-List

if ($B7Exit -ne 0) {
    Write-Host ""
    Write-Host "B7-A1 is BLOCKED."
    Write-Host "The evidence files were generated, but nothing will be staged."
    Write-Host "Inspect:"
    Write-Host "  $B7Output"
    exit $B7Exit
}

# ----------------------------------------------------------------------------
# Promote current-state metadata to B7-A1 complete / B7-A2 ready
# ----------------------------------------------------------------------------

$StateText = [System.IO.File]::ReadAllText(
    $CurrentState,
    [System.Text.Encoding]::UTF8
)

$StateText = [regex]::Replace(
    $StateText,
    "(?m)^LATEST_COMPLETED_INTERNAL_STEP:.*$",
    "LATEST_COMPLETED_INTERNAL_STEP: R5.17-B7-A1",
    1
)

$StateText = [regex]::Replace(
    $StateText,
    "(?m)^LATEST_INTERNAL_VERDICT:.*$",
    ("LATEST_INTERNAL_VERDICT: " + $B7.status),
    1
)

$StateText = [regex]::Replace(
    $StateText,
    "(?m)^ACTIVE_SUBPHASE:.*$",
    "ACTIVE_SUBPHASE: R5.17-B7",
    1
)

$StateText = [regex]::Replace(
    $StateText,
    "(?m)^ACTIVE_SUBPHASE_STATUS:.*$",
    "ACTIVE_SUBPHASE_STATUS: A1_PREFLIGHT_COMPLETE__A2_READY",
    1
)

$StateText = [regex]::Replace(
    $StateText,
    "(?m)^ACTIVE_SUBPHASE_SCOPE:.*$",
    "ACTIVE_SUBPHASE_SCOPE: NATURAL_BIOLOGICAL_FOOD_SUPPORT",
    1
)

$StateText = [regex]::Replace(
    $StateText,
    "(?m)^NEXT_ACTION:.*$",
    "NEXT_ACTION: RUN_B7_A2_SEMANTIC_BINDING_AND_TEMPORAL_COVERAGE_ADJUDICATION",
    1
)

$StateText = $StateText.Replace(
    "R5_17_B7_STATUS: AUTHORIZED_ACTIVE",
    "R5_17_B7_STATUS: ACTIVE__A1_COMPLETE"
)

$StateText = $StateText.Replace(
    "NEXT_OPERATION:`r`n  R5.17-B7-A1`r`n  NATURAL_FOOD_SUPPORT_SOURCE_AUTHORITY_SCHEMA_COVERAGE_PREFLIGHT",
    "NEXT_OPERATION:`r`n  R5.17-B7-A2`r`n  SEMANTIC_BINDING_AND_TEMPORAL_COVERAGE_ADJUDICATION"
)

$StateText = $StateText.Replace(
    "NEXT_OPERATION:`n  R5.17-B7-A1`n  NATURAL_FOOD_SUPPORT_SOURCE_AUTHORITY_SCHEMA_COVERAGE_PREFLIGHT",
    "NEXT_OPERATION:`n  R5.17-B7-A2`n  SEMANTIC_BINDING_AND_TEMPORAL_COVERAGE_ADJUDICATION"
)

Set-Content `
    -LiteralPath $CurrentState `
    -Value $StateText.TrimEnd() `
    -Encoding UTF8

# ----------------------------------------------------------------------------
# Register B6 evidence without committing heavyweight reconstructed payloads
# ----------------------------------------------------------------------------

$GitVisiblePaths = @(
    git ls-files --cached --others --exclude-standard
)

$B6TopLevelRel = @(
    $GitVisiblePaths |
        Where-Object {
            $_ -match "(?i)^R5_17_B6_[^/]+$" -and
            $_ -notmatch "(?i)^R5_17_B6_(CLOSE|RECOVER).*INDEX"
        } |
        Sort-Object -Unique
)

$B6TopLevelFiles = @(
    $B6TopLevelRel |
        ForEach-Object {
            $Candidate = Join-Path $Repo $_
            if (Test-Path $Candidate -PathType Leaf) {
                Get-Item -LiteralPath $Candidate
            }
        } |
        Sort-Object FullName -Unique
)

$B6PayloadDirs = @(
    Get-ChildItem -LiteralPath $Repo -Force -Directory |
        Where-Object {
            $_.Name -match "(?i)^R5_17_B6_"
        } |
        Sort-Object FullName -Unique
)

$B6PayloadFiles = @()

foreach ($Dir in $B6PayloadDirs) {
    $B6PayloadFiles += @(
        Get-ChildItem -LiteralPath $Dir.FullName -Recurse -File
    )
}

$B6PayloadFiles = @(
    $B6PayloadFiles |
        Sort-Object FullName -Unique
)

function Get-RepoRelativePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FullName
    )

    $Prefix = $RepoNorm + "\"

    if (-not $FullName.StartsWith(
        $Prefix,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw "Path is outside repository root: $FullName"
    }

    return $FullName.Substring($Prefix.Length).Replace("\", "/")
}

$CompactB6Bytes = 0L
$MaxCompactB6Bytes = 0L

foreach ($File in $B6TopLevelFiles) {
    $CompactB6Bytes += [int64]$File.Length

    if ([int64]$File.Length -gt $MaxCompactB6Bytes) {
        $MaxCompactB6Bytes = [int64]$File.Length
    }
}

$PayloadB6Bytes = 0L
$MaxPayloadB6Bytes = 0L

foreach ($File in $B6PayloadFiles) {
    $PayloadB6Bytes += [int64]$File.Length

    if ([int64]$File.Length -gt $MaxPayloadB6Bytes) {
        $MaxPayloadB6Bytes = [int64]$File.Length
    }
}

Write-Host ""
Write-Host "============================================================"
Write-Host " B6 EVIDENCE REGISTRATION SURFACE"
Write-Host "============================================================"
Write-Host "Compact top-level files = $($B6TopLevelFiles.Count)"
Write-Host "Compact total MiB       = $([math]::Round($CompactB6Bytes / 1MB, 2))"
Write-Host "Compact max MiB         = $([math]::Round($MaxCompactB6Bytes / 1MB, 2))"
Write-Host "Derived payload files   = $($B6PayloadFiles.Count)"
Write-Host "Derived payload MiB     = $([math]::Round($PayloadB6Bytes / 1MB, 2))"
Write-Host "Derived max MiB         = $([math]::Round($MaxPayloadB6Bytes / 1MB, 2))"

if ($MaxCompactB6Bytes -gt 95MB) {
    throw "STOP: a compact B6 authority/evidence file exceeds the 95 MiB safety gate."
}

if ($CompactB6Bytes -gt 250MB) {
    throw "STOP: compact B6 authority/evidence exceeds the 250 MiB staging safety gate."
}

# Heavy reconstructed/derived directories are intentionally not added to normal
# Git. They are reproducible execution products. Preserve their exact local
# identity in a committed manifest instead of forcing >100 MiB blobs into the
# repository history.

$ManifestRecords = @()

foreach ($File in $B6TopLevelFiles) {
    $ManifestRecords += [pscustomobject]@{
        path = (Get-RepoRelativePath -FullName $File.FullName)
        class = "COMMITTABLE_CONTROL_PLANE_EVIDENCE"
        size_bytes = [int64]$File.Length
        sha256 = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        repository_disposition = "STAGE_IN_NORMAL_GIT"
    }
}

foreach ($File in $B6PayloadFiles) {
    $ManifestRecords += [pscustomobject]@{
        path = (Get-RepoRelativePath -FullName $File.FullName)
        class = "DERIVED_RECONSTRUCTED_PAYLOAD"
        size_bytes = [int64]$File.Length
        sha256 = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        repository_disposition = "LOCAL_REPRODUCIBLE_PAYLOAD_NOT_STAGED_IN_NORMAL_GIT"
    }
}

$B6EvidenceManifestPath = Join-Path $Repo "R5_17_B6_EVIDENCE_MANIFEST.json"

$B6EvidenceManifest = [ordered]@{
    schema = "ARCANA_R517_B6_EVIDENCE_MANIFEST_V1"
    stage = "v0.6D1-R5.17"
    subphase = "R5.17-B6"
    status = "B6_COMPLETED_EVIDENCE_REGISTERED"
    repository_head_before_transition = $Head
    policy = [ordered]@{
        compact_control_plane_evidence = "COMMIT_IN_NORMAL_GIT"
        reconstructed_payloads = "HASH_REGISTER_ONLY"
        reason = "Avoid heavyweight generated payloads in normal Git history while preserving exact identity and replay provenance."
        future_remote_payload_option = "GIT_LFS_OR_EXTERNAL_ARTIFACT_STORAGE_IF_EXPLICITLY_AUTHORIZED"
    }
    counts = [ordered]@{
        compact_files = $B6TopLevelFiles.Count
        payload_files = $B6PayloadFiles.Count
        total_files = ($B6TopLevelFiles.Count + $B6PayloadFiles.Count)
    }
    bytes = [ordered]@{
        compact_total = $CompactB6Bytes
        payload_total = $PayloadB6Bytes
        payload_max_file = $MaxPayloadB6Bytes
    }
    records = @(
        $ManifestRecords |
            Sort-Object path
    )
}

$B6EvidenceManifest |
    ConvertTo-Json -Depth 8 |
    Set-Content -LiteralPath $B6EvidenceManifestPath -Encoding UTF8

Write-Host "Evidence manifest       = R5_17_B6_EVIDENCE_MANIFEST.json"
Write-Host "Payload staging policy  = HASH_REGISTER_ONLY"

# ----------------------------------------------------------------------------
# Stage compact B6 authority/evidence plus B7-A1 before index generation
# ----------------------------------------------------------------------------

Write-Host ""
Write-Host "============================================================"
Write-Host " STAGE COMPACT B6 EVIDENCE + B7-A1 CORE"
Write-Host "============================================================"

$B6CompactRel = @(
    $B6TopLevelFiles |
        ForEach-Object {
            Get-RepoRelativePath -FullName $_.FullName
        } |
        Where-Object {
            $_ -ne $SelfRel
        } |
        Sort-Object -Unique
)

$CoreExpected = @(
    $SelfRel,
    "ARCANA_WORLD_CURRENT_STATE.md",
    "R5_17_B6_COMPLETION_REGISTER.md",
    "R5_17_B6_EVIDENCE_MANIFEST.json",
    "R5_17_B7_A1_FORAGE_PROVENANCE_DISPOSITION.md",
    "R5_17_B7_BIOLOGICAL_FOOD_SUPPORT_CONTRACT.md",
    "R5_17_B7_A1_NATURAL_FOOD_SUPPORT_PREFLIGHT.py",
    "R5_17_B7_A1_NATURAL_FOOD_SUPPORT_AUTHORITY_PREFLIGHT.json",
    "tools/build_arcana_execution_reference_index.py"
)

$StageTargets = @(
    $CoreExpected + $B6CompactRel |
        Sort-Object -Unique
)

$StageSucceeded = $false
$AddDelays = @(2, 4, 8, 15, 30)

for ($Attempt = 1; $Attempt -le 6; $Attempt++) {
    Write-Host "git add attempt $Attempt/6"

    $OldEA = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    git add -- $StageTargets
    $AddExit = $LASTEXITCODE

    $ErrorActionPreference = $OldEA

    if ($AddExit -eq 0) {
        $StageSucceeded = $true
        break
    }

    if ($Attempt -lt 6) {
        $Delay = $AddDelays[$Attempt - 1]
        Write-Host "git add failed; waiting $Delay seconds before retry."
        Start-Sleep -Seconds $Delay
    }
}

if (-not $StageSucceeded) {
    throw "Failed to stage compact B6/B7 transition surface after 6 attempts."
}

$StagedCore = @(git diff --cached --name-only)

foreach ($File in $CoreExpected) {
    if ($File -notin $StagedCore) {
        throw "Expected core staged file missing: $File"
    }
}

# Explicitly forbid derived B6 payload directories from entering the index.
$StagedPayloads = @(
    $StagedCore |
        Where-Object {
            $_ -match "(?i)^R5_17_B6_.+/"
        }
)

if ($StagedPayloads.Count -gt 0) {
    Write-Host "Derived B6 payloads were staged unexpectedly:"
    $StagedPayloads
    throw "STOP: derived/reconstructed B6 payloads must remain hash-registered only."
}

$UnexpectedCore = @(
    $StagedCore |
        Where-Object {
            (
                $_ -notin $CoreExpected
            ) -and (
                $_ -notin $B6CompactRel
            )
        }
)

if ($UnexpectedCore.Count -gt 0) {
    Write-Host "Unexpected files staged before index generation:"
    $UnexpectedCore
    throw "STOP: staging escaped the compact B6/B7 authority surface."
}

# ----------------------------------------------------------------------------
# Build execution/reference index
# ----------------------------------------------------------------------------

Write-Host ""
Write-Host "============================================================"
Write-Host " BUILD EXECUTION / REFERENCE INDEX"
Write-Host "============================================================"

python .\tools\build_arcana_execution_reference_index.py

if ($LASTEXITCODE -ne 0) {
    throw "Reference-index builder failed."
}

$IndexMd = Join-Path $Repo "ARCANA_EXECUTION_REFERENCE_INDEX.md"
$IndexJson = Join-Path $Repo "ARCANA_EXECUTION_REFERENCE_INDEX.json"

if (-not (Test-Path $IndexMd -PathType Leaf)) {
    throw "Reference markdown index was not generated."
}

if (-not (Test-Path $IndexJson -PathType Leaf)) {
    throw "Reference JSON index was not generated."
}

$OldEA = $ErrorActionPreference
$ErrorActionPreference = "Continue"

git add -- `
    "ARCANA_EXECUTION_REFERENCE_INDEX.md" `
    "ARCANA_EXECUTION_REFERENCE_INDEX.json"

$IndexAddExit = $LASTEXITCODE
$ErrorActionPreference = $OldEA

if ($IndexAddExit -ne 0) {
    throw "Failed to stage generated reference indexes."
}

$IndexDoc = Get-Content $IndexJson -Raw | ConvertFrom-Json

Write-Host ""
Write-Host "Reference index records = $($IndexDoc.record_count)"

# ----------------------------------------------------------------------------
# Validate exact staged authority surface
# ----------------------------------------------------------------------------

$FinalCore = @(
    $CoreExpected +
    @(
        "ARCANA_EXECUTION_REFERENCE_INDEX.md",
        "ARCANA_EXECUTION_REFERENCE_INDEX.json"
    )
)

$Staged = @(git diff --cached --name-only)

foreach ($File in $FinalCore) {
    if ($File -notin $Staged) {
        throw "Expected final staged file missing: $File"
    }
}

$Unexpected = @(
    $Staged |
        Where-Object {
            (
                $_ -notin $FinalCore
            ) -and (
                $_ -notin $B6CompactRel
            )
        }
)

$FinalStagedPayloads = @(
    $Staged |
        Where-Object {
            $_ -match "(?i)^R5_17_B6_.+/"
        }
)

if ($FinalStagedPayloads.Count -gt 0) {
    Write-Host ""
    Write-Host "Heavy derived B6 payloads staged unexpectedly:"
    $FinalStagedPayloads
    throw "STOP: derived payloads are manifest-registered only."
}

if ($Unexpected.Count -gt 0) {
    Write-Host ""
    Write-Host "Unexpected staged files:"
    $Unexpected
    throw "STOP: unexpected file outside B6/B7 transition surface."
}

Write-Host "PASS: staged surface is restricted to B6 evidence and B7 transition authority."

# ----------------------------------------------------------------------------
# Final review - NO COMMIT / NO PUSH
# ----------------------------------------------------------------------------

Write-Host ""
Write-Host "============================================================"
Write-Host " FINAL REVIEW"
Write-Host "============================================================"

git diff --cached --stat

Write-Host ""
Write-Host "=== STAGED FILES ==="
git diff --cached --name-status

Write-Host ""
Write-Host "=== CURRENT HEAD ==="
git rev-parse HEAD

Write-Host ""
Write-Host "=== B7-A1 ==="
Write-Host "status   = $($B7.status)"
Write-Host "decision = $($B7.decision)"

Write-Host ""
Write-Host "=== REFERENCE INDEX ==="
Write-Host "records  = $($IndexDoc.record_count)"
Write-Host "markdown = ARCANA_EXECUTION_REFERENCE_INDEX.md"
Write-Host "json     = ARCANA_EXECUTION_REFERENCE_INDEX.json"

Write-Host ""
Write-Host "=== B6 EVIDENCE POLICY ==="
Write-Host "compact staged files = $($B6CompactRel.Count)"
Write-Host "payload files        = $($B6PayloadFiles.Count)"
Write-Host "payload MiB          = $([math]::Round($PayloadB6Bytes / 1MB, 2))"
Write-Host "payload disposition  = HASH_REGISTER_ONLY"
Write-Host "ignored logs         = EXCLUDED_BY_GITIGNORE"
Write-Host "git object policy    = NEW_OBJECT_PREFLIGHT_WITH_BACKOFF"
Write-Host "manifest             = R5_17_B6_EVIDENCE_MANIFEST.json"

Write-Host ""
Write-Host "=== REMAINING UNTRACKED (NOT STAGED) ==="
$RemainingUntracked = @(git ls-files --others --exclude-standard)
if ($RemainingUntracked.Count -eq 0) {
    Write-Host "[none]"
}
else {
    $RemainingUntracked | Select-Object -First 80
    if ($RemainingUntracked.Count -gt 80) {
        Write-Host "... $($RemainingUntracked.Count - 80) more untracked paths omitted"
    }
}

Write-Host ""
Write-Host "============================================================"
Write-Host " READY FOR MANUAL COMMIT / PUSH"
Write-Host "============================================================"
Write-Host ""
Write-Host 'Recommended commands:'
Write-Host '  git diff --cached --stat'
Write-Host '  git diff --cached -- ARCANA_WORLD_CURRENT_STATE.md'
Write-Host '  git commit -m "Complete R5.17 B6 and open B7 biological food support"'
Write-Host '  git push origin main'
