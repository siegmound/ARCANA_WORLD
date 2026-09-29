#!/usr/bin/env python3
"""Materialize replayable heat-flow state and numerical FEG support; never run OrbData."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from arcana_worldsim.r6.repository_context import (
    canonical_text_sha256, resolve_external_payload_path,
)
from arcana_worldsim.r6.shellset_mesh.adapter import load_canonical_mesh
from arcana_worldsim.r6.pre_orbdata_heat_flow import produce_heat_flow
from arcana_worldsim.r6.pre_orbdata_projection import (
    merge_projection_with_cell_state, project_heat_flow_to_feg,
)

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz"
OUTPUT = ROOT / "R6_PRE_ORBDATA_HEAT_FLOW_FEG_PROJECTION_V1.json"
TEXT_HASH_POLICY = "CANONICAL_UTF8_TEXT_LF_SHA256"
COMPACT_ARRAY_KEYS = {
    "heat_flow_w_m2", "cell_heat_flow_w_m2", "cell_source_branch_code",
    "cell_applicability_mask", "cell_owner_source_fields",
}


def write_projection_artifact(path: Path, payload: dict) -> None:
    """Write stable JSON while keeping the 64k per-node records one per line."""
    lines = ["{"]
    items = sorted(payload.items())
    for index, (key, value) in enumerate(items):
        comma = "," if index + 1 < len(items) else ""
        key_text = json.dumps(key, ensure_ascii=False)
        if key == "lineage":
            lines.append(f"  {key_text}: [")
            for row_index, row in enumerate(value):
                row_comma = "," if row_index + 1 < len(value) else ""
                lines.append("    " + json.dumps(row, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False) + row_comma)
            lines.append("  ]" + comma)
        elif key in COMPACT_ARRAY_KEYS:
            lines.append("  " + key_text + ": " + json.dumps(
                value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                allow_nan=False) + comma)
        else:
            encoded = json.dumps(value, sort_keys=True, indent=2,
                                 ensure_ascii=False, allow_nan=False).splitlines()
            if len(encoded) == 1:
                lines.append("  " + key_text + ": " + encoded[0] + comma)
            else:
                lines.append("  " + key_text + ": " + encoded[0])
                lines.extend("  " + line for line in encoded[1:-1])
                lines.append("  " + encoded[-1] + comma)
    lines.append("}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    lineage = {
        "field_package_sha256": hashlib.sha256(PACKAGE.read_bytes()).hexdigest(),
        "physical_geography_sha256": "a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c",
        "vector_partition_sha256": "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab",
        "kinematics_sha256": "50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4",
        "heat_flow_config_sha256": canonical_text_sha256(ROOT / "R6_PRE_ORBDATA_HEAT_FLOW_CONFIG_V1.json"),
        "material_config_sha256": canonical_text_sha256(ROOT / "R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json"),
    }
    with np.load(PACKAGE, allow_pickle=False) as z:
        domain = z["physical_crust_domain_id"].copy()
        age = z["oceanic_lithosphere_age_ma"].copy()
        continental = z["continental_reference_surface_heat_flow_w_m2"].copy()
        owner_parent_fields = {
            "physical_crust_domain_id": z["physical_crust_domain_id"].copy(),
            "oceanic_lithosphere_age_ma": z["oceanic_lithosphere_age_ma"].copy(),
            "crustal_thickness_m": z["crustal_thickness_m"].copy(),
            "continental_reference_lithosphere_thickness_m": z["continental_reference_lithosphere_thickness_m"].copy(),
            "continental_thermal_domain_id": z["continental_thermal_domain_id"].copy(),
        }

    ridge_report = json.loads((ROOT / "R6_PRE_ORBDATA_HEAT_FLOW_RIDGE_AND_RUNTIME_CLOSURE.json").read_text(encoding="utf-8"))
    ridge = np.zeros(domain.shape, dtype=bool)
    for cell in ridge_report["t0_ocean_age_support_audit"]["age_zero_cell_locations"]:
        ridge[cell["row_south_to_north_zero_based"], cell["column_west_to_east_zero_based"]] = True
    if np.count_nonzero(ridge) != 108 or not np.array_equal(ridge, (domain == 1) & (age == 0)):
        raise ValueError("GOVERNED_RIDGE_MASK_DOES_NOT_MATCH_T0_SUPPORT")
    lineage["ridge_support_mask_sha256"] = hashlib.sha256(ridge.astype("uint8").tobytes(order="C")).hexdigest()
    lineage["ridge_source_authority_sha256"] = canonical_text_sha256(ROOT / "R6_PRE_ORBDATA_HEAT_FLOW_RIDGE_AND_RUNTIME_CLOSURE.json")
    lineage["feg_mesh_sha256"] = "6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad"
    source_files = (
        "src/arcana_worldsim/r6/pre_orbdata_heat_flow.py",
        "src/arcana_worldsim/r6/pre_orbdata_thermal_column.py",
        "src/arcana_worldsim/r6/pre_orbdata_projection.py",
        "scripts/r6_pre_orbdata_materialize_heat_flow_projection.py",
    )
    for rel in source_files:
        lineage[rel.replace("/", "_") + "_sha256"] = canonical_text_sha256(ROOT / rel)

    q, branch, valid = produce_heat_flow(
        physical_domain=domain, age_ma=age, continental_q_w_m2=continental,
        ridge_support=ridge, parent_lineage=lineage)
    branch_name = np.select(
        (branch == 1, branch == 2, branch == 3),
        ("CONTINENTAL_AUTHORED_REFERENCE", "GOVERNED_RIDGE_BOUNDARY",
         "AUTHORIZED_POSITIVE_AGE_OCEAN"), default="UNKNOWN")
    owner_fields = {
        "cell_heat_flow_w_m2": q,
        "physical_crust_domain_id": domain,
        "cell_source_branch_code": branch,
        "runtime_branch": branch_name,
        "oceanic_lithosphere_age_ma": age,
        "material_configuration_identity": np.full(domain.shape,
            "R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1", dtype="U48"),
        "material_configuration_binding": np.asarray([
            "OCEANIC_CRUST_REFERENCE" if int(code) == 1 else "CONTINENTAL_CRUST_REFERENCE"
            for code in domain.flat], dtype="U48").reshape(domain.shape),
        **owner_parent_fields,
    }
    cell_counts = {
        "CONTINENT": int(np.count_nonzero(branch == 1)),
        "RIDGE": int(np.count_nonzero(branch == 2)),
        "POSITIVE_AGE_OCEAN": int(np.count_nonzero(branch == 3)),
    }
    cell_state = {
        "schema": "R6_PRE_ORBDATA_HEAT_FLOW_DERIVED_CELL_STATE_V1",
        "decision": "DERIVED_REPLAYABLE_T0_STATE__FEG_PROJECTION_PENDING",
        "cell_shape": list(q.shape), "cell_count": int(q.size),
        "cell_heat_flow_w_m2": q.tolist(),
        "cell_source_branch_code": branch.tolist(),
        "cell_applicability_mask": valid.tolist(),
        "cell_branch_metadata": {
            "1": {"branch": "CONTINENTAL_AUTHORED_REFERENCE", "model_identity": None},
            "2": {"branch": "GOVERNED_RIDGE_BOUNDARY", "model_identity": None},
            "3": {"branch": "AUTHORIZED_POSITIVE_AGE_OCEAN", "model_identity": "HWR2_FINITE_PLATE_CONSTANT_PROPERTY_SURFACE_FLUX"},
        },
        "source_lineage": dict(sorted(lineage.items())),
        "text_hash_policy": TEXT_HASH_POLICY,
        "cell_heat_flow_sha256": hashlib.sha256(np.asarray(q, dtype="<f8").tobytes()).hexdigest(),
        "cell_branch_counts": cell_counts,
        "cell_unknown_count": int(np.count_nonzero(~valid)),
        "authority": "DERIVED_REPLAYABLE_T0_STATE",
        "projection_authority": "NUMERICAL_DERIVED_SUPPORT",
        "serialized_orbdata_authority": "NUMERICAL_RUNTIME_INPUT_ONLY",
        "physical_resolution_promotion": False, "smoothing": "NONE",
    }

    parent = json.loads((ROOT / "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json").read_text(encoding="utf-8"))
    try:
        payload = resolve_external_payload_path(ROOT, parent["payload"]["path"])
        with np.load(payload, allow_pickle=False) as z:
            rows = z["face_row"].copy()
            cols = z["face_col"].copy()
        mesh = load_canonical_mesh(ROOT)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        blocked = dict(cell_state)
        blocked.update({
            "projection_status": "BLOCKED_MISSING_OR_INVALID_PINNED_FEG_PARENT_PAYLOAD",
            "projection_diagnostic": str(exc), "node_count_target": 64_442,
        })
        blocked["replay_sha256"] = hashlib.sha256(json.dumps(
            blocked, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        OUTPUT.write_text(json.dumps(blocked, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
        print(f"cell_state_materialized; FEG projection blocked: {exc}")
        return 2

    projection = project_heat_flow_to_feg(
        mesh, rows, cols, q, domain, source_lineage=lineage,
        cell_validity=valid, owner_cell_fields=owner_fields)
    runtime_owner_contract = {
        "owner_key": "lineage[].numerical_owner_cell_row_col",
        "same_owner_required_for": ["heat_flow", "runtime_domain_and_branch", "thermal_profile_state",
            "lithosphere_geometry", "material_configuration_binding"],
        "owner_fields": list(owner_fields),
        "material_configuration_identity": "R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1",
        "thermal_profile_state_binding": "DERIVE_FROM_THE_SAME_OWNER_CELL_AND_VERSIONED_MATERIAL_CONFIGURATION",
        "owner_domain_semantics": "NUMERICAL_OWNER_ONLY; NOT_CANONICAL_NODE_DOMAIN",
        "owner_value_source": "cell fields indexed by the shared numerical_owner_cell_row_col",
        "thermal_profile_state_binding": "derive from owner cell's branch, heat flow, age, geometry, and this versioned material configuration",
        "mixed_support_policy": "preserve all incident physical domain IDs; downstream values bind to the single numerical owner",
        "shellset_must_consume_owner_or_prove_identical_ownership": True,
        "latitude_longitude_reclassification_in_shellset": False,
    }
    artifact_metadata = {
        "decision": "R6_PRE_ORBDATA_FEG_NUMERICAL_SUPPORT_COMPLETE__SHELLSET_SUCCESSOR_PATCH_READY",
        "projection_status": "AUTHORITATIVE_CANONICAL_FEG_MATERIALIZATION_COMPLETE",
        "projection_authority": "NUMERICAL_DERIVED_SUPPORT",
        "serialized_orbdata_authority": "NUMERICAL_RUNTIME_INPUT_ONLY",
        "field_shape": list(q.shape), "cell_count": int(q.size),
        "cell_heat_flow_w_m2": q.tolist(),
        "cell_source_branch_code": branch.tolist(),
        "cell_validity_mask": valid.tolist(),
        "cell_branch_counts": cell_counts,
        "cell_unknown_count": int(np.count_nonzero(~valid)),
        "cell_heat_flow_sha256": cell_state["cell_heat_flow_sha256"],
        "cell_owner_source_fields": {
            name: [[(float(value) if np.isfinite(value) else None) for value in row]
                   for row in array] if np.issubdtype(array.dtype, np.floating)
                  else array.tolist()
            for name, array in owner_parent_fields.items()
        },
        "mesh_sha256": mesh.normalized_sha256,
        "material_configuration_identity": "R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1",
        "cell_branch_metadata": cell_state["cell_branch_metadata"],
        "physical_resolution_promotion": False, "smoothing": "NONE",
        "runtime_owner_contract": runtime_owner_contract,
    }
    result = merge_projection_with_cell_state(projection, artifact_metadata)
    result["source_lineage"] = dict(sorted(lineage.items()))
    result["text_hash_policy"] = TEXT_HASH_POLICY
    result["node_known_count"] = sum(v is not None for v in projection.node_heat_flow_w_m2)
    result["node_unknown_count"] = sum(v is None for v in projection.node_heat_flow_w_m2)
    mixed_count = sum(row["mixed_physical_support"] for row in projection.lineage)
    result["mixed_physical_support_node_count"] = mixed_count
    result["deterministic_numerical_owner_count"] = sum(
        row["numerical_owner_cell_row_col"] is not None for row in projection.lineage)
    result.pop("replay_sha256", None)
    result["replay_sha256"] = hashlib.sha256(json.dumps(
        result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    write_projection_artifact(OUTPUT, result)
    print(f"projection_nodes={result['node_count']} known={result['node_known_count']} "
          f"unknown={result['node_unknown_count']} mixed={mixed_count} "
          f"owners={result['deterministic_numerical_owner_count']} replay_sha256={result['replay_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
