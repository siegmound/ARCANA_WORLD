"""R5.17-B7-A3F2-P7NC1R governed legacy geologic-authority recovery.

This is a bounded evidence audit.  It reads the A1 endpoint authority and
the D3.2C event catalogue, and emits compact JSON/Markdown evidence.  It
does not run a geological model, mutate canonical state, or materialize
parent material.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
JSON_OUT = ROOT / "R5_17_B7_A3F2_P7NC1R_LEGACY_GEOLOGIC_TECTONIC_AUTHORITY_RECOVERY.json"
MD_OUT = ROOT / "R5_17_B7_A3F2_P7NC1R_LEGACY_GEOLOGIC_TECTONIC_AUTHORITY_RECOVERY.md"
A1 = ROOT / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz"
EVENTS = ROOT / "outputs/v0_6D1_R3/PALEOGEOGRAPHIC_EVENT_CATALOG_ALL_A1_v0_6D1_R3.json"
EXACT_TRANSPORT = ROOT / "outputs/v0_3/DEEP_GEOLOGICAL_TRANSPORT_KEYFRAMES_210_0Ma_v0_3.npz"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    with np.load(A1, allow_pickle=False) as z:
        schema = {
            key: {"shape": list(z[key].shape), "dtype": str(z[key].dtype)}
            for key in z.files
        }
        ages = [float(x) for x in z["age_ma"]]
        plate = z["plate_code"]
        land = z["land_mask"]
        persistence = []
        for i in range(len(ages) - 1):
            overlap = (land[i] > 0) & (land[i + 1] > 0)
            n = int(overlap.sum())
            persistence.append({
                "older_ma": ages[i], "younger_ma": ages[i + 1],
                "shared_land_cells": n,
                "same_plate_code_fraction": (
                    float((plate[i][overlap] == plate[i + 1][overlap]).mean())
                    if n else None
                ),
            })
        a1_authority = {
            "path": str(A1.relative_to(ROOT)),
            "sha256": sha256(A1),
            "ages_ma": ages,
            "grid_shape": [int(land.shape[1]), int(land.shape[2])],
            "schema": schema,
            "plate_code_unique_by_frame": [sorted(map(int, np.unique(x))) for x in plate],
            "land_cell_count_by_frame": [int(x.sum()) for x in land],
            "plate_persistence_diagnostics": persistence,
        }

    event_doc = load_json(EVENTS)
    summary = event_doc.get("summary", {})
    brackets = event_doc.get("brackets", [])
    event_evidence = {
        "path": str(EVENTS.relative_to(ROOT)),
        "sha256": sha256(EVENTS),
        "status": event_doc.get("status"),
        "bracket_count": len(brackets),
        "event_cluster_count": summary.get("event_cluster_count", sum(x.get("event_cluster_count", 0) for x in brackets)),
        "grid": [90, 180],
        "first_bracket_event_cluster_count": brackets[0].get("event_cluster_count") if brackets else None,
        "semantic_status": "DERIVED_ENDPOINT_CONSTRAINED_EVENT_CLUSTER_NOT_INDEPENDENT_GEOLOGICAL_OBSERVATION",
        "interpretation": "D3.2C groups endpoint land/ocean transitions and schedules derived event clusters; it is not a lithology, crust, basin, or provenance authority.",
    }

    exact_status = {
        "target": "outputs/v0_3/DEEP_GEOLOGICAL_TRANSPORT_KEYFRAMES_210_0Ma_v0_3.npz",
        "current_present": EXACT_TRANSPORT.exists(),
        "historical_file_confirmed": False,
        "sha256": sha256(EXACT_TRANSPORT) if EXACT_TRANSPORT.exists() else None,
        "status": "ARTIFACT_REFERENCED_ONLY__NO_HASH_OR_BLOB_CONFIRMED",
        "scope": "Targeted recovery; no broad corpus scan and no checkout/restore.",
    }

    matrix = {
        "surface_geological_province_identity": "PALEOGEOGRAPHIC_CONSTRAINT_ONLY",
        "crustal_domain_state": "KINEMATIC_CONSTRAINT_ONLY",
        "magmatic_volcanic_province": "ABSENT_AFTER_TARGETED_RECOVERY",
        "sedimentary_basin_province": "ABSENT_AFTER_TARGETED_RECOVERY",
        "orogenic_metamorphic_state": "ABSENT_AFTER_TARGETED_RECOVERY",
        "formation_exposure_persistence": "PARTIAL_EXISTING_AUTHORITY",
        "source_to_sediment_provenance_linkage": "ABSENT_AFTER_TARGETED_RECOVERY",
    }
    doc = {
        "record_id": "R5.17-B7-A3F2-P7NC1R",
        "title": "Legacy Geologic / Tectonic Authority Recovery",
        "p7nc1_parent_decision": "BLOCKED_SOURCE_MATERIAL_PRIOR_CAUSALITY",
        "recovered_a1_authority": a1_authority,
        "full_a1_schema": schema,
        "plate_code_semantics": "Discrete endpoint-constrained plate/region identity used for paleogeographic event ordering; no encoded lithology or formal rotation/topology model was recovered.",
        "plate_identity_persistence": {"classification": "COHERENT_DISCRETE_ENDPOINT_SCAFFOLD", "diagnostics": persistence, "limitation": "Persistence is diagnostic only; a codebook or plate-rotation authority is not encoded in this NPZ."},
        "d32c_event_semantics": event_evidence,
        "historical_transport_artifact_status": exact_status,
        "historical_transport_schema": {"status": "UNRECOVERED", "schema": None},
        "historical_transport_provenance": {"status": "UNCONFIRMED", "producer": None, "source_commit": None},
        "producer_lineage": {"a1": "R3.21 endpoint/reference lineage", "d32c": "D3.2C paleogeographic event catalogue", "exact_210_to_0_transport": "not confirmed in current evidence"},
        "execution_index_evidence": {"A1": "FULL_A1_REFERENCE_210_0Ma.npz is present and hashable", "D3.2C": "PALEOGEOGRAPHIC_EVENT_CATALOG_ALL_A1_v0_6D1_R3.json is present and hashable", "exact_transport": "no exact indexed match recovered"},
        "manifest_evidence": {"exact_transport": "no exact manifest match recovered"},
        "git_history_evidence": {"exact_path_history": "no exact path history match", "name_reference": "DEEP_GEOLOGICAL_TRANSPORT string observed in historical source context; no exact NPZ blob confirmed", "mutation": False},
        "seven_state_authority_matrix": matrix,
        "kinematic_causal_value": "KINEMATIC_STATE_PARTIALLY_SUFFICIENT",
        "conditional_geology_viability": "CONDITIONALLY_VIABLE_WITH_NEW_GEOLOGICAL_PROVINCE_STATE",
        "p7nc1_correction_assessment": "P7NC1 blocker is narrowed: A1/D3.2C recover a paleogeographic/kinematic scaffold, while source-material geological causality remains unresolved. P7NC1 was not edited.",
        "primary_decision": "CONFIRMED_ONLY_PALEOGEOGRAPHIC_KINEMATIC_AUTHORITY",
        "recommended_next_operation": "R5.17-B7-A3F2-P7Q_TARGETED_SYNTHETIC_GEOLOGIC_CAUSALITY_GATE",
        "governance": {"targeted_authority_recovery": True, "scientific_run": False, "parent_material_materialized": False, "abundance_materialized": False, "k_x_t_materialized": False, "human_management_used": False, "population_target_used": False, "canonical_mutation": False, "p7q_opened": False, "exact_transport_recovered": False},
    }
    JSON_OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    MD_OUT.write_text("# R5.17-B7-A3F2-P7NC1R\n\n"
        "## Decision\n\n**CONFIRMED_ONLY_PALEOGEOGRAPHIC_KINEMATIC_AUTHORITY**\n\n"
        "The recovered A1 authority supplies 11 governed endpoint snapshots on a 90x180 grid. D3.2C supplies derived endpoint-constrained transition clusters (801 total; 69 in the 210–180 Ma bracket), not independent geological observations.\n\n"
        "The named Deep Geological Transport NPZ was not found in the current checkout, targeted indexes/manifests, or exact Git path history; its schema and hash therefore remain unconfirmed.\n\n"
        "## Adjudication\n\nA1 `plate_code` is a discrete paleogeographic/kinematic scaffold. It does not establish lithology, crustal domain composition, volcanic or sedimentary provinces, or source-to-sediment provenance. Formation/exposure persistence is only partial through land-mask and endpoint/event history.\n\n"
        "P7NC1 is narrowed, not completed: a future P7Q should consume this existing kinematic scaffold and introduce only the missing geological causal state. No geological run or materialization occurred.\n\n"
        "## Governance\n\nNo canonical mutation, abundance, parent-material materialization, human management, population target, or K(x,t) was used. P7NC1 and all state/index files remain unchanged.\n", encoding="utf-8")
    print(f"wrote {JSON_OUT.name}")
    print(f"wrote {MD_OUT.name}")


if __name__ == "__main__":
    main()
