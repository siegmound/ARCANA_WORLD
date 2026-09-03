from __future__ import annotations

from pathlib import Path
import hashlib
import json
import shutil

STAGE = "v0.6D1-R4.54-R1"
PRE_SHA = "46251558cc7d373aff56707dc783b4cacc32b2fcbcf8a6a735ee998b88fe1067"
POST_SHA = "9f8e09c2122b41cab224412b478adfd1e1e816122a2b2652a3c8668246feeaf8"
TARGET = Path("capture_v0_6D1_R4_54_dry_runs.ps1")
MANIFEST = Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_54.json")
OUT = Path("outputs/v0_6D1_R4_54_R1")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preserve(root: Path) -> None:
    dst = root / OUT / "PREPATCH_FAILED_EVIDENCE"
    dst.mkdir(parents=True, exist_ok=True)
    candidates = [
        root / "outputs/v0_6D1_R4_54/R4_54_RUNTIME_IDENTITY_EVIDENCE.json",
        root / "outputs/v0_6D1_R4_54/R4_54_HOST_DRY_RUN_EVIDENCE.json",
        root / "outputs/v0_6D1_R4_54/dry_runs/Madingley.json",
    ]
    for p in candidates:
        if p.exists():
            q = dst / p.name
            if not q.exists():
                shutil.copy2(p, q)

    work = root / "outputs/v0_6D1_R4_54/runtime_work/Madingley"
    if work.exists():
        q = dst / "Madingley_runtime_work"
        if not q.exists():
            shutil.copytree(work, q)

    src_dst = root / OUT / "PREPATCH_SOURCE"
    src_dst.mkdir(parents=True, exist_ok=True)
    target = root / TARGET
    if target.exists() and sha(target) == PRE_SHA:
        shutil.copy2(target, src_dst / TARGET.name)


def patch_text(s: str) -> str:
    old = '    return [ordered]@{engine=$Engine;status="FAIL";returncode=[int]$Exec.ExitCode;metrics=@();artifact_hashes=@{};error="missing/unparseable result"}\n'
    new = '    return [pscustomobject][ordered]@{engine=$Engine;status="FAIL";returncode=[int]$Exec.ExitCode;metrics=@();artifact_hashes=@{};error="missing/unparseable result"}\n'
    if old not in s:
        raise RuntimeError("R454_R1_MISSING_READRESULT_FALLBACK_ANCHOR")
    s = s.replace(old, new, 1)

    anchor = '  $x | Add-Member -NotePropertyName bridge_exit_code -NotePropertyValue ([int]$Exec.ExitCode) -Force\n  return $x\n}\n'
    helper = anchor + 'function Set-ArtifactHashes([object]$Row,[object]$Hashes){\n  if($null -eq $Row){ throw "Cannot materialize artifact_hashes on null dry-run row" }\n  $Row | Add-Member -NotePropertyName artifact_hashes -NotePropertyValue $Hashes -Force\n  return $Row\n}\n'
    if anchor not in s:
        raise RuntimeError("R454_R1_MISSING_READRESULT_HELPER_ANCHOR")
    s = s.replace(anchor, helper, 1)

    replacements = [
        (
            '$r.artifact_hashes=[ordered]@{"dry_run_result_json"=(Get-FileHash -Algorithm SHA256 (Join-Path $Results "Madingley.json")).Hash.ToLowerInvariant()}\n',
            '$r=Set-ArtifactHashes $r ([ordered]@{"dry_run_result_json"=(Get-FileHash -Algorithm SHA256 (Join-Path $Results "Madingley.json")).Hash.ToLowerInvariant()})\n',
        ),
        (
            '$r.artifact_hashes=[ordered]@{"dry_run_result_json"=(Get-FileHash -Algorithm SHA256 (Join-Path $Results "RangeShifter.json")).Hash.ToLowerInvariant()}\n',
            '$r=Set-ArtifactHashes $r ([ordered]@{"dry_run_result_json"=(Get-FileHash -Algorithm SHA256 (Join-Path $Results "RangeShifter.json")).Hash.ToLowerInvariant()})\n',
        ),
        (
            'if($null -ne $qf){\n  $r.artifact_hashes=[ordered]@{"NEMO_NATIVE_QFREQ_OUTPUT"=(Get-FileHash -Algorithm SHA256 $qf.FullName).Hash.ToLowerInvariant()}\n}else{$r.artifact_hashes=@{}}\n',
            'if($null -ne $qf){\n  $r=Set-ArtifactHashes $r ([ordered]@{"NEMO_NATIVE_QFREQ_OUTPUT"=(Get-FileHash -Algorithm SHA256 $qf.FullName).Hash.ToLowerInvariant()})\n}else{\n  $r=Set-ArtifactHashes $r ([ordered]@{})\n}\n',
        ),
    ]
    for old, new in replacements:
        if old not in s:
            raise RuntimeError("R454_R1_MISSING_ARTIFACT_HASH_ASSIGNMENT_ANCHOR")
        s = s.replace(old, new, 1)
    return s


def main() -> int:
    root = Path.cwd()
    target = root / TARGET
    current = sha(target)
    preserve(root)

    if current == PRE_SHA:
        patched = patch_text(target.read_text(encoding="utf-8"))
        target.write_text(patched, encoding="utf-8", newline="\n")
    elif current == POST_SHA:
        pass
    else:
        raise RuntimeError(
            f"R454_R1_SOURCE_HASH_NOT_AUTHORIZED: {current} "
            f"expected pre={PRE_SHA} or post={POST_SHA}"
        )

    actual_post = sha(target)
    if actual_post != POST_SHA:
        raise RuntimeError(
            f"R454_R1_POSTPATCH_HASH_MISMATCH: {actual_post} != {POST_SHA}"
        )

    manifest_path = root / MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    found = False
    for rec in manifest["files"]:
        if rec["path"] == TARGET.as_posix():
            rec["sha256"] = POST_SHA
            rec["bytes"] = target.stat().st_size
            found = True
    if not found:
        raise RuntimeError("R454_R1_TARGET_NOT_FOUND_IN_R454_SOURCE_MANIFEST")
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    result = {
        "stage": STAGE,
        "status": "PASS_R454_R1_POWERSHELL_ARTIFACT_HASH_PROPERTY_REPAIR_APPLIED",
        "prepatch_capture_bridge_sha256": PRE_SHA,
        "postpatch_capture_bridge_sha256": POST_SHA,
        "root_cause": (
            "CONVERTFROM_JSON_PSCUSTOMOBJECT_MISSING_ARTIFACT_HASHES_PROPERTY_"
            "DIRECT_PROPERTY_ASSIGNMENT_THROWS_BEFORE_DRY_RUN_EVIDENCE_CAPTURE"
        ),
        "repair": (
            "MATERIALIZE_ARTIFACT_HASHES_WITH_ADD_MEMBER_FORCE_VIA_SINGLE_"
            "SET_ARTIFACT_HASHES_HELPER_FOR_MADINGLEY_RANGESHIFTER_AND_NEMO"
        ),
        "governance": {
            "failed_r454_attempt_preserved": True,
            "historical_scientific_execution_had_occurred_before_failure": False,
            "scientific_evidence_had_been_created_before_failure": False,
            "dry_run_rerun_authorized": True,
            "scientific_metric_semantics_modified": False,
            "seed_semantics_modified": False,
            "readout_authority_modified": False,
            "numeric_thresholds_added": False,
            "canonical_state_changed": False,
            "gate_weakening_performed": False,
        },
    }
    (root / OUT).mkdir(parents=True, exist_ok=True)
    (root / OUT / "R4_54_R1_REPAIR_APPLICATION.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
