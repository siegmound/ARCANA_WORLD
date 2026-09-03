from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping
import json
import numpy as np

from . import r38_restartable_checkpoint as r38
from . import r316_c2_bridge_fixed_biology as r316

STAGE = "v0.6D1-R3.17"
PARENT_STAGE = "v0.6D1-R3.16"
START_PHYSICAL_AGE_MA = 0.125
RESTART_PHYSICAL_AGE_MA = 0.120
PENDING_YEARS = 5_000.0
SEALED_BIOLOGY_CADENCE_YEARS = 125_000.0
SEALED_TRANSPORT_CADENCE_YEARS = 62_500.0
SEALED_LIFECYCLE_CHECK_YEARS = 500_000.0
NEXT_FULL_BIOLOGY_BOUNDARY_AGE_MA = 0.0
NEXT_TRANSPORT_BOUNDARY_AGE_MA = 0.0625
EXPECTED_C2_SUBSTEPS = 10
C2_STEP_YEARS = 500.0
R316_SEALED_VERDICT = (
    "PASS_R316_CANONICAL_250_TO_125KA_H0_C2_EXPOSURE_PRESERVING_FIXED_BIOLOGY__"
    "125KA_PRE_120KA_RESTART_BOUNDARY_SEALED"
)
R316_READY_VERDICT = (
    "PASS_CANONICAL_R316_250_TO_125KA_H0_C2_EXPOSURE_PRESERVING_FIXED_BIOLOGY__"
    "125KA_PRE_120KA_RESTART_CHECKPOINT_READY"
)
R316_CHECKPOINT_JSON_SHA256 = "aaf0bab510b4bcb5fbf77707ad66201515342cf8eb25b687e8f15952d2afca32"
R316_CHECKPOINT_NPZ_SHA256 = "de0ef549d2fc74f1546e320b3fc3e0bc2f7ca7cbf5ebac464976494ad4055593"
VERDICT = (
    "PASS_R317_EXACT_120KA_ENVIRONMENTAL_RESTART__"
    "R316_125KA_BIOLOGY_PRESERVED_WITH_5KYR_PENDING_EXPOSURE"
)
ENVELOPE_SCHEMA = "ARCANA_R317_120KA_DUAL_CLOCK_RESTART_ENVELOPE_V1"
ACCUMULATOR_SCHEMA = "ARCANA_R317_PENDING_125_TO_120KA_EXPOSURE_ACCUMULATOR_V1"
SUMMARY_SCHEMA = "ARCANA_R317_EXACT_120KA_ENVIRONMENTAL_RESTART_SUMMARY_V1"


@dataclass(frozen=True)
class R317Config:
    start_physical_age_ma: float = START_PHYSICAL_AGE_MA
    restart_physical_age_ma: float = RESTART_PHYSICAL_AGE_MA
    biology_state_age_ma: float = START_PHYSICAL_AGE_MA
    biology_cadence_years: float = SEALED_BIOLOGY_CADENCE_YEARS
    transport_cadence_years: float = SEALED_TRANSPORT_CADENCE_YEARS
    lifecycle_check_interval_years: float = SEALED_LIFECYCLE_CHECK_YEARS
    advance_biology: bool = False
    advance_transport: bool = False
    advance_gene_flow: bool = False
    advance_lifecycle_gates: bool = False
    advance_pair_clocks: bool = False
    advance_demography: bool = False
    advance_selection: bool = False
    advance_variance: bool = False
    deep_biological_coupling: bool = False

    def __post_init__(self) -> None:
        if abs(self.start_physical_age_ma - START_PHYSICAL_AGE_MA) > 1e-12:
            raise ValueError("R3.17 starts at the SEALED R3.16 125 ka boundary")
        if abs(self.restart_physical_age_ma - RESTART_PHYSICAL_AGE_MA) > 1e-12:
            raise ValueError("R3.17 exact environmental restart is 120 ka")
        if abs(self.biology_state_age_ma - START_PHYSICAL_AGE_MA) > 1e-12:
            raise ValueError("R3.17 cannot relabel the 125 ka biology state as 120 ka")
        if abs(self.biology_cadence_years - SEALED_BIOLOGY_CADENCE_YEARS) > 1e-9:
            raise ValueError("R3.17 preserves the SEALED 125 kyr biology cadence")
        if abs(self.transport_cadence_years - SEALED_TRANSPORT_CADENCE_YEARS) > 1e-9:
            raise ValueError("R3.17 preserves the SEALED 62.5 kyr transport cadence")
        forbidden = (
            self.advance_biology, self.advance_transport, self.advance_gene_flow,
            self.advance_lifecycle_gates, self.advance_pair_clocks,
            self.advance_demography, self.advance_selection, self.advance_variance,
            self.deep_biological_coupling,
        )
        if any(forbidden):
            raise ValueError("R3.17 is an environmental restart/deferred-biology synchronization stage")


def _sha256(path: Path) -> str:
    h = sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _r316_paths(root: Path) -> dict[str, Path]:
    run = Path(root) / "local_runs/v0_6D1_R3_16"
    return {
        "seal": Path(root) / "R3_16_SEAL_SUMMARY.json",
        "audit": Path(root) / "outputs/v0_6D1_R3_16/FORMAL_AUDIT_SEALED_v0_6D1_R3_16.json",
        "summary": run / "R3_16_C2_BRIDGE_FIXED_BIOLOGY_SUMMARY.json",
        "checkpoint_json": run / "WORLD1_H0_125ka_C2_EXPOSURE_PRESERVING_FIXED_BIOLOGY_PRE_120KA_RESTART_CHECKPOINT_v0_6D1_R3_16.json",
        "checkpoint_npz": run / "WORLD1_H0_125ka_C2_EXPOSURE_PRESERVING_FIXED_BIOLOGY_PRE_120KA_RESTART_CHECKPOINT_v0_6D1_R3_16.npz",
    }


def validate_parent_r316_authority(root: Path) -> dict[str, Any]:
    root = Path(root)
    p = _r316_paths(root)
    for path in p.values():
        if not path.is_file():
            raise RuntimeError(f"R3.17 requires R3.16 SEALED evidence: missing {path}")
    seal = json.loads(p["seal"].read_text(encoding="utf-8"))
    audit = json.loads(p["audit"].read_text(encoding="utf-8"))
    summary = json.loads(p["summary"].read_text(encoding="utf-8"))
    if seal.get("stage") != PARENT_STAGE or seal.get("verdict") != R316_SEALED_VERDICT:
        raise RuntimeError("R3.16 seal verdict is not authoritative")
    if audit.get("verdict") != R316_SEALED_VERDICT or audit.get("checks") != "193/193":
        raise RuntimeError("R3.16 sealed audit is not authoritative")
    if summary.get("verdict") != R316_READY_VERDICT:
        raise RuntimeError("R3.16 canonical summary verdict mismatch")
    b = seal.get("boundary", {})
    if abs(float(b.get("age_ma", -1.0)) - START_PHYSICAL_AGE_MA) > 1e-12:
        raise RuntimeError("R3.16 sealed boundary is not 125 ka")
    if int(b.get("species", -1)) != 134 or int(b.get("components", -1)) != 295:
        raise RuntimeError("R3.16 sealed boundary cardinality mismatch")
    if _sha256(p["checkpoint_json"]) != R316_CHECKPOINT_JSON_SHA256:
        raise RuntimeError("R3.16 checkpoint JSON SHA mismatch")
    if _sha256(p["checkpoint_npz"]) != R316_CHECKPOINT_NPZ_SHA256:
        raise RuntimeError("R3.16 checkpoint NPZ SHA mismatch")
    st = r316.load_checkpoint(p["checkpoint_json"])
    if abs(float(st.age_ma) - START_PHYSICAL_AGE_MA) > 1e-12:
        raise RuntimeError("R3.16 checkpoint does not reproduce 125 ka")
    # Reuse the already-governed R3.14 provider/clock chain through R3.16's parent validation.
    p315 = r316.validate_parent_r315_authority(root)
    return {
        "state": st,
        "a1": p315["a1"],
        "c2": p315["c2"],
        "clock": p315["clock"],
        "r316_seal_sha256": _sha256(p["seal"]),
        "r316_audit_sha256": _sha256(p["audit"]),
        "r316_summary_sha256": _sha256(p["summary"]),
        "checkpoint_json_sha256": R316_CHECKPOINT_JSON_SHA256,
        "checkpoint_npz_sha256": R316_CHECKPOINT_NPZ_SHA256,
        "r315_seal_sha256": p315["r315_seal_sha256"],
        "r314_seal_sha256": p315["r314_seal_sha256"],
        "r314_clock_sha256": p315["r314_clock_sha256"],
    }


def restart_partition(clock: Mapping[str, Any]) -> dict[str, Any]:
    part = r316.remaining_125_to_120_partition(clock)
    if part["segment_count"] != EXPECTED_C2_SUBSTEPS:
        raise RuntimeError("R3.17 requires exactly ten C2 500-y intervals")
    if abs(float(part["total_years"]) - PENDING_YEARS) > 1e-6:
        raise RuntimeError("R3.17 125->120 ka interval does not close to 5 kyr")
    return part


def _nodes_from_partition(part: Mapping[str, Any]) -> list[float]:
    segs = list(part["segments"])
    if not segs:
        raise RuntimeError("R3.17 restart partition is empty")
    nodes = [float(segs[0]["older_age_ma"])] + [float(s["younger_age_ma"]) for s in segs]
    if abs(nodes[0] - START_PHYSICAL_AGE_MA) > 1e-12 or abs(nodes[-1] - RESTART_PHYSICAL_AGE_MA) > 1e-12:
        raise RuntimeError("R3.17 restart partition lost exact endpoints")
    return nodes


def build_pending_exposure_accumulator(adapter: r316.R316C2BridgeEnvironmentAdapter,
                                       clock: Mapping[str, Any]) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    part = restart_partition(clock)
    nodes = _nodes_from_partition(part)
    states = [adapter.state_at_age(age) for age in nodes]
    accum: dict[str, np.ndarray] = {}
    for key in r316.AVERAGED_FIELDS:
        accum[key] = np.zeros_like(np.asarray(states[0][key], dtype=float), dtype=float)
    for i, seg in enumerate(part["segments"]):
        dt = float(seg["dt_years"])
        if abs(dt - C2_STEP_YEARS) > 1e-6:
            raise RuntimeError("R3.17 exposure interval is not exactly 500 years")
        for key in r316.AVERAGED_FIELDS:
            a = np.asarray(states[i][key], dtype=float)
            b = np.asarray(states[i + 1][key], dtype=float)
            if a.shape != b.shape or a.shape != accum[key].shape:
                raise RuntimeError(f"R3.17 exposure field shape drift: {key}")
            accum[key] += 0.5 * (a + b) * dt
    avg = {k: v / PENDING_YEARS for k, v in accum.items()}
    avg_total = avg["browse_forage"] + avg["low_forage"] + avg["wetland_forage"]
    endpoint = states[-1]
    endpoint_total = np.asarray(endpoint["browse_forage"], float) + np.asarray(endpoint["low_forage"], float) + np.asarray(endpoint["wetland_forage"], float)
    diagnostics = {
        "older_age_ma": START_PHYSICAL_AGE_MA,
        "younger_age_ma": RESTART_PHYSICAL_AGE_MA,
        "duration_years": PENDING_YEARS,
        "segment_count": len(part["segments"]),
        "node_count": len(nodes),
        "all_segments_500y": all(abs(float(s["dt_years"]) - C2_STEP_YEARS) <= 1e-6 for s in part["segments"]),
        "nodes_age_ma": nodes,
        "averaging_rule": "TRAPEZOID_INTEGRAL_ON_R314_C2_500Y_PARTITION",
        "accumulator_role": "PENDING_FIRST_5KYR_OF_THE_125KA_TO_0KA_SEALED_BIOLOGY_MACROSTEP",
        "biological_state_mutated": False,
        "total_forage_average_closure_max_abs": float(np.max(np.abs(avg_total - (accum["browse_forage"] + accum["low_forage"] + accum["wetland_forage"]) / PENDING_YEARS))),
        "endpoint_total_forage_closure_max_abs": float(np.max(np.abs(endpoint_total - np.asarray(endpoint["total_edible_forage"], float)))),
    }
    return accum, diagnostics


def biology_phase_report() -> dict[str, Any]:
    return {
        "physical_age_ma": RESTART_PHYSICAL_AGE_MA,
        "biology_state_age_ma": START_PHYSICAL_AGE_MA,
        "elapsed_since_last_full_biology_boundary_years": PENDING_YEARS,
        "remaining_to_next_full_biology_boundary_years": SEALED_BIOLOGY_CADENCE_YEARS - PENDING_YEARS,
        "next_full_biology_boundary_age_ma": NEXT_FULL_BIOLOGY_BOUNDARY_AGE_MA,
        "elapsed_since_last_transport_boundary_years": PENDING_YEARS,
        "remaining_to_next_transport_boundary_years": SEALED_TRANSPORT_CADENCE_YEARS - PENDING_YEARS,
        "next_transport_boundary_age_ma": NEXT_TRANSPORT_BOUNDARY_AGE_MA,
        "gene_flow_due_at_120ka": False,
        "transport_due_at_120ka": False,
        "lifecycle_gate_due_at_120ka": False,
        "speciation_gate_due_at_120ka": False,
        "extinction_gate_due_at_120ka": False,
        "pair_clock_advanced_to_120ka": False,
        "demography_advanced_to_120ka": False,
        "selection_advanced_to_120ka": False,
        "variance_advanced_to_120ka": False,
        "semantics": "DUAL_CLOCK_RESTART_ENVIRONMENT_AT_120KA_WITH_SEALED_BIOLOGY_STATE_CARRIED_FROM_125KA",
    }


def state_identity_report(before: r38.R38RuntimeState, after: r38.R38RuntimeState) -> dict[str, Any]:
    cmp = r38.compare_runtime_states(before, after, atol=0.0)
    return {
        "equivalent": bool(cmp.get("equivalent", False)),
        "comparison": cmp,
        "biology_state_age_ma": float(after.age_ma),
        "physical_restart_age_ma": RESTART_PHYSICAL_AGE_MA,
    }


def build_restart_envelope(parent_state: r38.R38RuntimeState, a1: Mapping[str, Any], c2: Any,
                           clock: Mapping[str, Any], cfg: R317Config | None = None) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    cfg = cfg or R317Config()
    if abs(float(parent_state.age_ma) - START_PHYSICAL_AGE_MA) > 1e-12:
        raise ValueError("R3.17 requires the exact R3.16 125 ka biology state")
    adapter = r316.R316C2BridgeEnvironmentAdapter(a1, c2)
    accum, exposure_diag = build_pending_exposure_accumulator(adapter, clock)
    endpoint125 = adapter.state_at_age(START_PHYSICAL_AGE_MA)
    endpoint120 = adapter.state_at_age(RESTART_PHYSICAL_AGE_MA)
    if not bool(endpoint120.get("replay_safe_boundary_continuation", False)):
        raise RuntimeError("R3.17 exact 120 ka provider endpoint is not replay-safe")
    # Provider C2 hands off to the recent SEALED stack exactly at 120 ka.
    if not bool(endpoint120.get("restart_boundary_at_120ka", False)):
        raise RuntimeError("R3.17 provider did not expose the governed exact 120 ka restart boundary")
    p125 = np.asarray(parent_state.pop, dtype=float)
    acc125 = np.asarray(endpoint125["accessible"], dtype=bool)
    acc120 = np.asarray(endpoint120["accessible"], dtype=bool)
    if p125.shape[1:] != acc120.shape:
        raise RuntimeError("R3.17 population/environment grid shape mismatch")
    lost = acc125 & ~acc120
    gained = ~acc125 & acc120
    lost_mass = float(p125[:, lost].sum()) if np.any(lost) else 0.0
    # The biology state itself is deliberately not cloned/mutated: its exact parent
    # checkpoint remains the restart authority.  The envelope carries only timing
    # and environmental exposure necessary to continue the *same* 125 kyr step.
    phase = biology_phase_report()
    envelope = {
        "schema": ENVELOPE_SCHEMA,
        "stage": STAGE,
        "physical_restart_age_ma": RESTART_PHYSICAL_AGE_MA,
        "biology_state_age_ma": START_PHYSICAL_AGE_MA,
        "biology_state_source": "R3.16_SEALED_125KA_CHECKPOINT_UNMODIFIED",
        "biology_state_mutated": False,
        "biology_state_relabelled_to_120ka": False,
        "phase": phase,
        "environmental_restart": {
            "provider": endpoint120.get("provider"),
            "subprovider": endpoint120.get("subprovider"),
            "authority": endpoint120.get("authority"),
            "restart_boundary_at_120ka": bool(endpoint120.get("restart_boundary_at_120ka", False)),
            "replay_safe_boundary_continuation": bool(endpoint120.get("replay_safe_boundary_continuation", False)),
            "pre_120ka_historical_glacial_chronology_claimed": bool(endpoint120.get("pre120ka_historical_glacial_chronology_claimed", endpoint120.get("pre_120ka_eustatic_chronology_claimed", False))),
        },
        "pending_exposure": exposure_diag,
        "support_transition_diagnostic": {
            "lost_accessible_cell_count_125_to_120": int(np.count_nonzero(lost)),
            "gained_accessible_cell_count_125_to_120": int(np.count_nonzero(gained)),
            "parent_population_mass_on_cells_inaccessible_at_120ka": lost_mass,
            "support_reconciliation_applied_in_r317": False,
            "role": "DIAGNOSTIC_ONLY__R317_DOES_NOT_INSERT_A_SUBCADENCE_TRANSPORT_OR_REMAP_OPERATOR",
        },
        "governance": {
            "biology_cadence_changed": False,
            "transport_cadence_changed": False,
            "gene_flow_step_cadence_changed": False,
            "lifecycle_gate_cadence_changed": False,
            "partial_biology_step_executed": False,
            "adaptive_clock_used_as_biology_timestep": False,
            "environmental_exposure_accumulated_without_biology_update": True,
            "deep_biological_coupling": False,
            "scientific_parameter_changes": False,
            "richness_target_used": False,
            "human_lineage_target_used": False,
        },
    }
    return envelope, accum


def save_accumulator(accum: Mapping[str, np.ndarray], out_path: Path) -> dict[str, Any]:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {f"integral__{k}": np.asarray(v, dtype=float) for k, v in accum.items()}
    payload["duration_years"] = np.asarray([PENDING_YEARS], dtype=float)
    payload["older_age_ma"] = np.asarray([START_PHYSICAL_AGE_MA], dtype=float)
    payload["younger_age_ma"] = np.asarray([RESTART_PHYSICAL_AGE_MA], dtype=float)
    np.savez_compressed(out_path, **payload)
    return {
        "path": str(out_path),
        "sha256": _sha256(out_path),
        "schema": ACCUMULATOR_SCHEMA,
        "duration_years": PENDING_YEARS,
        "fields": sorted(accum),
    }


def load_accumulator(path: Path) -> dict[str, Any]:
    z = np.load(Path(path), allow_pickle=False)
    try:
        out = {
            "duration_years": float(np.asarray(z["duration_years"])[0]),
            "older_age_ma": float(np.asarray(z["older_age_ma"])[0]),
            "younger_age_ma": float(np.asarray(z["younger_age_ma"])[0]),
            "integrals": {k[len("integral__"):]: np.asarray(z[k], dtype=float).copy() for k in z.files if k.startswith("integral__")},
        }
    finally:
        z.close()
    return out
