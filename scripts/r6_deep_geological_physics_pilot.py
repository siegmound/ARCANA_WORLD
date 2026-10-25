from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter
import tracemalloc
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.deep_geological_physics_pilot import (  # noqa: E402
    DeepCell, PilotConfig, ReducedStateNodeMapping, RoleModalParameters,
    map_reduced_state_material_nodes, run_canon_guided_pilot,
)
from arcana_worldsim.r6.tectonic_deep_pilot import load_archived_state_jsonl  # noqa: E402

DEFAULT_ARCHIVE = Path(r"F:\corsiiiuu\Magistrale\Arcana\ENG10K_LUNA_ANALYSIS\ENG10K_ARCHIVE_ec79bf89_01.tar.gz")
DEFAULT_OUTPUT = ROOT / "outputs/r6_experimental_multiphysics/MATERIAL_DEEP_INTEGRATION_20261025_02/RESULT.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Short canon-guided, explicitly synthetic Deep geology pilot")
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--steps", type=int, default=3)
    args = parser.parse_args()
    target = args.output.resolve()
    if "WORLD_HISTORY" in str(target).upper():
        parser.error("canonical WORLD_HISTORY paths are prohibited")
    if target.exists():
        parser.error(f"output already exists; refusing overwrite: {target}")
    if args.steps < 1 or args.steps > 10:
        parser.error("pilot steps must be between 1 and 10")

    state, provenance = load_archived_state_jsonl(str(args.archive))
    archive_sha = hashlib.sha256(args.archive.read_bytes()).hexdigest()
    canon_zip = Path(r"C:\Users\jose_\Downloads\ARCANA_UNIVERSE_CANON_v0_3_73_MC_FAMILY_H3_CHARACTER_AUTHORIAL_RATIFICATION_RATIFIED(1).zip")
    canon_members = (
        "CANON/12_DEEP_ENERGY_GEOGRAPHY_EXTRACTION_AND_TRANSPORT.md",
        "CANON/13_LEVEL1_PHYSICS_CANDIDATE.md",
        "CANON/17_LEVEL1_THERMAL_PHYSICS.md",
        "CANON/21_LEVEL1_CONDENSED_MATTER_CRYSTALS_AND_ACCUMULATORS.md",
        "CANON/25_LEVEL1_CROSS_DOMAIN_INTEGRATION.md",
    )
    canon_hashes = {}
    with zipfile.ZipFile(canon_zip) as archive:
        for suffix in canon_members:
            member = next(name for name in archive.namelist() if name.endswith(suffix))
            canon_hashes[suffix] = hashlib.sha256(archive.read(member)).hexdigest()
    indices = (23, 25)
    role_parameters = (
        RoleModalParameters("CONTINENTAL_CRUST_REFERENCE", 0.6, 0.3, 0.05),
        RoleModalParameters("LITHOSPHERIC_MANTLE_REFERENCE", 0.8, 0.2, 0.08),
    )
    mapping_identity = ReducedStateNodeMapping(
        support_id=str(provenance["support_id"]), trajectory_id=str(provenance["trajectory_id"]),
        sequence=int(provenance["sequence"]), state_payload_sha256=str(provenance["state_payload_sha256"]),
        mapping_id="C029_MOHO_BRACKET_NODES_023_025_MATERIAL_INTERFACE_SAMPLE_V1",
        node_indices=indices, strike_length_m=1.0,
    )
    mapped = map_reduced_state_material_nodes(state, identity=mapping_identity,
                                              modal_parameters_by_role=role_parameters)
    geology = mapped.geology
    cells = mapped.deep_cells(inventory_j=(100.0, 20.0), zeta=(0.4, 0.7), a_x=(0.5, 0.8))

    configs = {
        "baseline": PilotConfig(duration_years=float(args.steps), mobility_per_year=0.08),
        "low_mobility": PilotConfig(duration_years=float(args.steps), mobility_per_year=0.01),
        "high_mobility": PilotConfig(duration_years=float(args.steps), mobility_per_year=0.20),
        "modal_role_contrast": PilotConfig(duration_years=float(args.steps), mobility_per_year=0.08),
        "structural_accessibility_perturbation": PilotConfig(duration_years=float(args.steps), mobility_per_year=0.08),
    }
    cases = {}
    tracemalloc.start()
    started = perf_counter()
    for name, config in configs.items():
        case_geo = tuple(geology)
        case_cells = tuple(cells)
        modal_config = role_parameters
        perturbation = (0.0, 0.0)
        if name == "modal_role_contrast":
            modal_config = (RoleModalParameters("CONTINENTAL_CRUST_REFERENCE", 0.2, 1.0, 0.15),
                            RoleModalParameters("LITHOSPHERIC_MANTLE_REFERENCE", 0.9, 0.1, 0.02))
            remapped = map_reduced_state_material_nodes(state, identity=mapping_identity,
                                                        modal_parameters_by_role=modal_config)
            case_geo = remapped.geology
            case_cells = remapped.deep_cells(inventory_j=(100.0, 20.0), zeta=(0.4, 0.7), a_x=(0.5, 0.8))
        if name == "structural_accessibility_perturbation":
            perturbation = (0.0, 0.15)
        cases[name] = run_canon_guided_pilot(
            state, geology=case_geo, deep_cells=case_cells, config=config,
            material_mapping=mapping_identity, modal_parameters_by_role=modal_config,
            structure_accessibility_perturbation=perturbation,
        )
    elapsed = perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    base_energy = cases["baseline"]["energy_ledgers"]["final_inventory_j_by_cell"]
    for name, result in cases.items():
        result["input_provenance"] = provenance
        result["component_source_sha256"] = {
            "thermal_kernel": hashlib.sha256((ROOT / "src/arcana_worldsim/r6/functional_development.py").read_bytes()).hexdigest(),
            "pilot_module": hashlib.sha256((ROOT / "src/arcana_worldsim/r6/deep_geological_physics_pilot.py").read_bytes()).hexdigest(),
        }
    document = {
        "schema": "ARCANA_CANON_GUIDED_DEEP_PILOT_EXPERIMENTS_V1",
        "scope": "SHORT_NONCANONICAL_ENGINEERING_SENSITIVITY_NOT_PHYSICAL_QUALIFICATION",
        "cases": cases,
        "comparison": {
            "baseline_final_inventory_j": base_energy,
            "modal_role_contrast_final_inventory_j": cases["modal_role_contrast"]["energy_ledgers"]["final_inventory_j_by_cell"],
            "low_mobility_final_inventory_j": cases["low_mobility"]["energy_ledgers"]["final_inventory_j_by_cell"],
            "high_mobility_final_inventory_j": cases["high_mobility"]["energy_ledgers"]["final_inventory_j_by_cell"],
            "structural_perturbation_final_inventory_j": cases["structural_accessibility_perturbation"]["energy_ledgers"]["final_inventory_j_by_cell"],
            "structural_perturbation_changes_stock": (cases["baseline"]["energy_ledgers"]["final_inventory_j_by_cell"] != cases["structural_accessibility_perturbation"]["energy_ledgers"]["final_inventory_j_by_cell"]),
        },
        "provenance": {
            "canon_zip_path": str(canon_zip),
            "canon_zip_sha256": hashlib.sha256(canon_zip.read_bytes()).hexdigest(),
            "canon_chapter_member_sha256": canon_hashes,
            "archive_path": str(args.archive),
            "archive_sha256": archive_sha,
            "identity_authority": "LOCAL_BYTE_HASHES; CANON CONTENT SUMMARIZED, NOT EMBEDDED",
        },
        "measurements": {"case_count": len(cases), "steps_per_case": args.steps,
                         "elapsed_seconds": elapsed, "python_tracemalloc_peak_bytes": peak,
                         "output_bytes": None},
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(4):
        encoded = (json.dumps(document, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
        actual = len(encoded)
        if document["measurements"]["output_bytes"] == actual:
            break
        document["measurements"]["output_bytes"] = actual
    with target.open("xb") as f:
        f.write(encoded); f.flush()
    print(json.dumps({"result_path": str(target), "result_bytes": target.stat().st_size,
                      "result_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                      "elapsed_seconds": elapsed, "tracemalloc_peak_bytes": peak,
                      "baseline_final_inventory_j": base_energy}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
