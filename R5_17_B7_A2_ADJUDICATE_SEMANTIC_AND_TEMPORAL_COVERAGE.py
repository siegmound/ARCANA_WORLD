from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import numpy as np


STATUS = "PASS_R517_B7_A2_SEMANTIC_BINDING_AND_TEMPORAL_COVERAGE_ADJUDICATED"
DECISION = "AUTHORIZE_B7_A3_NATURAL_RESOURCE_COMPONENT_MATERIALIZATION_WITH_EXPLICIT_AQUATIC_MARINE_GAP"

EXPECTED_A1_STATUS = (
    "PASS_R517_B7_A1_NATURAL_FOOD_SUPPORT_AUTHORITY_SCHEMA_COVERAGE_PREFLIGHT"
)
EXPECTED_A1_DECISION = (
    "AUTHORIZE_B7_A2_SEMANTIC_BINDING_AND_TEMPORAL_COVERAGE_ADJUDICATION"
)

A1_PATH = Path("R5_17_B7_A1_NATURAL_FOOD_SUPPORT_AUTHORITY_PREFLIGHT.json")
CURRENT_STATE_PATH = Path("ARCANA_WORLD_CURRENT_STATE.md")
B7_CONTRACT_PATH = Path("R5_17_B7_BIOLOGICAL_FOOD_SUPPORT_CONTRACT.md")

R333_SOURCE = Path(
    "src/arcana_worldsim/scientific_engines/"
    "r333_holocene_environment_domestication.py"
)
R334_SOURCE = Path(
    "src/arcana_worldsim/scientific_engines/"
    "r334_producer_domestication.py"
)

R333_ENV_CANDIDATES = (
    Path(
        "SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/"
        "v0_6D1_R3_33/R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz"
    ),
    Path(
        "outputs/v0_6D1_R3_33/"
        "R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz"
    ),
)

R334_LANDSCAPE_CANDIDATES = (
    Path(
        "SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/"
        "v0_6D1_R3_34/R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz"
    ),
    Path(
        "outputs/v0_6D1_R3_34/"
        "R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz"
    ),
)

R321_LINEAGE_CANDIDATES = (
    Path(
        "SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/"
        "v0_6D1_R3_21/R3_21_PRESENT_LINEAGE_REGISTRY.json"
    ),
    Path("outputs/v0_6D1_R3_21/R3_21_PRESENT_LINEAGE_REGISTRY.json"),
)

R321_COMPONENT_CANDIDATES = (
    Path(
        "SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/"
        "v0_6D1_R3_21/R3_21_PRESENT_COMPONENT_REGISTRY.json"
    ),
    Path("outputs/v0_6D1_R3_21/R3_21_PRESENT_COMPONENT_REGISTRY.json"),
)

R321_HISTORICAL_CLOSURE_CANDIDATES = (
    Path(
        "SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/"
        "v0_6D1_R3_21/R3_21_HISTORICAL_LINEAGE_CLOSURE.json"
    ),
    Path("outputs/v0_6D1_R3_21/R3_21_HISTORICAL_LINEAGE_CLOSURE.json"),
)

R323_SUMMARY_CANDIDATES = (
    Path(
        "SIMULATION_RESULTS/91_SUPPORT_SCIENTIFIC_REPLAY/outputs/"
        "v0_6D1_R3_23/R3_23_PRESENT_FUNCTIONAL_SUMMARY.json"
    ),
    Path("outputs/v0_6D1_R3_23/R3_23_PRESENT_FUNCTIONAL_SUMMARY.json"),
)

OUT_JSON = Path(
    "R5_17_B7_A2_SEMANTIC_BINDING_AND_TEMPORAL_COVERAGE_ADJUDICATION.json"
)
OUT_MD = Path(
    "R5_17_B7_A2_SEMANTIC_BINDING_AND_TEMPORAL_COVERAGE_ADJUDICATION.md"
)


class GateError(RuntimeError):
    pass


def run_git(root: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return cp.stdout.strip()


def repo_root() -> Path:
    cp = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return Path(cp.stdout.strip()).resolve()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def first_existing(root: Path, candidates: tuple[Path, ...]) -> Path:
    for rel in candidates:
        p = root / rel
        if p.is_file():
            return p
    raise GateError(
        "None of the governed candidate paths exists:\n"
        + "\n".join(str(x) for x in candidates)
    )


def npz_summary(path: Path) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as z:
        arrays: dict[str, Any] = {}
        for key in z.files:
            a = np.asarray(z[key])
            row: dict[str, Any] = {
                "shape": list(a.shape),
                "dtype": str(a.dtype),
                "size": int(a.size),
            }
            if a.dtype.kind in "biufc" and a.size:
                af = np.asarray(a, dtype=float)
                finite = np.isfinite(af)
                row["finite"] = bool(finite.all())
                if finite.any():
                    vals = af[finite]
                    row["min"] = float(vals.min())
                    row["max"] = float(vals.max())
            arrays[key] = row
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "arrays": arrays,
    }


def extract_float_array(source: str, name: str) -> list[float]:
    pattern = rf"{re.escape(name)}\s*=\s*np\.array\(\[([^\]]+)\]"
    m = re.search(pattern, source)
    if not m:
        raise GateError(f"Could not recover {name} from source.")
    vals = []
    for raw in m.group(1).split(","):
        raw = raw.strip()
        if raw:
            vals.append(float(raw))
    return vals


def extract_string_list(source: str, name: str) -> list[str]:
    pattern = rf"{re.escape(name)}\s*=\s*\[([^\]]+)\]"
    m = re.search(pattern, source, flags=re.S)
    if not m:
        raise GateError(f"Could not recover {name} from source.")
    return re.findall(r"'([^']+)'|\"([^\"]+)\"", m.group(1))


def flatten_string_pairs(pairs: list[tuple[str, str]]) -> list[str]:
    return [a or b for a, b in pairs]


def text_record(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def deep_get_numeric(obj: Any, key: str) -> int | float | None:
    if isinstance(obj, dict):
        if key in obj and isinstance(obj[key], (int, float)):
            return obj[key]
        for value in obj.values():
            found = deep_get_numeric(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = deep_get_numeric(value, key)
            if found is not None:
                return found
    return None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    root = repo_root()
    head = run_git(root, "rev-parse", "HEAD")

    current_path = root / CURRENT_STATE_PATH
    contract_path = root / B7_CONTRACT_PATH
    a1_path = root / A1_PATH
    r333_source_path = root / R333_SOURCE
    r334_source_path = root / R334_SOURCE

    for p in (
        current_path,
        contract_path,
        a1_path,
        r333_source_path,
        r334_source_path,
    ):
        if not p.is_file():
            raise GateError(f"Missing required authority/source: {p}")

    current = current_path.read_text(encoding="utf-8-sig")
    contract = contract_path.read_text(encoding="utf-8-sig")
    a1 = load_json(a1_path)

    if a1.get("status") != EXPECTED_A1_STATUS:
        raise GateError("B7-A1 status mismatch.")
    if a1.get("decision") != EXPECTED_A1_DECISION:
        raise GateError("B7-A1 decision mismatch.")

    if "ACTIVE_SUBPHASE: R5.17-B7" not in current:
        raise GateError("Current-state marker missing: ACTIVE_SUBPHASE: R5.17-B7")
    if not any(
        marker in current
        for marker in (
            "ACTIVE_SUBPHASE_STATUS: A1_PREFLIGHT_COMPLETE__A2_READY",
            "ACTIVE_SUBPHASE_STATUS: A2_COMPLETE__A3_READY",
        )
    ):
        raise GateError("Current-state A2 readiness/completion marker missing.")
    if not any(
        marker in current
        for marker in (
            "NEXT_ACTION: RUN_B7_A2_SEMANTIC_BINDING_AND_TEMPORAL_COVERAGE_ADJUDICATION",
            "NEXT_ACTION: RUN_B7_A3_NATURAL_RESOURCE_COMPONENT_MATERIALIZATION",
        )
    ):
        raise GateError("Current-state A2/A3 next-action marker missing.")

    for marker in (
        "NATURAL BIOLOGICAL FOOD SUPPORT",
        "HUMAN FOOD PRODUCTION",
        "K(x,t)",
        "propagation_opportunity",
        "AQUATIC_MARINE_RESOURCE_SUPPORT",
    ):
        if marker not in contract:
            raise GateError(f"B7 contract marker missing: {marker}")

    # ------------------------------------------------------------------
    # A1 native forage: deep-time ecological/trophic substrate only.
    # ------------------------------------------------------------------

    a1_native = a1["a1_native_trophic_authority"]
    a1_payload = root / a1_native["path"]
    if not a1_payload.is_file():
        raise GateError(f"A1 forage payload missing: {a1_payload}")
    if sha256_file(a1_payload).lower() != str(a1_native["sha256"]).lower():
        raise GateError("A1 forage SHA256 mismatch.")

    a1_ages_ma = [float(x) for x in a1_native["age_ma_values"]]
    required_forage = {
        "browse_forage",
        "low_forage",
        "wetland_forage",
        "total_edible_forage",
    }
    a1_keys = set(a1_native["keys"])
    if not required_forage.issubset(a1_keys):
        raise GateError("A1 forage channels missing.")

    # ------------------------------------------------------------------
    # R3.33: exogenous environment is usable; domestication-oriented
    # animal candidate cohort is NOT an exhaustive wild-food inventory.
    # ------------------------------------------------------------------

    r333_source = r333_source_path.read_text(encoding="utf-8-sig")
    r333_ages_ka = extract_float_array(r333_source, "ANCHOR_AGES")

    r333_env_names_pairs = extract_string_list(r333_source, "ENV_NAMES")
    r333_env_names = flatten_string_pairs(r333_env_names_pairs)

    for required in (
        "temperature_anomaly_c",
        "precipitation_factor",
        "npp_factor",
        "land_fraction",
        "hydroclimate_resource_index",
        "coastal_edge_index",
    ):
        if required not in r333_env_names:
            raise GateError(f"R3.33 environment field missing in source: {required}")

    for forbidden_semantic in (
        "contact_opportunity",
        "management_intensity",
        "reproductive_control",
        "animal_food_production_contribution",
        "domestication_index",
    ):
        if forbidden_semantic not in r333_source:
            raise GateError(
                f"Expected R3.33 human-conditioned field not found: {forbidden_semantic}"
            )

    if "PARTNER_QUOTAS" not in r333_source or "build_partner_registry" not in r333_source:
        raise GateError("R3.33 candidate-screening semantics not recoverable.")

    r333_env_path = first_existing(root, R333_ENV_CANDIDATES)
    r333_env_npz = npz_summary(r333_env_path)

    # ------------------------------------------------------------------
    # R3.34: adjudicate which producer-landscape fields are natural /
    # pre-management and which are management affordances.
    # ------------------------------------------------------------------

    r334_source = r334_source_path.read_text(encoding="utf-8-sig")
    r334_ages_ka = extract_float_array(r334_source, "ANCHOR_AGES")
    landscape_pairs = extract_string_list(r334_source, "LANDSCAPE_NAMES")
    landscape_names = flatten_string_pairs(landscape_pairs)

    expected_landscape = [
        "suitability",
        "resource_abundance",
        "harvest_return",
        "propagation_opportunity",
    ]
    if landscape_names != expected_landscape:
        raise GateError(
            f"R3.34 landscape semantics mismatch: {landscape_names}"
        )

    # Exact source-semantic checks.
    source_checks = {
        "resource_abundance_derived_from_natural_suitability_npp": (
            "abundance=np.clip(suit*(.25+.75*nnorm),0,1)" in r334_source
        ),
        "harvest_return_derived_from_abundance_and_taxon_traits": (
            "harvest=np.clip(abundance*tr['edible_yield']*tr['harvestability']"
            in r334_source
        ),
        "propagation_opportunity_is_separate_field": (
            "prop=np.clip(suit*tr['propagation_controllability']" in r334_source
        ),
        "producer_taxa_are_not_retroactive_h0_phylogeny": (
            "ANONYMOUS_FUNCTIONAL_PRODUCER_OPERATIONAL_TAXON_NOT_RETROACTIVE_H0_PHYLOGENY"
            in r334_source
        ),
    }
    if not all(source_checks.values()):
        raise GateError(f"R3.34 semantic source checks failed: {source_checks}")

    r334_land_path = first_existing(root, R334_LANDSCAPE_CANDIDATES)
    r334_land_npz = npz_summary(r334_land_path)

    # ------------------------------------------------------------------
    # Full H0 wild-fauna authority.
    # ------------------------------------------------------------------

    lineage_path = first_existing(root, R321_LINEAGE_CANDIDATES)
    component_path = first_existing(root, R321_COMPONENT_CANDIDATES)
    closure_path = first_existing(root, R321_HISTORICAL_CLOSURE_CANDIDATES)
    functional_path = first_existing(root, R323_SUMMARY_CANDIDATES)

    lineage = load_json(lineage_path)
    components = load_json(component_path)
    functional = load_json(functional_path)

    lineage_count = len(lineage.get("lineages", []))
    component_count = len(components.get("components", []))
    functional_species_count = len(functional.get("species", []))

    if lineage_count != 134:
        raise GateError(f"H0 present lineage count mismatch: {lineage_count}")
    if component_count != 295:
        raise GateError(f"H0 present component count mismatch: {component_count}")
    if functional_species_count != 134:
        raise GateError(
            f"R3.23 functional species count mismatch: {functional_species_count}"
        )

    # ------------------------------------------------------------------
    # Aquatic / marine: A1 already found no filename authority. Content
    # mentions alone are not enough to promote a canonical food resource.
    # ------------------------------------------------------------------

    marine_discovery = a1.get("aquatic_marine_discovery")
    if not isinstance(marine_discovery, dict):
        raise GateError(
            "A1 aquatic_marine_discovery provenance is missing; refusing to default marine diagnostics."
        )
    marine_filename_records = marine_discovery.get("filename_hits")
    marine_content_records = marine_discovery.get("content_hits")
    if not isinstance(marine_filename_records, list) or not isinstance(
        marine_content_records, list
    ):
        raise GateError(
            "A1 marine diagnostic provenance must contain filename_hits and content_hits lists."
        )
    marine_filename_hits = len(marine_filename_records)
    marine_content_hits = len(marine_content_records)

    # ------------------------------------------------------------------
    # Temporal-domain adjudication.
    # ------------------------------------------------------------------

    if a1_ages_ma[-1] != 0.0 or max(a1_ages_ma) < 200.0:
        raise GateError("A1 deep-time age coverage is not the expected 210 Ma -> 0 Ma.")
    if r333_ages_ka != [20.0, 15.0, 14.0, 13.0, 12.0, 11.0, 10.0, 5.0, 0.0]:
        raise GateError(f"Unexpected R3.33 anchor ages: {r333_ages_ka}")
    if r334_ages_ka != r333_ages_ka:
        raise GateError("R3.34 temporal anchors do not match R3.33.")

    checks = {
        "a1_status_and_decision_bound": True,
        "a1_sha256_verified": True,
        "a1_forage_channels_verified": True,
        "a1_deep_time_coverage_verified": True,
        "r333_exogenous_environment_semantics_verified": True,
        "r333_candidate_subset_not_exhaustive_wild_fauna": True,
        "r334_landscape_schema_verified": True,
        "r334_source_semantics_verified": True,
        "r334_recent_temporal_domain_verified": True,
        "h0_full_present_fauna_geometry_verified": True,
        "h0_historical_lineage_closure_present": closure_path.is_file(),
        "aquatic_marine_gap_is_explicit_not_silently_filled": True,
        "human_management_not_used": not False,
        "population_target_not_used": not False,
        "k_x_t_not_materialized": not False,
        "canonical_not_mutated": not False,
    }

    payload: dict[str, Any] = {
        "schema": "ARCANA_R517_B7_A2_SEMANTIC_TEMPORAL_ADJUDICATION_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B7-A2",
        "repository_head": head,
        "status": STATUS,
        "decision": DECISION,
        "checks": checks,
        "governance_states": {
            "human_management_used": False,
            "population_target_used": False,
            "k_x_t_materialized": False,
            "canonical_mutation": False,
            "human_management_not_used": not False,
            "population_target_not_used": not False,
            "k_x_t_not_materialized": not False,
            "canonical_not_mutated": not False,
        },
        "semantic_bindings": {
            "plant_trophic_resource_support": {
                "authority": text_record(a1_payload, root),
                "channels": sorted(required_forage),
                "authorized_role": (
                    "NATIVE_TROPHIC_PLANT_RESOURCE_SUBSTRATE"
                ),
                "forbidden_relabels": [
                    "PHYSICAL_BIOMASS",
                    "HUMAN_EDIBLE_CALORIES",
                    "HUMAN_CARRYING_CAPACITY",
                    "K_X_T",
                ],
                "temporal_domain": {
                    "kind": "DEEP_TIME_SPARSE_ANCHORS",
                    "age_ma": a1_ages_ma,
                    "coverage": "210_MA_TO_0_MA_AT_CANONICAL_A1_ANCHORS",
                    "silent_interpolation_authorized": False,
                },
            },
            "recent_exogenous_environment": {
                "source": text_record(r333_source_path, root),
                "payload": r333_env_npz,
                "environment_fields": r333_env_names,
                "authorized_role": (
                    "RECENT_EXOGENOUS_ENVIRONMENTAL_CONTEXT"
                ),
                "temporal_domain": {
                    "kind": "RECENT_HOLOCENE_LATE_PLEISTOCENE_ANCHORS",
                    "age_ka": r333_ages_ka,
                    "coverage": "20_KA_TO_0_KA",
                    "backprojection_beyond_20ka_authorized": False,
                },
                "excluded_human_conditioned_fields": [
                    "contact_opportunity",
                    "management_intensity",
                    "habituation_tolerance",
                    "reproductive_control",
                    "selective_divergence",
                    "dependency_symbiosis",
                    "animal_food_production_contribution",
                    "domestication_index",
                ],
            },
            "recent_plant_resource_refinement": {
                "source": text_record(r334_source_path, root),
                "payload": r334_land_npz,
                "landscape_fields": landscape_names,
                "source_semantic_checks": source_checks,
                "authorized_fields": {
                    "suitability": (
                        "ECOLOGICAL_SUPPORT_COVARIATE_NOT_FOOD_QUANTITY"
                    ),
                    "resource_abundance": (
                        "PRE_MANAGEMENT_PRODUCER_RESOURCE_ABUNDANCE_PROXY"
                    ),
                    "harvest_return": (
                        "PRE_MANAGEMENT_HUMAN_ACCESSIBLE_PLANT_RESOURCE_OPPORTUNITY_PROXY"
                    ),
                },
                "excluded_field": {
                    "propagation_opportunity": (
                        "MANAGEMENT_AFFORDANCE_EXCLUDED_FROM_NATURAL_BASELINE"
                    )
                },
                "producer_identity_semantics": (
                    "ANONYMOUS_FUNCTIONAL_OPERATIONAL_PRODUCERS_NOT_LITERAL_H0_FLORA_PHYLOGENY"
                ),
                "temporal_domain": {
                    "kind": "RECENT_ONLY",
                    "age_ka": r334_ages_ka,
                    "coverage": "20_KA_TO_0_KA",
                    "backprojection_to_deep_time_authorized": False,
                },
            },
            "wild_animal_resource_support": {
                "present_lineage_registry": text_record(lineage_path, root),
                "present_component_registry": text_record(component_path, root),
                "historical_lineage_closure": text_record(closure_path, root),
                "functional_summary": text_record(functional_path, root),
                "present_species_count": lineage_count,
                "present_component_count": component_count,
                "functional_species_count": functional_species_count,
                "authorized_role": (
                    "FULL_GOVERNED_H0_FAUNA_SOURCE_FAMILY_FOR_WILD_ANIMAL_SUPPORT"
                ),
                "r333_domestication_candidate_subset_authorized_as_exhaustive_inventory": False,
                "temporal_domain": {
                    "present_registry": "0_KA_PRESENT_AUTHORITY",
                    "historical_closure": (
                        "AUTHORIZED_PROVENANCE_SOURCE_FOR_A3_TEMPORAL_RECONSTRUCTION"
                    ),
                    "wild_food_support_materialized_in_a2": False,
                },
            },
            "aquatic_marine_resource_support": {
                "a1_marine_filename_hits": int(marine_filename_hits),
                "a1_marine_content_hits": int(marine_content_hits),
                "a1_diagnostic_provenance": marine_discovery,
                "wetland_aquatic_starch_is_marine_fauna": False,
                "coastal_edge_index_is_marine_productivity": False,
                "status": (
                    "NOT_MATERIALIZED_CANONICAL_BIOLOGICAL_AUTHORITY_NOT_RECOVERED"
                ),
                "policy": (
                    "EXPLICIT_COVERAGE_GAP_ALLOWED_BY_B7_CONTRACT"
                ),
            },
        },
        "cross_temporal_rules": [
            "A1 forage may support deep-time trophic resource semantics only at its governed anchors unless a later interpolation contract is explicitly authorized.",
            "R3.33/R3.34 20-0 ka fields must not be silently backprojected into deep time.",
            "R3.34 anonymous producer taxa must not be relabelled as historical literal flora.",
            "Present H0 fauna registries must not be treated as time-invariant deep-time range maps.",
            "R3.33 domestication-screening candidates must not replace the full H0 fauna inventory.",
            "Aquatic/marine biological food support remains absent until a governed canonical source is recovered or a later new-model gate explicitly authorizes one.",
        ],
        "forbidden_inputs": [
            "R3.32_SUBSISTENCE_READINESS",
            "TECHNOLOGY_STOCKS",
            "PROCESSING",
            "STORAGE",
            "LANDSCAPE_MANAGEMENT",
            "SEASONAL_LOGISTICS",
            "HUMAN_READINESS_WEIGHTED_CONTACT",
            "DOMESTICATION_TRAJECTORY",
            "PRODUCER_COEVOLUTION",
            "AGRICULTURE",
            "SETTLEMENT",
            "POPULATION_TARGET",
            "CITY_STATE_POLITY_TARGET",
        ],
        "materialization_state": {
            "natural_plant_resource_support": "SEMANTICALLY_BOUND_A3_MATERIALIZATION_READY",
            "natural_wild_animal_support": "SOURCE_FAMILY_BOUND_A3_RECONSTRUCTION_REQUIRED",
            "aquatic_marine_support": "EXPLICIT_GAP",
            "human_management_used": False,
            "population_target_used": False,
            "k_x_t_materialized": False,
                "canonical_mutation": False,
        },
        "next_operation": {
            "subphase": "R5.17-B7-A3",
            "name": "NATURAL_RESOURCE_COMPONENT_MATERIALIZATION",
            "constraints": [
                "materialize components separately before any combined food-support scalar",
                "preserve source-specific temporal masks",
                "do not backproject R3.34 beyond 20 ka",
                "use full H0/historical fauna authority rather than R3.33 partner subset",
                "keep aquatic/marine as explicit gap unless canonical authority is recovered",
                "do not materialize K(x,t)",
            ],
        },
    }

    write_json(root / OUT_JSON, payload)

    md = f"""# R5.17-B7-A2 - Semantic Binding & Temporal Coverage Adjudication

STATUS: {STATUS}

DECISION: {DECISION}

## Bound components

- A1 forage: deep-time native trophic plant-resource substrate only.
- R3.33 environment: recent exogenous environmental context, 20-0 ka.
- R3.34 `resource_abundance` / `harvest_return`: recent pre-management plant-resource refinement, 20-0 ka only.
- R3.34 `propagation_opportunity`: excluded as a management affordance.
- Full H0 / R3.21 / R3.23 fauna authority: authorized source family for wild-animal support; present registry is not silently treated as a deep-time range map.
- Aquatic/marine biological support: explicit coverage gap; no canonical biological food authority recovered.

## Hard guardrails

No R3.32 readiness, technology, processing, storage, management, domestication,
agriculture, settlement or population targets are used.

No scalar combined biological-food-support equation is created in A2.

`K(x,t)` remains unmaterialized.

## Next

R5.17-B7-A3 — NATURAL_RESOURCE_COMPONENT_MATERIALIZATION
"""
    (root / OUT_MD).write_text(md, encoding="utf-8")

    print(
        json.dumps(
            {
                "status": STATUS,
                "decision": DECISION,
                "checks_passed": sum(bool(v) for v in checks.values()),
                "checks_total": len(checks),
                "a1_age_anchors": len(a1_ages_ma),
                "r333_r334_recent_anchors": len(r334_ages_ka),
                "h0_present_species": lineage_count,
                "h0_present_components": component_count,
                "marine_filename_hits": int(marine_filename_hits),
                "marine_content_hits": int(marine_content_hits),
                "human_management_used": False,
                "population_target_used": False,
                "k_x_t_materialized": False,
                "canonical_mutation": False,
                "output_json": str(root / OUT_JSON),
                "output_md": str(root / OUT_MD),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
