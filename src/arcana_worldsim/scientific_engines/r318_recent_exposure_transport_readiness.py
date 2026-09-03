from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping
import json
import numpy as np

from . import r38_restartable_checkpoint as r38
from . import r317_recent_restart_sync as r317
from . import r316_c2_bridge_fixed_biology as r316
from arcana_worldsim.late_cenozoic.production_interface import D3LateCenozoicSubstrateAdapter

STAGE = "v0.6D1-R3.18"
PARENT_STAGE = "v0.6D1-R3.17"
PHYSICAL_START_AGE_MA = 0.120
PHYSICAL_END_AGE_MA = 0.0
BIOLOGY_STATE_AGE_MA = 0.125
TRANSPORT_BOUNDARY_AGE_MA = 0.0625
BIOLOGY_CADENCE_YEARS = 125_000.0
TRANSPORT_CADENCE_YEARS = 62_500.0
PENDING_R317_YEARS = 5_000.0
RECENT_YEARS = 120_000.0
FULL_MACROSTEP_YEARS = 125_000.0
R317_SEALED_VERDICT = (
    "PASS_R317_EXACT_120KA_ENVIRONMENTAL_RESTART__"
    "125KA_BIOLOGY_STATE_AND_5KYR_PENDING_EXPOSURE_SEALED"
)
R317_READY_VERDICT = (
    "PASS_R317_EXACT_120KA_ENVIRONMENTAL_RESTART__"
    "R316_125KA_BIOLOGY_PRESERVED_WITH_5KYR_PENDING_EXPOSURE"
)
R317_ENVELOPE_SHA256 = "5b800279324afdd19279fa0c395ace822b4104155690191f81c6be884d2aeca8"
R317_ACCUMULATOR_SHA256 = "b191faae44b4db8bc0afaaba942b0f04087758fa554c480375eb0f753ab309cc"
VERDICT = (
    "PASS_R318_120KA_TO_0_RECENT_H0_EXPOSURE_COMPLETED__"
    "125KA_BIOLOGY_PRESERVED_TRANSPORT_PHASE_OPERATOR_AUDIT_READY"
)
ENVELOPE_SCHEMA = "ARCANA_R318_RECENT_EXPOSURE_TRANSPORT_PHASE_READINESS_V1"
ACCUMULATOR_SCHEMA = "ARCANA_R318_125KA_TO_0_EXPOSURE_AND_TRANSPORT_PHASES_V1"
SUMMARY_SCHEMA = "ARCANA_R318_RECENT_EXPOSURE_COMPLETION_SUMMARY_V1"

AVERAGED_FIELDS = r316.AVERAGED_FIELDS


@dataclass(frozen=True)
class R318Config:
    physical_start_age_ma: float = PHYSICAL_START_AGE_MA
    physical_end_age_ma: float = PHYSICAL_END_AGE_MA
    biology_state_age_ma: float = BIOLOGY_STATE_AGE_MA
    transport_boundary_age_ma: float = TRANSPORT_BOUNDARY_AGE_MA
    biology_cadence_years: float = BIOLOGY_CADENCE_YEARS
    transport_cadence_years: float = TRANSPORT_CADENCE_YEARS
    advance_biology: bool = False
    advance_transport: bool = False
    advance_gene_flow: bool = False
    advance_lifecycle_gates: bool = False
    deep_biological_coupling: bool = False

    def __post_init__(self) -> None:
        if abs(self.physical_start_age_ma - PHYSICAL_START_AGE_MA) > 1e-12:
            raise ValueError("R3.18 starts at the R3.17 exact 120 ka physical restart")
        if abs(self.physical_end_age_ma) > 1e-12:
            raise ValueError("R3.18 recent exposure endpoint is 0 ka")
        if abs(self.biology_state_age_ma - BIOLOGY_STATE_AGE_MA) > 1e-12:
            raise ValueError("R3.18 preserves the SEALED 125 ka biology state")
        if abs(self.transport_boundary_age_ma - TRANSPORT_BOUNDARY_AGE_MA) > 1e-12:
            raise ValueError("R3.18 derived transport boundary is exactly 62.5 ka")
        if abs(self.biology_cadence_years - BIOLOGY_CADENCE_YEARS) > 1e-9:
            raise ValueError("R3.18 preserves the SEALED 125 kyr biology cadence")
        if abs(self.transport_cadence_years - TRANSPORT_CADENCE_YEARS) > 1e-9:
            raise ValueError("R3.18 preserves the SEALED 62.5 kyr transport cadence")
        if any((self.advance_biology, self.advance_transport, self.advance_gene_flow,
                self.advance_lifecycle_gates, self.deep_biological_coupling)):
            raise ValueError("R3.18 is an exposure-completion/readiness stage; biology remains frozen")


def _sha256(path: Path) -> str:
    h = sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _r317_paths(root: Path) -> dict[str, Path]:
    run = Path(root) / "local_runs/v0_6D1_R3_17"
    return {
        "seal": Path(root) / "R3_17_SEAL_SUMMARY.json",
        "audit": Path(root) / "outputs/v0_6D1_R3_17/FORMAL_AUDIT_SEALED_v0_6D1_R3_17.json",
        "summary": run / "R3_17_EXACT_120KA_ENVIRONMENTAL_RESTART_SUMMARY.json",
        "envelope": run / "R3_17_120KA_DUAL_CLOCK_RESTART_ENVELOPE.json",
        "accumulator": run / "R3_17_PENDING_125_TO_120KA_EXPOSURE_ACCUMULATOR.npz",
    }


def validate_parent_r317_authority(root: Path) -> dict[str, Any]:
    root = Path(root)
    p = _r317_paths(root)
    for path in p.values():
        if not path.is_file():
            raise RuntimeError(f"R3.18 requires R3.17 SEALED evidence: missing {path}")
    seal = json.loads(p["seal"].read_text(encoding="utf-8"))
    audit = json.loads(p["audit"].read_text(encoding="utf-8"))
    summary = json.loads(p["summary"].read_text(encoding="utf-8"))
    envelope = json.loads(p["envelope"].read_text(encoding="utf-8"))
    if seal.get("stage") != PARENT_STAGE or seal.get("verdict") != R317_SEALED_VERDICT:
        raise RuntimeError("R3.17 seal verdict is not authoritative")
    if audit.get("verdict") != R317_SEALED_VERDICT or audit.get("checks") != "123/123":
        raise RuntimeError("R3.17 sealed audit is not authoritative")
    if summary.get("verdict") != R317_READY_VERDICT:
        raise RuntimeError("R3.17 canonical summary verdict mismatch")
    if _sha256(p["envelope"]) != R317_ENVELOPE_SHA256:
        raise RuntimeError("R3.17 restart envelope SHA mismatch")
    if _sha256(p["accumulator"]) != R317_ACCUMULATOR_SHA256:
        raise RuntimeError("R3.17 pending accumulator SHA mismatch")
    if abs(float(envelope.get("physical_restart_age_ma", -1.0)) - PHYSICAL_START_AGE_MA) > 1e-12:
        raise RuntimeError("R3.17 restart envelope is not exactly 120 ka")
    if abs(float(envelope.get("biology_state_age_ma", -1.0)) - BIOLOGY_STATE_AGE_MA) > 1e-12:
        raise RuntimeError("R3.17 biology state is not preserved at 125 ka")
    pending = r317.load_accumulator(p["accumulator"])
    if abs(float(pending["duration_years"]) - PENDING_R317_YEARS) > 1e-9:
        raise RuntimeError("R3.17 pending exposure duration is not 5 kyr")
    if set(pending["integrals"]) != set(AVERAGED_FIELDS):
        raise RuntimeError("R3.17 pending exposure field schema mismatch")
    parent316 = r317.validate_parent_r316_authority(root)
    return {
        "state": parent316["state"],
        "a1": parent316["a1"],
        "c2": parent316["c2"],
        "clock": parent316["clock"],
        "pending": pending,
        "r317_seal_sha256": _sha256(p["seal"]),
        "r317_audit_sha256": _sha256(p["audit"]),
        "r317_summary_sha256": _sha256(p["summary"]),
        "r317_envelope_sha256": R317_ENVELOPE_SHA256,
        "r317_accumulator_sha256": R317_ACCUMULATOR_SHA256,
        "r316_seal_sha256": parent316["r316_seal_sha256"],
    }


def _unique_desc(values: list[float], tol: float = 1e-13) -> list[float]:
    out: list[float] = []
    for x in sorted((float(v) for v in values), reverse=True):
        if not out or abs(x - out[-1]) > tol:
            out.append(x)
    return out


def recent_partition(clock: Mapping[str, Any], older_age_ma: float = PHYSICAL_START_AGE_MA,
                     younger_age_ma: float = PHYSICAL_END_AGE_MA,
                     include_transport_boundary: bool = True) -> dict[str, Any]:
    older = float(older_age_ma); younger = float(younger_age_ma)
    if not older > younger - 1e-15:
        raise ValueError("R3.18 partition requires older >= younger with nonzero duration")
    ages = [older, younger]
    if include_transport_boundary and younger - 1e-12 <= TRANSPORT_BOUNDARY_AGE_MA <= older + 1e-12:
        ages.append(TRANSPORT_BOUNDARY_AGE_MA)
    ages.extend(float(x) for x in np.asarray(clock["age_ma"], dtype=float)
                if younger - 1e-12 <= float(x) <= older + 1e-12)
    nodes = _unique_desc(ages)
    if abs(nodes[0] - older) > 1e-12 or abs(nodes[-1] - younger) > 1e-12:
        raise RuntimeError("R3.18 recent partition lost endpoints")
    segments = []
    for a, b in zip(nodes[:-1], nodes[1:]):
        dt = (a - b) * 1e6
        if dt <= 0:
            raise RuntimeError("R3.18 non-positive recent exposure segment")
        segments.append({"older_age_ma": a, "younger_age_ma": b, "dt_years": dt})
    total = sum(float(x["dt_years"]) for x in segments)
    want = (older - younger) * 1e6
    if abs(total - want) > 1e-6:
        raise RuntimeError("R3.18 recent exposure partition duration mismatch")
    return {
        "older_age_ma": older,
        "younger_age_ma": younger,
        "nodes_age_ma": nodes,
        "segments": segments,
        "segment_count": len(segments),
        "node_count": len(nodes),
        "total_years": total,
        "contains_62p5ka_transport_boundary": any(abs(x - TRANSPORT_BOUNDARY_AGE_MA) <= 1e-12 for x in nodes),
    }


def integrate_partition(adapter: D3LateCenozoicSubstrateAdapter, part: Mapping[str, Any]) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    nodes = list(part["nodes_age_ma"])
    states = [adapter.state_at_age(float(age)) for age in nodes]
    accum = {k: np.zeros_like(np.asarray(states[0][k], dtype=float), dtype=float) for k in AVERAGED_FIELDS}
    for i, seg in enumerate(part["segments"]):
        dt = float(seg["dt_years"])
        for key in AVERAGED_FIELDS:
            a = np.asarray(states[i][key], dtype=float)
            b = np.asarray(states[i + 1][key], dtype=float)
            if a.shape != b.shape or a.shape != accum[key].shape:
                raise RuntimeError(f"R3.18 exposure field shape drift: {key}")
            accum[key] += 0.5 * (a + b) * dt
    diag = {
        "older_age_ma": float(part["older_age_ma"]),
        "younger_age_ma": float(part["younger_age_ma"]),
        "duration_years": float(part["total_years"]),
        "segment_count": int(part["segment_count"]),
        "node_count": int(part["node_count"]),
        "contains_62p5ka_transport_boundary": bool(part.get("contains_62p5ka_transport_boundary", False)),
        "averaging_rule": "TRAPEZOID_INTEGRAL_ON_R314_C2_RECENT_ADAPTIVE_CLOCK_WITH_EXACT_62P5KA_INSERTION",
    }
    return accum, diag


def combine_integrals(a: Mapping[str, np.ndarray], b: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    if set(a) != set(AVERAGED_FIELDS) or set(b) != set(AVERAGED_FIELDS):
        raise ValueError("R3.18 integral schemas must match the governed environment fields")
    out: dict[str, np.ndarray] = {}
    for key in AVERAGED_FIELDS:
        aa = np.asarray(a[key], dtype=float); bb = np.asarray(b[key], dtype=float)
        if aa.shape != bb.shape:
            raise RuntimeError(f"R3.18 integral shape mismatch: {key}")
        out[key] = aa + bb
    return out


def effective_environment(integrals: Mapping[str, np.ndarray], duration_years: float) -> dict[str, Any]:
    d = float(duration_years)
    if d <= 0:
        raise ValueError("R3.18 effective environment duration must be positive")
    avg = {k: np.asarray(integrals[k], dtype=float) / d for k in AVERAGED_FIELDS}
    avg["land_support"] = np.clip(avg["land_support"], 0.0, 1.0)
    avg["aridity_index"] = np.maximum(avg["aridity_index"], 0.0)
    for key in ("browse_forage", "low_forage", "wetland_forage", "reference_population"):
        avg[key] = np.maximum(avg[key], 0.0)
    avg["total_edible_forage"] = avg["browse_forage"] + avg["low_forage"] + avg["wetland_forage"]
    avg["accessible"] = avg["land_support"] > 1e-9
    return avg


def compare_phase_environments(a: Mapping[str, Any], b: Mapping[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    all_exact = True
    global_max = 0.0
    for key in AVERAGED_FIELDS + ("total_edible_forage",):
        aa = np.asarray(a[key], dtype=float); bb = np.asarray(b[key], dtype=float)
        array_equal = bool(np.array_equal(aa, bb))
        diff = np.abs(aa - bb)
        mx = float(np.max(diff)) if diff.size else 0.0
        scale = max(float(np.max(np.abs(aa))) if aa.size else 0.0, float(np.max(np.abs(bb))) if bb.size else 0.0, 1.0)
        roundoff_tol = 32.0 * np.finfo(float).eps * scale
        same = bool(mx <= roundoff_tol)
        all_exact = all_exact and same
        global_max = max(global_max, mx)
        fields[key] = {"array_equal": array_equal, "roundoff_equivalent": same, "roundoff_tolerance": roundoff_tol, "max_abs_error": mx, "mean_abs_error": float(np.mean(diff)) if diff.size else 0.0}
    return {
        "roundoff_equivalent_all_fields": all_exact,
        "global_max_abs_difference": global_max,
        "fields": fields,
        "single_environment_for_two_transport_substeps_is_roundoff_equivalent": all_exact,
    }


def _support_transition(pop: np.ndarray, older_accessible: np.ndarray, younger_accessible: np.ndarray, label: str) -> dict[str, Any]:
    older = np.asarray(older_accessible, bool); younger = np.asarray(younger_accessible, bool)
    if older.shape != younger.shape or np.asarray(pop).shape[1:] != older.shape:
        raise RuntimeError("R3.18 support diagnostic grid mismatch")
    lost = older & ~younger; gained = ~older & younger
    mass = float(np.asarray(pop, float)[:, lost].sum()) if np.any(lost) else 0.0
    return {
        "label": label,
        "lost_accessible_cell_count": int(np.count_nonzero(lost)),
        "gained_accessible_cell_count": int(np.count_nonzero(gained)),
        "population_mass_on_cells_lost_at_boundary": mass,
        "remap_applied": False,
    }


def build_recent_exposure_readiness(parent_state: r38.R38RuntimeState, a1: Mapping[str, Any], c2: Any,
                                    clock: Mapping[str, Any], pending: Mapping[str, Any],
                                    cfg: R318Config | None = None) -> tuple[dict[str, Any], dict[str, dict[str, np.ndarray]]]:
    cfg = cfg or R318Config()
    if abs(float(parent_state.age_ma) - BIOLOGY_STATE_AGE_MA) > 1e-12:
        raise ValueError("R3.18 requires the exact R3.16/R3.17 SEALED 125 ka biology state")
    if abs(float(pending["duration_years"]) - PENDING_R317_YEARS) > 1e-9:
        raise ValueError("R3.18 requires the exact 5 kyr R3.17 pending exposure")
    adapter = D3LateCenozoicSubstrateAdapter(a1, c2)
    if not c2.supports_age(TRANSPORT_BOUNDARY_AGE_MA):
        raise RuntimeError("R3.18 provider does not support exact 62.5 ka transport boundary")
    if not c2.supports_age(PHYSICAL_END_AGE_MA):
        raise RuntimeError("R3.18 provider does not support exact 0 ka endpoint")

    p_recent = recent_partition(clock, PHYSICAL_START_AGE_MA, PHYSICAL_END_AGE_MA, True)
    recent, recent_diag = integrate_partition(adapter, p_recent)
    full = combine_integrals(pending["integrals"], recent)

    p_120_62 = recent_partition(clock, PHYSICAL_START_AGE_MA, TRANSPORT_BOUNDARY_AGE_MA, True)
    i_120_62, d_120_62 = integrate_partition(adapter, p_120_62)
    phase1 = combine_integrals(pending["integrals"], i_120_62)
    p_62_0 = recent_partition(clock, TRANSPORT_BOUNDARY_AGE_MA, PHYSICAL_END_AGE_MA, True)
    phase2, d_62_0 = integrate_partition(adapter, p_62_0)

    # Exact closure: the two transport-phase integrals must sum to the full 125-kyr macro exposure.
    closure: dict[str, float] = {}
    for key in AVERAGED_FIELDS:
        err = np.asarray(full[key]) - (np.asarray(phase1[key]) + np.asarray(phase2[key]))
        closure[key] = float(np.max(np.abs(err))) if err.size else 0.0
    closure_max = max(closure.values(), default=0.0)

    macro_env = effective_environment(full, FULL_MACROSTEP_YEARS)
    phase1_env = effective_environment(phase1, TRANSPORT_CADENCE_YEARS)
    phase2_env = effective_environment(phase2, TRANSPORT_CADENCE_YEARS)
    divergence = compare_phase_environments(phase1_env, phase2_env)

    s125 = adapter.state_at_age(BIOLOGY_STATE_AGE_MA)
    s120 = adapter.state_at_age(PHYSICAL_START_AGE_MA)
    s625 = adapter.state_at_age(TRANSPORT_BOUNDARY_AGE_MA)
    s0 = adapter.state_at_age(PHYSICAL_END_AGE_MA)
    pop = np.asarray(parent_state.pop, float)
    a125 = np.asarray(parent_state.current_accessible, bool)
    support = {
        "125_to_120": _support_transition(pop, a125, np.asarray(s120["accessible"], bool), "125ka_TO_120ka"),
        "120_to_62p5": _support_transition(pop, np.asarray(s120["accessible"], bool), np.asarray(s625["accessible"], bool), "120ka_TO_62p5ka"),
        "62p5_to_0": _support_transition(pop, np.asarray(s625["accessible"], bool), np.asarray(s0["accessible"], bool), "62p5ka_TO_0ka"),
    }
    endpoint_mass_inaccessible = {
        "at_62p5ka": float(pop[:, ~np.asarray(s625["accessible"], bool)].sum()),
        "at_0ka": float(pop[:, ~np.asarray(s0["accessible"], bool)].sum()),
    }

    envelope = {
        "schema": ENVELOPE_SCHEMA,
        "stage": STAGE,
        "physical_start_age_ma": PHYSICAL_START_AGE_MA,
        "physical_end_age_ma": PHYSICAL_END_AGE_MA,
        "biology_state_age_ma": BIOLOGY_STATE_AGE_MA,
        "biology_state_mutated": False,
        "biology_state_relabelled_to_0ka": False,
        "recent_exposure": recent_diag,
        "full_125ka_macrostep": {
            "duration_years": FULL_MACROSTEP_YEARS,
            "r317_pending_years": PENDING_R317_YEARS,
            "r318_recent_years": RECENT_YEARS,
            "integral_phase_closure_max_abs": closure_max,
            "integral_phase_closure_by_field": closure,
        },
        "transport_phases": {
            "boundary_age_ma": TRANSPORT_BOUNDARY_AGE_MA,
            "phase1": {"older_age_ma": BIOLOGY_STATE_AGE_MA, "younger_age_ma": TRANSPORT_BOUNDARY_AGE_MA, "duration_years": TRANSPORT_CADENCE_YEARS, "recent_component": d_120_62},
            "phase2": {"older_age_ma": TRANSPORT_BOUNDARY_AGE_MA, "younger_age_ma": PHYSICAL_END_AGE_MA, "duration_years": TRANSPORT_CADENCE_YEARS, "recent_component": d_62_0},
            "effective_environment_divergence": divergence,
            "phase_aware_transport_operator_required": not bool(divergence["single_environment_for_two_transport_substeps_is_roundoff_equivalent"]),
        },
        "support_diagnostics": support,
        "parent_population_endpoint_inaccessible_mass": endpoint_mass_inaccessible,
        "governance": {
            "biology_advanced": False,
            "transport_advanced": False,
            "gene_flow_advanced": False,
            "lifecycle_gates_advanced": False,
            "biology_cadence_changed": False,
            "transport_cadence_changed": False,
            "adaptive_clock_used_as_biology_timestep": False,
            "support_remap_applied": False,
            "scientific_parameter_changes": False,
            "deep_biological_coupling": False,
            "richness_target_used": False,
            "human_lineage_target_used": False,
            "production_biology_closure_authorized_in_r318": False,
        },
        "next_stage_requirement": (
            "R3.19_MUST_VALIDATE_A_PHASE_AWARE_TRANSPORT_COUPLING_OPERATOR_AGAINST_CONSTANT_FORCING_EQUIVALENCE_"
            "BEFORE_THE_125KA_TO_0KA_BIOLOGY_MACROSTEP_CAN_BE_PROMOTED"
        ),
    }
    integrals = {"recent_120_to_0": recent, "full_125_to_0": full, "transport_phase1_125_to_62p5": phase1, "transport_phase2_62p5_to_0": phase2}
    return envelope, integrals


def save_integral_bundle(integrals: Mapping[str, Mapping[str, np.ndarray]], out_path: Path) -> dict[str, Any]:
    out_path = Path(out_path); out_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, np.ndarray] = {
        "biology_state_age_ma": np.asarray([BIOLOGY_STATE_AGE_MA], float),
        "physical_end_age_ma": np.asarray([PHYSICAL_END_AGE_MA], float),
        "transport_boundary_age_ma": np.asarray([TRANSPORT_BOUNDARY_AGE_MA], float),
    }
    for group, fields in integrals.items():
        for key, value in fields.items():
            payload[f"{group}__{key}"] = np.asarray(value, dtype=float)
    np.savez_compressed(out_path, **payload)
    return {"path": str(out_path), "sha256": _sha256(out_path), "schema": ACCUMULATOR_SCHEMA, "groups": sorted(integrals), "fields": list(AVERAGED_FIELDS)}


def load_integral_bundle(path: Path) -> dict[str, Any]:
    z = np.load(Path(path), allow_pickle=False)
    try:
        groups: dict[str, dict[str, np.ndarray]] = {}
        for key in z.files:
            if "__" not in key:
                continue
            group, field = key.split("__", 1)
            groups.setdefault(group, {})[field] = np.asarray(z[key], dtype=float).copy()
        return {
            "biology_state_age_ma": float(z["biology_state_age_ma"][0]),
            "physical_end_age_ma": float(z["physical_end_age_ma"][0]),
            "transport_boundary_age_ma": float(z["transport_boundary_age_ma"][0]),
            "groups": groups,
        }
    finally:
        z.close()
