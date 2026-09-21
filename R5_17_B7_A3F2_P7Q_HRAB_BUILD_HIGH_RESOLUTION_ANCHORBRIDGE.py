"""Build the governed P7Q high-resolution AnchorBridge core.

This stage materializes only a temporal clock, a sparse per-cell rule index,
and independently check-pointable interval metadata.  It never backcasts the
0 ka endpoint, interpolates categorical material, resamples spatial data, or
creates a physical-soil state.
"""
from __future__ import annotations

import argparse
import gzip
import io
import hashlib
import json
import subprocess
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
PYTHON = Path(r"F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\_ARCANA_TOOL_ENVS\PRE5I_RASTERIO\Scripts\python.exe")
ANCHORS = [200.0, 125.0, 120.0, 20.0, 15.0, 14.0, 13.0, 12.0, 11.0, 10.0, 5.0, 0.0]
INTERVALS = list(zip(ANCHORS[:-1], ANCHORS[1:]))
EXPECTED_HEAD = "96aaa8c68e7c97607035f606d89c0f06c4ade2dd"
EXPECTED_CLOCK_SHA256 = "16a48a3ec8736b4b6297186222d7274a5ce376085f27bfa9108d7ba5cd0ec99a"
STATIC_SHA256 = "e25cd2b55e34e5b175aaf631849dc319448f8510b83d1407ef9f1ffab0a4caee"
LEDGER_SHA256 = "cadf5bcde2bc7350cd4968e6f65074480aaaf60de2b0943df1604f482bd0a41f"
INDEX_BLOBS = {
    "ARCANA_EXECUTION_REFERENCE_INDEX.json": "551727fd6ea73dd39a4194bf3aa34dc2a2707836",
    "ARCANA_EXECUTION_REFERENCE_INDEX.md": "8a8052c5c2ec73f26c598df5aeb3ab50105da085",
}
STATIC_PATH = Path(r"F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\_ARCANA_EXTERNAL_SOURCES\p7q_parent_state\PRE5I_STATIC_MATERIALIZATION\PRE5I_STATIC_PARENT_STATE_0KA.jsonl.gz")
LEDGER_PATH = Path(r"F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld_ARCANA_EXTERNAL_SOURCES\p7q_parent_state\PRE5N_DECISION_LEDGER\PRE5N_RESIDUAL_CLASSIFIER_DECISIONS_0KA.jsonl.gz")
CLOCK_SOURCE = ROOT / "outputs" / "v0_6D1_R3_28" / "R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz"
PRE5N = ROOT / "R5_17_B7_A3F2_P7Q_PRE5N_ADJUDICATION.json"
P7T = ROOT / "R5_17_B7_A3F2_P7T_HUMAN_SUPPORT_TEMPORAL_SNAPSHOT_AUTHORITY.json"
PRE3 = ROOT / "R5_17_B7_A3F2_P7Q_PRE3_TEMPORAL_PARENT_MATERIAL_RECONSTRUCTION_METHOD_ADJUDICATION.json"
PRE4 = ROOT / "R5_17_B7_A3F2_P7Q_PRE4_HYBRID_TEMPORAL_PARENT_STATE_ADAPTER_SCHEMA_ADJUDICATION.json"
RULES = ROOT / "R5_17_B7_A3F2_P7Q_PRE4_TEMPORAL_PARENT_STATE_RULE_REGISTRY.json"
DRIVER_MATRIX = ROOT / "R5_17_B7_A3F2_P7Q_HRAB_DRIVER_AUTHORITY_MATRIX.json"
STATE = ROOT / "ARCANA_WORLD_CURRENT_STATE.md"
OUT = Path(r"F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld_ARCANA_EXTERNAL_SOURCES\p7q_parent_state\HRAB")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def deterministic_npz(path: Path, arrays: dict[str, np.ndarray]) -> None:
    """Write a timestamp-independent compressed NPZ for repeatable evidence."""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in sorted(arrays):
            payload = io.BytesIO()
            np.lib.format.write_array(payload, np.asarray(arrays[name]), allow_pickle=False)
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            zf.writestr(info, payload.getvalue(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def git_blob(path: str) -> str:
    data = subprocess.check_output(["git", "show", f":{path}"], cwd=ROOT)
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def authority_checks() -> dict:
    for p in (PRE5N, P7T, PRE3, PRE4, RULES, CLOCK_SOURCE, STATIC_PATH, LEDGER_PATH):
        if not p.exists():
            raise RuntimeError(f"missing authority: {p}")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    origin = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip()
    if head != EXPECTED_HEAD or origin != EXPECTED_HEAD:
        raise RuntimeError(f"unexpected Git baseline: HEAD={head} origin/main={origin}")
    for name, expected in INDEX_BLOBS.items():
        actual = git_blob(name)
        if actual != expected:
            raise RuntimeError(f"protected staged blob drift: {name}: {actual}")
    pre5n = json.loads(PRE5N.read_text(encoding="utf-8"))
    required = {
        "contract_valid": True,
        "classifier_executed": True,
        "compatible_records_inspected": 560,
        "static_parent_state_ready_for_anchorbridge": True,
        "readiness_class": "READY_FOR_ENDPOINT_CONSTRAINED_HYBRID_TEMPORAL_ADAPTER_WITH_EXPLICIT_UNKNOWN_MASK",
    }
    for key, value in required.items():
        if pre5n.get(key) != value:
            raise RuntimeError(f"PRE5N failed {key}: {pre5n.get(key)!r}")
    if pre5n.get("assignments") != {"BEDROCK_EXPOSED": 0, "RESIDUAL_REGOLITH": 0, "SAPROLITE_OR_DEEP_WEATHERING": 0}:
        raise RuntimeError("PRE5N assignment invariant failed")
    if sha256(CLOCK_SOURCE) != EXPECTED_CLOCK_SHA256:
        raise RuntimeError("R3.28 clock source hash drift")
    if sha256(STATIC_PATH) != STATIC_SHA256 or sha256(LEDGER_PATH) != LEDGER_SHA256:
        raise RuntimeError("PRE5N payload hash drift")
    p7t = json.loads(P7T.read_text(encoding="utf-8"))
    if p7t["shared_temporal_registry"]["ages_ka_before_model_present"] != ANCHORS:
        raise RuntimeError("P7T anchor registry drift")
    pre3 = json.loads(PRE3.read_text(encoding="utf-8"))
    pre4 = json.loads(PRE4.read_text(encoding="utf-8"))
    if pre3["target_temporal_domain"]["snapshot_ages_ka"] != ANCHORS or pre4["canonical_snapshots"] != ANCHORS:
        raise RuntimeError("PRE3/PRE4 anchor registry drift")
    return {"head": head, "origin_main": origin, "pre5n": pre5n}


def build_clock() -> tuple[np.ndarray, dict]:
    source = np.load(CLOCK_SOURCE, allow_pickle=False)["age_ka"]
    if source.shape != (280,) or not np.isfinite(source).all() or np.any(np.diff(source) >= 0):
        raise RuntimeError("R3.28 age_ka is not a finite strict descending clock")
    if len(np.unique(source)) != len(source) or float(source[0]) != 200.0 or float(source[-1]) != 0.0:
        raise RuntimeError("R3.28 age_ka domain/uniqueness failed")
    presence = {str(a): bool(np.any(source == a)) for a in ANCHORS}
    if not all(presence.values()):
        raise RuntimeError("a governed hard anchor is absent from R3.28; no silent insertion permitted")
    interval_index = []
    point_kind = []
    for age in source.tolist():
        if age in ANCHORS:
            point_kind.append("HARD_ANCHOR")
            interval_index.append(None)
            continue
        found = [i for i, (older, younger) in enumerate(INTERVALS) if older > age > younger]
        if len(found) != 1:
            raise RuntimeError(f"clock point not in exactly one governed interval: {age}")
        point_kind.append("INTERVAL_POINT")
        interval_index.append(found[0])
    clock = source.astype(np.float64, copy=True)
    return clock, {
        "source_path": str(CLOCK_SOURCE),
        "source_sha256": EXPECTED_CLOCK_SHA256,
        "source_age_count": int(source.size),
        "clock_age_count": int(clock.size),
        "age_ka": [float(x) for x in clock],
        "direction": "OLDER_TO_YOUNGER_FORWARD",
        "domain_ka": {"older": 200.0, "younger": 0.0},
        "hard_anchors_ka": ANCHORS,
        "hard_anchor_count": len(ANCHORS),
        "anchor_presence": presence,
        "anchor_insertion": "NONE__ALL_12_PRESENT_EXACTLY",
        "point_kind": point_kind,
        "interval_index": interval_index,
        "interval_count": len(INTERVALS),
        "generic_categorical_interpolation": False,
    }


BRANCH_RULES = {
    "OUTSIDE_SCOPE": ("OUTSIDE_SCOPE", "OUTSIDE_SCOPE", "OUTSIDE_SCOPE"),
    "UNKNOWN_MATERIAL": ("UNKNOWN_PROPAGATION", "UNKNOWN_INITIAL_STATE", "UNKNOWN_PROPAGATION_ONLY"),
    "MARINE_DERIVED_EXPOSED": ("SHORELINE_TRANSITION_V1", "UNKNOWN_INITIAL_STATE", "UNKNOWN_PROPAGATION_ONLY"),
    "TRANSPORTED_ALLUVIAL": ("GUM_AGE_GATED_TRANSPORTED_V1", "AGE_GATED_CANDIDATE", "UNKNOWN_PROPAGATION_ONLY"),
    "GLACIAL_OR_GLACIOFLUVIAL": ("GLACIAL_PERIGLACIAL_V1", "UNKNOWN_INITIAL_STATE", "INSUFFICIENT_AUTHORITY"),
    "COASTAL": ("SHORELINE_TRANSITION_V1", "UNKNOWN_INITIAL_STATE", "UNKNOWN_PROPAGATION_ONLY"),
    "TRANSPORTED_COLLUVIAL": ("GUM_AGE_GATED_TRANSPORTED_V1", "AGE_GATED_CANDIDATE", "UNKNOWN_PROPAGATION_ONLY"),
    "LACUSTRINE": ("LACUSTRINE_WATER_ELIGIBILITY_V1", "UNKNOWN_INITIAL_STATE", "UNKNOWN_PROPAGATION_ONLY"),
    "ORGANIC": ("ORGANIC_V1", "UNKNOWN_INITIAL_STATE", "INSUFFICIENT_AUTHORITY"),
    "TRANSPORTED_AEOLIAN": ("AEOLIAN_V1", "UNKNOWN_INITIAL_STATE", "INSUFFICIENT_AUTHORITY"),
    "EVAPORITIC": ("EVAPORITIC_V1", "UNKNOWN_INITIAL_STATE", "INSUFFICIENT_AUTHORITY"),
    "PYROCLASTIC": ("PYROCLASTIC_V1", "UNKNOWN_INITIAL_STATE", "INSUFFICIENT_AUTHORITY"),
}


def rule_for(record: dict) -> tuple[str, str, str]:
    branch = record.get("material_branch")
    if branch not in BRANCH_RULES:
        raise RuntimeError(f"unmapped static material branch: {branch!r}")
    return BRANCH_RULES[branch]


def build_cell_index() -> tuple[Path, dict]:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "HRAB_CELL_TEMPORAL_RULE_INDEX.jsonl.gz"
    counts = {"records": 0, "unknown": 0, "outside_scope": 0, "preserved_endpoint_only": 0, "conflicts": 0}
    branch_counts = Counter()
    rule_family_counts = Counter()
    initialization_status_counts = Counter()
    forward_status_counts = Counter()
    with path.open("wb") as fileobj:
        with gzip.GzipFile(filename="", mode="wb", fileobj=fileobj, mtime=0) as raw:
            with io.TextIOWrapper(raw, encoding="utf-8", newline="\n") as out:
                with gzip.open(STATIC_PATH, "rt", encoding="utf-8") as source:
                    for line in source:
                        record = json.loads(line)
                        branch_counts[record.get("material_branch")] += 1
                        rule_id, init, status = rule_for(record)
                        rule_family_counts[rule_id] += 1
                        initialization_status_counts[init] += 1
                        forward_status_counts[status] += 1
                        unknown = init == "UNKNOWN_INITIAL_STATE" or status in {"INSUFFICIENT_AUTHORITY", "UNKNOWN_PROPAGATION_ONLY"}
                        if unknown:
                            counts["unknown"] += 1
                        if status == "OUTSIDE_SCOPE":
                            counts["outside_scope"] += 1
                        if rule_id == "UNKNOWN_PROPAGATION":
                            counts["preserved_endpoint_only"] += 1
                        if record.get("conflict_flags"):
                            counts["conflicts"] += 1
                        result = {
                            "cell_id": record["cell_id"],
                            "endpoint_0ka_material_branch": record.get("material_branch"),
                            "endpoint_0ka_support_class": record.get("state_support"),
                            "endpoint_constraint": "CHECK_ONLY__NOT_INITIALIZER_OR_BACKCAST",
                            "source_temporal_rule": record.get("temporal_rule"),
                            "rule_family": rule_id,
                            "initialization_200ka": init,
                            "forward_status": status,
                            "temporal_condition_status": record.get("applicability", {}).get("age_evidence_status"),
                            "independent_temporal_condition_present": bool(record.get("applicability", {}).get("formation_min_ka") is not None or record.get("applicability", {}).get("formation_max_ka") is not None),
                            "land_state_applicability": record.get("land_state"),
                            "formation_interval": record.get("formation_interval"),
                            "applicability": record.get("applicability"),
                            "persistence_authority": False,
                            "unknown_preserved": unknown,
                            "conflict_flags": record.get("conflict_flags", []),
                            "source_provenance": record.get("source_provenance", []),
                            "spatial_policy": "NATIVE_ENDPOINT_SUPPORT_PRESERVED__NO_RESAMPLING",
                        }
                        out.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
                        counts["records"] += 1
    counts["sha256"] = sha256(path)
    counts["bytes"] = path.stat().st_size
    counts["path"] = str(path)
    counts["material_branch_counts"] = dict(sorted(branch_counts.items()))
    counts["rule_family_counts"] = dict(sorted(rule_family_counts.items()))
    counts["initialization_status_counts"] = dict(sorted(initialization_status_counts.items()))
    counts["forward_status_counts"] = dict(sorted(forward_status_counts.items()))
    counts["all_static_material_branches_covered"] = set(branch_counts) == set(BRANCH_RULES)
    counts["unmapped_static_material_branches"] = sorted(set(branch_counts) - set(BRANCH_RULES))
    if not counts["all_static_material_branches_covered"]:
        raise RuntimeError(f"static branch coverage failed: {counts['unmapped_static_material_branches']}")
    return path, counts


def update_state_idempotently() -> None:
    marker = "## R5.17-B7-A3F2-P7Q-HRAB CORE"
    block = marker + "\n\nLATEST_COMPLETED_INTERNAL_STEP: R5.17-B7-A3F2-P7Q-HRAB-CORE\nANCHORBRIDGE_CORE: READY\nFULL_TEMPORAL_PARENT_STATE: PARTIAL_OR_PENDING_DRIVER_BINDING\nP7Q_reopened: false\nphysical_soil_created: false\nscientific_authority_register_mutated: false\n"
    text = STATE.read_text(encoding="utf-8")
    if marker in text:
        start = text.index(marker)
        next_heading = text.find("\n## ", start + len(marker))
        end = len(text) if next_heading < 0 else next_heading
        text = text[:start] + block + text[end:]
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    STATE.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-state-update", action="store_true", help="build evidence without appending current-state status")
    args = parser.parse_args()
    audit = authority_checks()
    clock, clock_manifest = build_clock()
    OUT.mkdir(parents=True, exist_ok=True)
    clock_path = OUT / "HRAB_HIGH_RES_TEMPORAL_CLOCK.npz"
    deterministic_npz(clock_path, {"age_ka": clock, "hard_anchor_ka": np.asarray(ANCHORS), "interval_index": np.asarray([x if x is not None else -1 for x in clock_manifest["interval_index"]], dtype=np.int16)})
    clock_manifest["materialized_clock_path"] = str(clock_path)
    clock_manifest["materialized_clock_sha256"] = sha256(clock_path)
    cell_path, cell_manifest = build_cell_index()
    interval_records = []
    for i, (older, younger) in enumerate(INTERVALS):
        points = [float(x) for x, kind, idx in zip(clock_manifest["age_ka"], clock_manifest["point_kind"], clock_manifest["interval_index"]) if idx == i]
        interval_records.append({"interval_index": i, "older_anchor_ka": older, "younger_anchor_ka": younger, "clock_points_ka": points, "driver_authorities_used": [], "rule_families_active": [], "cells_updated": 0, "cells_state_persisted": 0, "cells_endpoint_metadata_indexed": cell_manifest["records"], "cells_unknown_or_unresolved": cell_manifest["unknown"], "cells_preserved": 0, "conflicts": cell_manifest["conflicts"], "materialized_state_output": False, "status": "CHECKPOINT_ARCHITECTURE_READY__NO_AUTHORIZED_STATE_TRANSITION_EXECUTED"})
    matrix = json.loads(DRIVER_MATRIX.read_text(encoding="utf-8"))
    matrix_families = {family for row in matrix["families"] for family in row["source_branches"]}
    static_families = set(cell_manifest["material_branch_counts"])
    if matrix_families != static_families:
        raise RuntimeError(f"driver matrix branch coverage failed: matrix_only={sorted(matrix_families-static_families)} static_only={sorted(static_families-matrix_families)}")
    family_status = {row["family"]: row["status"] for row in matrix["families"]}
    assigned_rule_families = set(cell_manifest["rule_family_counts"])
    authorized = sorted(f for f in assigned_rule_families if family_status.get(f) == "AUTHORIZED_FORWARD")
    unresolved = sorted(f for f in assigned_rule_families if family_status.get(f) in {"UNKNOWN_PROPAGATION_ONLY", "INSUFFICIENT_AUTHORITY"})
    validation = {"stage": "R5.17-B7-A3F2-P7Q-HRAB", "repository": audit, "pre5n_validated": True, "static_endpoint": {"records": 249840, "sha256": STATIC_SHA256, "backcast_initializer": False, "endpoint_constraint_only": True}, "clock": clock_manifest, "cell_rule_index": cell_manifest, "hard_anchor_count": 12, "interval_count": 11, "all_hard_anchors_represented": True, "all_static_material_branches_covered": cell_manifest["all_static_material_branches_covered"], "unmapped_static_material_branches": cell_manifest["unmapped_static_material_branches"], "no_backward_endpoint_inversion": True, "no_generic_categorical_interpolation": True, "fake_spatial_resolution_used": False, "native_resolution_preserved": True, "unknown_preserved": True, "saprolite_authority_created": False, "physical_soil_created": False, "P7Q_reopened": False, "scientific_authority_register_mutated": False, "execution_indexes_mutated": False, "forward_evolution": {"executed": False, "reason": "PRE3/PRE4 production rules remain schema-only or missing required drivers", "authorized_forward_rule_families": authorized, "unresolved_rule_families": unresolved}, "anchorbridge_core_ready": True, "full_temporal_parent_state_materialized": False, "interval_checkpoints": interval_records}
    dump(ROOT / "R5_17_B7_A3F2_P7Q_HRAB_TEMPORAL_CLOCK_MANIFEST.json", clock_manifest)
    dump(ROOT / "R5_17_B7_A3F2_P7Q_HRAB_CELL_RULE_INDEX_MANIFEST.json", cell_manifest)
    dump(ROOT / "R5_17_B7_A3F2_P7Q_HRAB_VALIDATION.json", validation)
    adjudication = {"stage": validation["stage"], "decision": "ANCHORBRIDGE_CORE_READY__FULL_TEMPORAL_PARENT_STATE_PENDING_DRIVER_AUTHORITY", "verdict": "PASS_P7Q_HRAB_CORE_ARCHITECTURE_WITH_EXPLICIT_UNKNOWN_MASK", "anchorbridge_core_ready": True, "full_temporal_parent_state_materialized": False, "next_action": "RECOVER_OR_ADJUDICATE_MISSING_TEMPORAL_PARENT_MATERIAL_DRIVERS_BEFORE_ANY_FULL_EVOLUTION", "governance": {"P7Q_reopened": False, "physical_soil_created": False, "scientific_authority_register_mutated": False, "canonical_mutation": False}}
    dump(ROOT / "R5_17_B7_A3F2_P7Q_HRAB_ADJUDICATION.json", adjudication)
    (ROOT / "R5_17_B7_A3F2_P7Q_HRAB_ADJUDICATION.md").write_text("# R5.17-B7-A3F2-P7Q-HRAB\n\nCore AnchorBridge ready. The 280-point R3.28 clock and 11 sparse interval checkpoints are materialized without categorical interpolation or spatial upsampling. Full temporal parent-material state remains pending missing/blocked driver authorities; UNKNOWN is preserved.\n\n- 0 ka endpoint: constraint/check only\n- 200 ka initializer: not inferred from 0 ka\n- forward state evolution: not executed because PRE3/PRE4 production rules are not authorized\n- physical soil: not created\n- P7Q reopened: false\n", encoding="utf-8")
    if not args.no_state_update:
        update_state_idempotently()
    print(json.dumps({"decision": adjudication["decision"], "verdict": adjudication["verdict"], "cell_rule_index": cell_manifest, "clock_points": len(clock), "intervals": 11}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
