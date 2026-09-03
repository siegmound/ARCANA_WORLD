from __future__ import annotations

from pathlib import Path
from typing import Any
import inspect
import json

STAGE = "v0.6D1-R4.43"

PARENT_COMPLETE = (
    "PASS_R442_GEONOMICS_MULTI_TRANSITION_BOUNDED_REPLAY_AND_PRODUCTION_"
    "EXECUTION_QUEUE_AUTHORIZATION_PREFLIGHT_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R442_GEONOMICS_MULTI_TRANSITION_BOUNDED_REPLAY_AND_PRODUCTION_"
    "EXECUTION_QUEUE_AUTHORIZATION_PREFLIGHT_SEALED"
)
PARENT_R1 = "PASS_R442_R1_MULTI_STEP_CLOCK_REPAIR_AND_R442_RESEAL_VERIFIED"
PARENT_NEXT = (
    "BUILD_R443_GEONOMICS_SCIENTIFIC_READOUT_AUTHORITY_METRIC_EXTRACTION_"
    "AND_ADJUDICATION_SCHEMA_PREFLIGHT"
)

COMPLETE = (
    "PASS_R443_GEONOMICS_SCIENTIFIC_READOUT_AUTHORITY_METRIC_EXTRACTION_"
    "AND_ADJUDICATION_SCHEMA_PREFLIGHT_COMPLETE"
)
SEALED = (
    "PASS_R443_GEONOMICS_SCIENTIFIC_READOUT_AUTHORITY_METRIC_EXTRACTION_"
    "AND_ADJUDICATION_SCHEMA_PREFLIGHT_SEALED"
)
BLOCKED = (
    "BLOCKED_R443_SCIENTIFIC_READOUT_AUTHORITY_METRIC_EXTRACTION_OR_"
    "ADJUDICATION_SCHEMA_PREFLIGHT_FAILURE"
)
NEXT = (
    "BUILD_R444_GEONOMICS_READOUT_EXTRACTION_DRY_RUN_AND_ADJUDICATION_INPUT_"
    "VALIDATION"
)

OUT = Path("outputs/v0_6D1_R4_43")
SEAL = Path("outputs/v0_6D1_R4_43_SEAL/R4_43_FINAL_SEAL_AUDIT.json")
CFG = Path(
    "configs/world1_r443_geonomics_scientific_readout_authority_metric_"
    "extraction_adjudication_schema_preflight_v0_6D1_R4_43.json"
)

R442 = Path("outputs/v0_6D1_R4_42/R4_42_INTEGRATED_AUDIT.json")
R442_SEAL = Path("outputs/v0_6D1_R4_42_SEAL/R4_42_FINAL_SEAL_AUDIT.json")
R442_R1 = Path(
    "outputs/v0_6D1_R4_42_R1/R4_42_R1_POSTREPAIR_RESEAL_AUDIT.json"
)

J14 = "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"
J18 = "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
J21 = "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _source_audit() -> dict[str, Any]:
    import geonomics as gnx
    import geonomics.structs.species as sppmod
    import geonomics.utils.spatial as spatial

    model_get_coords = inspect.getsource(gnx.Model.get_coords)
    spp_get_coords = inspect.getsource(sppmod.Species._get_coords)
    spp_set_coords = inspect.getsource(sppmod.Species._set_coords_and_cells)
    spp_set_kdtree = inspect.getsource(sppmod.Species._set_kd_tree)
    kdtree_init = inspect.getsource(spatial._KDTree.__init__)
    spp_density = inspect.getsource(sppmod.Species._calc_density)

    checks = {
        "version_1_4_9":
            str(getattr(gnx, "__version__", "")) == "1.4.9",
        "public_model_get_coords_exists":
            "def get_coords(self, spp=0, individs=None)" in model_get_coords,
        "species_get_coords_uses_stored_continuous_coords":
            "_coord_attrgetter" in spp_get_coords,
        "species_cells_floor_coords":
            "np.int32(np.floor(self._coords))" in spp_set_coords,
        "species_kdtree_built_from_coords":
            "_KDTree(coords=self._coords" in spp_set_kdtree,
        "kdtree_wraps_scipy_ckdtree":
            "cKDTree(data=coords" in kdtree_init,
        "density_is_species_density":
            "Calculate an interpolated raster of local species density"
            in spp_density,
    }
    ok = all(checks.values())
    return {
        "stage": STAGE,
        "status":
            "R443_GEONOMICS_149_READOUT_SOURCE_SURFACE_AUDITED"
            if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "source_semantics": {
            "coordinate_readback":
                "CONTINUOUS_XY_COORDINATES_FROM_SPECIES_INDIVIDUAL_STORAGE",
            "native_cell_assignment":
                "FLOOR_CONTINUOUS_XY_TO_INTEGER_CELLS",
            "native_neighbor_index":
                "GEONOMICS_KDTREE_WRAPPER_AROUND_SCIPY_CKDTREE",
            "density_semantics":
                "BIOLOGICAL_SPECIES_DENSITY_NOT_LITERAL_FOR_ARCANA_CARRIERS",
        },
        "pass": ok,
    }


def _readout_registry() -> dict[str, Any]:
    carrier_metrics = [
        {
            "metric_id": "GNX_CARRIER_COORDINATE_READBACK_XY",
            "role": "EXACT_INTEGRITY_ONLY",
            "source": "Model.get_coords / Species._get_coords",
            "unit": "grid_coordinate_units",
            "shape": "N_carriers x 2",
            "semantics":
                "nonliteral carrier support coordinates; not observed history",
            "adjudicative": False,
            "scientific_descriptive": False,
            "exact_comparison_required": True,
        },
        {
            "metric_id": "GNX_CARRIER_NATIVE_CELL_READBACK_IJ",
            "role": "EXACT_INTEGRITY_ONLY",
            "source": "Species._cells",
            "unit": "integer_grid_cells",
            "semantics": "floor(y,x) native cell assignment integrity",
            "adjudicative": False,
            "scientific_descriptive": False,
            "exact_comparison_required": True,
        },
        {
            "metric_id": "GNX_CARRIER_NEAREST_NEIGHBOR_DISTANCE",
            "role": "SCIENTIFIC_DESCRIPTIVE_CONNECTIVITY",
            "source": "Species._kd_tree.tree.query(coords,k=2)",
            "unit": "grid_coordinate_units",
            "raw_output":
                "one nearest-nonneighbor distance per carrier when N>=2",
            "summary_output": [
                "count",
                "finite_count",
                "min",
                "median",
                "mean",
                "max",
            ],
            "single_carrier_policy":
                "NOT_APPLICABLE_SINGLE_CARRIER_NO_FAILURE",
            "semantics":
                "spatial connectivity descriptor of canonical nonliteral deme supports",
            "adjudicative": False,
            "scientific_descriptive": True,
            "numeric_acceptance_threshold": None,
        },
    ]

    layer_metrics = [
        {
            "metric_id": "GNX_NATIVE_LAYER_RASTER_READBACK",
            "role": "EXACT_INTEGRITY_ONLY",
            "source": "Landscape Layer.rast",
            "unit": "canonical_native_layer_units",
            "scope": "147 R4.39/R4.42 native dynamic layers only",
            "adjudicative": False,
            "scientific_descriptive": False,
            "exact_comparison_required": True,
        },
        {
            "metric_id": "GNX_NATIVE_LAYER_DESCRIPTIVE_SUMMARY",
            "role": "SCIENTIFIC_DESCRIPTIVE_LAYER_STATE",
            "source": "Landscape Layer.rast",
            "unit": "per-layer canonical units",
            "summary_output": [
                "finite_count",
                "min",
                "max",
                "mean",
                "std",
            ],
            "scope": "147 native layers; 4 dynamic sidecars excluded",
            "adjudicative": False,
            "scientific_descriptive": True,
            "numeric_acceptance_threshold": None,
        },
    ]

    forbidden = [
        {
            "readout": "Species.N_or_calc_density_as_population_density",
            "reason":
                "one ARCANA carrier is one active canonical deme support, not one biological individual",
        },
        {
            "readout": "Species.Nt_as_population_history",
            "reason":
                "autonomous biological population semantics are forbidden",
        },
        {
            "readout": "births_deaths_as_scientific_history",
            "reason":
                "R4.40/R4.42 authorize zero autonomous demography",
        },
        {
            "readout": "age_stage_as_physical_time",
            "reason":
                "ordinal Geonomics timestep is not biological age",
        },
        {
            "readout": "K_as_population_carrying_capacity_adjudication",
            "reason":
                "construction/support K is not authorized as canonical population capacity",
        },
        {
            "readout": "fitness_genotype_heterozygosity_genetic_distance",
            "reason":
                "R4.36/R4.38 carrier species is intentionally nongenomic",
        },
        {
            "readout": "movement_distance_or_dispersal_history",
            "reason":
                "autonomous Geonomics movement is forbidden",
        },
        {
            "readout": "four_dynamic_sidecars_as_native_layer_metrics",
            "reason":
                "temperature_anomaly_c, precipitation_factor, npp_factor, sea_level_anomaly_m remain external sidecars",
        },
    ]

    jobs = {
        J14: {
            "domain": "sapient_spatial_connectivity_3Ma_to_200ka",
            "authorized_metrics": [
                x["metric_id"] for x in carrier_metrics
            ],
            "historical_prediction_claim_authorized": False,
        },
        J18: {
            "domain": "sapient_spatial_connectivity_200ka_to_0",
            "authorized_metrics": [
                x["metric_id"] for x in carrier_metrics
            ],
            "historical_prediction_claim_authorized": False,
        },
        J21: {
            "domain": "producer_environment_native_layer_state_20ka_to_0",
            "authorized_metrics": [
                x["metric_id"] for x in layer_metrics
            ],
            "historical_prediction_claim_authorized": False,
        },
    }

    return {
        "stage": STAGE,
        "status": "R443_GEONOMICS_SCIENTIFIC_READOUT_AUTHORITY_REGISTRY_FROZEN",
        "carrier_metrics": carrier_metrics,
        "layer_metrics": layer_metrics,
        "forbidden_readouts": forbidden,
        "jobs": jobs,
        "authorized_metric_count":
            len(carrier_metrics) * 2 + len(layer_metrics),
        "unique_metric_definition_count":
            len(carrier_metrics) + len(layer_metrics),
        "result_selected_metric_choice": False,
        "engine_result_defines_arcana_target": False,
        "canonical_rewrite_authorized": False,
    }


def _extraction_schema(registry: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage": STAGE,
        "status": "R443_GEONOMICS_METRIC_EXTRACTION_SCHEMA_FROZEN",
        "schema_version": 1,
        "common_record_fields": [
            "stage",
            "job_id",
            "replicate_index",
            "frozen_seed",
            "canonical_state_index",
            "canonical_physical_age",
            "metric_id",
            "metric_role",
            "source_object",
            "value_shape",
            "finite",
            "payload_sha256",
        ],
        "carrier_nn_distance_schema": {
            "raw_vector_preserved": True,
            "raw_vector_order":
                "current Species carrier-key iteration order",
            "self_neighbor_removed_by_k2_second_column": True,
            "N_lt_2_policy": "NOT_APPLICABLE_SINGLE_CARRIER_NO_FAILURE",
            "summary_fields": [
                "count",
                "finite_count",
                "min",
                "median",
                "mean",
                "max",
            ],
            "rounding_authorized": False,
            "normalization_authorized": False,
            "thresholding_authorized": False,
        },
        "layer_summary_schema": {
            "per_layer": True,
            "layer_order":
                "frozen R4.39 dynamic native authority order",
            "summary_fields": [
                "finite_count",
                "min",
                "max",
                "mean",
                "std",
            ],
            "raster_digest_required": True,
            "four_sidecars_excluded": True,
            "rounding_authorized": False,
            "normalization_authorized": False,
            "clipping_authorized": False,
        },
        "integrity_payloads": {
            "coordinates":
                "exact float64 x,y sequence plus SHA256",
            "cells":
                "exact integer cell sequence plus SHA256",
            "native_layers":
                "exact raster shape/dtype/bytes plus SHA256",
        },
        "metric_extraction_dry_run_validated": False,
        "scientific_execution_performed": False,
    }


def _adjudication_schema() -> dict[str, Any]:
    return {
        "stage": STAGE,
        "status": "R443_GEONOMICS_ADJUDICATION_SCHEMA_FROZEN",
        "schema_version": 1,
        "classes": {
            "EXACT_INTEGRITY_ONLY": {
                "comparison":
                    "exact canonical replay authority equality; no tolerance",
                "mismatch_classification":
                    "ADAPTER_OR_RUNTIME_INTEGRITY_FAILURE",
                "scientific_divergence_claim": False,
                "can_change_canonical_state": False,
            },
            "SCIENTIFIC_DESCRIPTIVE_CONNECTIVITY": {
                "comparison":
                    "record raw and summary Geonomics native spatial descriptor",
                "numeric_acceptance_threshold": None,
                "automatic_pass_fail_from_value": False,
                "can_define_arcana_target": False,
                "can_change_canonical_state": False,
                "role":
                    "external-engine descriptive revalidation evidence only",
            },
            "SCIENTIFIC_DESCRIPTIVE_LAYER_STATE": {
                "comparison":
                    "record raw layer digest and descriptive summaries",
                "numeric_acceptance_threshold": None,
                "automatic_pass_fail_from_value": False,
                "can_define_arcana_target": False,
                "can_change_canonical_state": False,
                "role":
                    "external-engine descriptive layer-state evidence only",
            },
            "FORBIDDEN_NONLITERAL_BIOLOGY": {
                "accepted": False,
                "failure_if_emitted_as_scientific_evidence": True,
            },
        },
        "global_rules": {
            "majority_vote_authorized": False,
            "result_selected_threshold_authorized": False,
            "result_selected_metric_authorized": False,
            "engine_output_target_definition_authorized": False,
            "backward_target_inference_authorized": False,
            "canonical_rewrite_authorized": False,
            "readout_failure_may_be_relabelled_as_scientific_divergence": False,
            "integrity_failure_may_be_relabelled_as_scientific_divergence": False,
        },
        "scientific_readout_authority_closed": True,
        "adjudicative_numeric_threshold_count": 0,
        "metric_extraction_dry_run_validated": False,
        "scientific_execution_authorized": False,
    }


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    parent = load(root / R442)
    parent_seal = load(root / R442_SEAL)
    parent_r1 = load(root / R442_R1)

    source = _source_audit()
    registry = _readout_registry()
    extraction = _extraction_schema(registry)
    adjudication = _adjudication_schema()

    write(root / OUT / "R4_43_GEONOMICS_READOUT_SOURCE_AUDIT.json", source)
    write(root / OUT / "R4_43_SCIENTIFIC_READOUT_AUTHORITY_REGISTRY.json", registry)
    write(root / OUT / "R4_43_METRIC_EXTRACTION_SCHEMA.json", extraction)
    write(root / OUT / "R4_43_ADJUDICATION_SCHEMA.json", adjudication)

    jobs = registry["jobs"]
    forbidden = registry["forbidden_readouts"]

    checks = {
        "parent_r442_complete_26_26":
            parent.get("status") == PARENT_COMPLETE
            and parent.get("checks_passed") == 26
            and parent.get("checks_failed") == 0,
        "parent_r442_sealed_21_21":
            parent_seal.get("status") == PARENT_SEALED
            and parent_seal.get("verdict") == "SEALED"
            and parent_seal.get("checks_passed") == 21
            and parent_seal.get("checks_failed") == 0,
        "parent_r442_r1_verified_16_16":
            parent_r1.get("status") == PARENT_R1
            and parent_r1.get("checks_passed") == 16
            and parent_r1.get("checks_total") == 16,
        "parent_next_action_r443":
            parent.get("next_action") == PARENT_NEXT
            and parent_seal.get("next_action") == PARENT_NEXT
            and parent_r1.get("next_action") == PARENT_NEXT,
        "policy_frozen":
            cfg.get("policy")
            == "R443_PREDECLARE_READOUTS_BEFORE_ANY_SCIENTIFIC_EXECUTION",
        "production_queue_authority_preserved":
            parent.get("production_execution_queue_authorized") is True
            and parent.get("authorized_queue")
            == "ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE",
        "default_queue_still_forbidden":
            parent.get("default_geonomics_queue_authorized") is False,
        "source_surface_audited":
            source.get("pass") is True,
        "public_coordinate_readback_source_valid":
            source["checks"]["public_model_get_coords_exists"] is True,
        "continuous_coordinate_semantics_valid":
            source["checks"][
                "species_get_coords_uses_stored_continuous_coords"
            ] is True,
        "native_cell_floor_semantics_valid":
            source["checks"]["species_cells_floor_coords"] is True,
        "native_kdtree_semantics_valid":
            source["checks"]["species_kdtree_built_from_coords"] is True
            and source["checks"]["kdtree_wraps_scipy_ckdtree"] is True,
        "biological_density_semantics_detected":
            source["checks"]["density_is_species_density"] is True,
        "readout_registry_frozen":
            registry.get("status")
            == "R443_GEONOMICS_SCIENTIFIC_READOUT_AUTHORITY_REGISTRY_FROZEN",
        "five_unique_metric_definitions":
            registry.get("unique_metric_definition_count") == 5,
        "j14_exact_three_metric_ids":
            len(jobs[J14]["authorized_metrics"]) == 3,
        "j18_exact_three_metric_ids":
            len(jobs[J18]["authorized_metrics"]) == 3,
        "j21_exact_two_metric_ids":
            len(jobs[J21]["authorized_metrics"]) == 2,
        "j14_j18_historical_prediction_claim_off":
            jobs[J14]["historical_prediction_claim_authorized"] is False
            and jobs[J18]["historical_prediction_claim_authorized"] is False,
        "j21_historical_prediction_claim_off":
            jobs[J21]["historical_prediction_claim_authorized"] is False,
        "nonliteral_density_forbidden":
            any(
                x["readout"]
                == "Species.N_or_calc_density_as_population_density"
                for x in forbidden
            ),
        "Nt_population_history_forbidden":
            any(
                x["readout"] == "Species.Nt_as_population_history"
                for x in forbidden
            ),
        "birth_death_scientific_history_forbidden":
            any(
                x["readout"] == "births_deaths_as_scientific_history"
                for x in forbidden
            ),
        "genetic_readouts_forbidden":
            any(
                x["readout"]
                == "fitness_genotype_heterozygosity_genetic_distance"
                for x in forbidden
            ),
        "movement_history_forbidden":
            any(
                x["readout"] == "movement_distance_or_dispersal_history"
                for x in forbidden
            ),
        "four_sidecars_forbidden_as_native_metrics":
            any(
                x["readout"]
                == "four_dynamic_sidecars_as_native_layer_metrics"
                for x in forbidden
            ),
        "metric_extraction_schema_frozen":
            extraction.get("status")
            == "R443_GEONOMICS_METRIC_EXTRACTION_SCHEMA_FROZEN",
        "nn_raw_vector_preserved":
            extraction["carrier_nn_distance_schema"][
                "raw_vector_preserved"
            ] is True,
        "nn_no_threshold":
            extraction["carrier_nn_distance_schema"][
                "thresholding_authorized"
            ] is False,
        "layer_sidecars_excluded":
            extraction["layer_summary_schema"][
                "four_sidecars_excluded"
            ] is True,
        "adjudication_schema_frozen":
            adjudication.get("status")
            == "R443_GEONOMICS_ADJUDICATION_SCHEMA_FROZEN",
        "scientific_readout_authority_closed":
            adjudication.get("scientific_readout_authority_closed") is True,
        "zero_adjudicative_numeric_thresholds":
            adjudication.get("adjudicative_numeric_threshold_count") == 0,
        "no_majority_vote":
            adjudication["global_rules"]["majority_vote_authorized"]
            is False,
        "no_result_selected_threshold":
            adjudication["global_rules"][
                "result_selected_threshold_authorized"
            ] is False,
        "no_engine_output_target_definition":
            adjudication["global_rules"][
                "engine_output_target_definition_authorized"
            ] is False,
        "no_canonical_rewrite":
            adjudication["global_rules"][
                "canonical_rewrite_authorized"
            ] is False,
        "metric_extraction_dry_run_pending":
            extraction.get("metric_extraction_dry_run_validated") is False,
        "scientific_execution_not_authorized":
            adjudication.get("scientific_execution_authorized") is False,
        "geonomics_execution_not_ready":
            cfg.get("geonomics_execution_ready") is False,
        "no_scientific_execution":
            cfg.get("scientific_engine_execution_performed") is False,
        "no_target_numeric":
            cfg.get("target_numeric_execution_performed") is False,
        "no_readjudication":
            cfg.get("readjudication_performed") is False,
        "canonical_unchanged":
            cfg.get("canonical_state_changed") is False,
        "deep_off":
            cfg.get("deep_biological_coupling") is False,
        "deferred_p2_two":
            parent.get("active_deferred_p2_cell_count") == 2,
        "proxy_context_two":
            parent.get("proxy_context_only_count") == 2,
        "p3_backlog_six":
            parent.get("p3_backlog_cell_count") == 6,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "status": COMPLETE if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "geonomics_version": "1.4.9",
        "production_execution_queue_authorized":
            parent.get("production_execution_queue_authorized"),
        "authorized_queue": parent.get("authorized_queue"),
        "scientific_readout_authority_closed": bool(ok),
        "unique_authorized_metric_definition_count":
            registry.get("unique_metric_definition_count"),
        "j14_authorized_metric_count":
            len(jobs[J14]["authorized_metrics"]),
        "j18_authorized_metric_count":
            len(jobs[J18]["authorized_metrics"]),
        "j21_authorized_metric_count":
            len(jobs[J21]["authorized_metrics"]),
        "forbidden_readout_count": len(forbidden),
        "adjudicative_numeric_threshold_count": 0,
        "metric_extraction_dry_run_validated": False,
        "scientific_execution_authorized": False,
        "geonomics_execution_ready": False,
        "scientific_engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action":
            NEXT if ok else "REPAIR_R443_READOUT_OR_ADJUDICATION_SCHEMA",
    }
    write(root / OUT / "R4_43_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    a = load(root / OUT / "R4_43_INTEGRATED_AUDIT.json")
    reg = load(root / OUT / "R4_43_SCIENTIFIC_READOUT_AUTHORITY_REGISTRY.json")
    ext = load(root / OUT / "R4_43_METRIC_EXTRACTION_SCHEMA.json")
    adj = load(root / OUT / "R4_43_ADJUDICATION_SCHEMA.json")

    checks = {
        "r443_complete":
            a.get("status") == COMPLETE and a.get("checks_failed") == 0,
        "production_queue_authority_preserved":
            a.get("production_execution_queue_authorized") is True
            and a.get("authorized_queue")
            == "ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE",
        "readout_authority_closed":
            a.get("scientific_readout_authority_closed") is True,
        "five_unique_metric_definitions":
            a.get("unique_authorized_metric_definition_count") == 5,
        "j14_three_metrics":
            a.get("j14_authorized_metric_count") == 3,
        "j18_three_metrics":
            a.get("j18_authorized_metric_count") == 3,
        "j21_two_metrics":
            a.get("j21_authorized_metric_count") == 2,
        "forbidden_readouts_present":
            a.get("forbidden_readout_count") >= 8,
        "carrier_density_forbidden":
            any(
                x["readout"]
                == "Species.N_or_calc_density_as_population_density"
                for x in reg["forbidden_readouts"]
            ),
        "nn_metric_descriptive_only":
            next(
                x for x in reg["carrier_metrics"]
                if x["metric_id"]
                == "GNX_CARRIER_NEAREST_NEIGHBOR_DISTANCE"
            )["role"] == "SCIENTIFIC_DESCRIPTIVE_CONNECTIVITY",
        "layer_summary_descriptive_only":
            next(
                x for x in reg["layer_metrics"]
                if x["metric_id"]
                == "GNX_NATIVE_LAYER_DESCRIPTIVE_SUMMARY"
            )["role"] == "SCIENTIFIC_DESCRIPTIVE_LAYER_STATE",
        "raw_nn_vector_preserved":
            ext["carrier_nn_distance_schema"][
                "raw_vector_preserved"
            ] is True,
        "sidecars_excluded":
            ext["layer_summary_schema"]["four_sidecars_excluded"] is True,
        "zero_numeric_thresholds":
            adj.get("adjudicative_numeric_threshold_count") == 0,
        "no_majority_vote":
            adj["global_rules"]["majority_vote_authorized"] is False,
        "no_result_selected_threshold":
            adj["global_rules"][
                "result_selected_threshold_authorized"
            ] is False,
        "no_engine_target_definition":
            adj["global_rules"][
                "engine_output_target_definition_authorized"
            ] is False,
        "no_canonical_rewrite":
            adj["global_rules"]["canonical_rewrite_authorized"] is False,
        "extraction_dry_run_pending":
            a.get("metric_extraction_dry_run_validated") is False,
        "scientific_execution_not_authorized":
            a.get("scientific_execution_authorized") is False,
        "execution_not_ready":
            a.get("geonomics_execution_ready") is False,
        "no_scientific_execution":
            a.get("scientific_engine_execution_performed") is False,
        "no_target_numeric":
            a.get("target_numeric_execution_performed") is False,
        "no_readjudication":
            a.get("readjudication_performed") is False,
        "canonical_unchanged":
            a.get("canonical_state_changed") is False,
        "deferred_p2_two":
            a.get("active_deferred_p2_cell_count") == 2,
        "proxy_context_two":
            a.get("proxy_context_only_count") == 2,
        "p3_backlog_six":
            a.get("p3_backlog_cell_count") == 6,
        "next_r444":
            a.get("next_action") == NEXT,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "audit":
            "FINAL_GEONOMICS_SCIENTIFIC_READOUT_AUTHORITY_METRIC_EXTRACTION_"
            "AND_ADJUDICATION_SCHEMA_PREFLIGHT",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "production_execution_queue_authorized":
                a.get("production_execution_queue_authorized"),
            "scientific_readout_authority_closed":
                a.get("scientific_readout_authority_closed"),
            "unique_metric_definition_count":
                a.get("unique_authorized_metric_definition_count"),
            "forbidden_readout_count":
                a.get("forbidden_readout_count"),
            "adjudicative_numeric_threshold_count": 0,
            "metric_extraction_dry_run_validated": False,
            "scientific_execution_authorized": False,
            "geonomics_execution_ready": False,
            "scientific_engine_execution_performed": False,
            "canonical_state_changed": False,
            "deep_biological_coupling": False,
            "next_action": NEXT,
        },
        "next_action": NEXT,
    }
    write(root / SEAL, out)
    return out
