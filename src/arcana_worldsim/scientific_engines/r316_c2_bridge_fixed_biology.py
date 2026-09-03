from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping
import json

import numpy as np

from arcana_worldsim.late_cenozoic.late_pleistocene_boundary import IntegratedLateCenozoicProviderC2

from . import r38_restartable_checkpoint as r38
from . import r315_late_cenozoic_secular_biology as r315

STAGE = "v0.6D1-R3.16"
PARENT_STAGE = "v0.6D1-R3.15_SEALED"
START_AGE_MA = 0.25
BIOLOGY_END_AGE_MA = 0.125
C2_BRIDGE_START_AGE_MA = 0.2
C2_BRIDGE_END_AGE_MA = 0.12
BIOLOGY_MACROSTEP_YEARS = 125_000.0
C2_BRIDGE_STEP_YEARS = 500.0
EXPECTED_BIOLOGY_STEPS = 1
EXPECTED_C2_SUBSTEPS_CONSUMED = 150
EXPECTED_C2_SUBSTEPS_TOTAL = 160
EXPECTED_C2_SUBSTEPS_REMAINING = 10
SCHEMA = "ARCANA_R316_125KA_EXPOSURE_PRESERVING_C2_BRIDGE_CHECKPOINT_V1"
SUMMARY_SCHEMA = "ARCANA_R316_C2_BRIDGE_FIXED_BIOLOGY_COUPLING_V1"
VERDICT = "PASS_CANONICAL_R316_250_TO_125KA_H0_C2_EXPOSURE_PRESERVING_FIXED_BIOLOGY__125KA_PRE_120KA_RESTART_CHECKPOINT_READY"

R315_CHECKPOINT_JSON_SHA256 = "4fb4ffdd711b7a5439ffff15a0a6f381e42ca560b00a2338d70edb77d848bcf6"
R315_CHECKPOINT_NPZ_SHA256 = "f8e79ea862de6c48f01784c727ca15abf9d8fd53b07f47d1aaab5bf589ee5692"
R315_SEALED_VERDICT = "PASS_R315_CANONICAL_30MA_TO_250KA_H0_LATE_CENOZOIC_SECULAR_BIOLOGY__250KA_PRE_C2_BRIDGE_RESTART_BOUNDARY_SEALED"
A1_RUNTIME_RELATIVE_PATH = Path("references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz")


def _load_r38_runtime_a1(root: Path):
    """Load the A1 authority in the concrete container contract required by R3.8.

    R3.14 materializes A1 as a plain mapping for provider construction, while
    the sealed R3.8 runtime also inspects ``a1.files`` for optional coordinate
    channels.  R3.16 therefore reopens the *same* NPZ authority for the R3.8
    call rather than coercing the runtime to a new type or weakening R3.8.
    """
    path = Path(root) / A1_RUNTIME_RELATIVE_PATH
    if not path.is_file():
        raise FileNotFoundError(f"R3.16 requires A1 runtime NPZ authority: {path}")
    z = np.load(path, allow_pickle=False)
    if not hasattr(z, "files"):
        raise TypeError("R3.16 A1 runtime authority must preserve the NpzFile .files contract")
    required = {"age_ma", "lat", "lon", "population"}
    missing = sorted(required.difference(set(z.files)))
    if missing:
        z.close()
        raise RuntimeError(f"R3.16 A1 runtime NPZ missing required channels: {missing}")
    return z



class R316C2BridgeEnvironmentAdapter(r315.R315D3EnvironmentAdapter):
    """R3.14 C2 -> D3 substrate adapter scoped to the R3.16 bridge window.

    R3.15 intentionally fail-closes at 250 ka and must remain unchanged.  R3.16
    owns the authority to sample C2 from 250 ka through the exact 120 ka
    environmental restart boundary for exposure integration/diagnostics.  This
    adapter changes only the governance scope; the underlying D3 substrate
    conversion remains the inherited R3.15 implementation.
    """

    def state_at_age(self, age_ma: float) -> dict[str, Any]:
        age = float(age_ma)
        if age < C2_BRIDGE_END_AGE_MA - 1e-12 or age > START_AGE_MA + 1e-12:
            raise ValueError("R3.16 adapter is scoped to 250 ka -> 120 ka only")
        out = dict(self.d3.state_at_age(age))
        out.update({
            "older_ma": age,
            "younger_ma": age,
            "older_index": -1,
            "younger_index": -1,
            "phase": 0.0,
            "topology": "R316_C2_250_120KA_BRIDGE_PROVIDER",
            "paleogeographic_history_provider": "R314_C2_BOUND_LATE_PLEISTOCENE_BRIDGE_PROVIDER",
            "biology_forcing_sample_semantics": "ENVIRONMENT_SAMPLE_FOR_R316_EXPOSURE_QUADRATURE_NOT_A_BIOLOGY_TIMESTEP",
            "adaptive_clock_checkpoint_promoted_to_biology_step": False,
        })
        return out

AVERAGED_FIELDS = (
    "land_support",
    "temperature_c",
    "aridity_index",
    "browse_forage",
    "low_forage",
    "wetland_forage",
    "reference_population",
)


@dataclass(frozen=True)
class R316Config(r38.R38Config):
    end_age_ma: float = BIOLOGY_END_AGE_MA
    bridge_start_age_ma: float = START_AGE_MA
    bridge_biology_end_age_ma: float = BIOLOGY_END_AGE_MA
    c2_bridge_start_age_ma: float = C2_BRIDGE_START_AGE_MA
    c2_bridge_end_age_ma: float = C2_BRIDGE_END_AGE_MA
    biology_cadence_preserved: bool = True
    adaptive_clock_used_as_biology_timestep: bool = False
    environmental_exposure_quadrature: str = "R314_ADAPTIVE_CLOCK_PARTITION_TRAPEZOID_TIME_AVERAGE"
    lifecycle_gate_cadence_changed: bool = False
    gene_flow_step_cadence_changed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if abs(float(self.end_age_ma) - BIOLOGY_END_AGE_MA) > 1e-12:
            raise ValueError("R3.16 canonical biology endpoint is 125 ka")
        if abs(float(self.biology_cadence_years) - BIOLOGY_MACROSTEP_YEARS) > 1e-9:
            raise ValueError("R3.16 preserves the sealed 125 kyr biology cadence")
        if not self.biology_cadence_preserved or self.adaptive_clock_used_as_biology_timestep:
            raise ValueError("R3.16 cannot promote environmental checkpoints to biology timesteps")
        if self.lifecycle_gate_cadence_changed or self.gene_flow_step_cadence_changed:
            raise ValueError("R3.16 cannot alter lifecycle or gene-flow step cadence")


def _sha256(path: Path) -> str:
    h = sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _r315_paths(root: Path) -> dict[str, Path]:
    run = Path(root) / "local_runs/v0_6D1_R3_15"
    return {
        "seal": Path(root) / "R3_15_SEAL_SUMMARY.json",
        "audit": Path(root) / "outputs/v0_6D1_R3_15/FORMAL_AUDIT_SEALED_v0_6D1_R3_15.json",
        "summary": run / "R3_15_LATE_CENOZOIC_SECULAR_BIOLOGY_SUMMARY.json",
        "checkpoint_json": run / "WORLD1_H0_250ka_LATE_CENOZOIC_SECULAR_BIOLOGY_PRE_C2_BRIDGE_CHECKPOINT_v0_6D1_R3_15.json",
        "checkpoint_npz": run / "WORLD1_H0_250ka_LATE_CENOZOIC_SECULAR_BIOLOGY_PRE_C2_BRIDGE_CHECKPOINT_v0_6D1_R3_15.npz",
    }


def validate_parent_r315_authority(root: Path) -> dict[str, Any]:
    root = Path(root)
    p = _r315_paths(root)
    for path in p.values():
        if not path.is_file():
            raise RuntimeError(f"R3.16 requires R3.15 SEALED evidence: missing {path}")
    seal = json.loads(p["seal"].read_text(encoding="utf-8"))
    audit = json.loads(p["audit"].read_text(encoding="utf-8"))
    summary = json.loads(p["summary"].read_text(encoding="utf-8"))
    if seal.get("stage") != "v0.6D1-R3.15" or seal.get("verdict") != R315_SEALED_VERDICT:
        raise RuntimeError("R3.15 seal verdict is not authoritative")
    if audit.get("verdict") != R315_SEALED_VERDICT or audit.get("checks") != "292/292":
        raise RuntimeError("R3.15 sealed audit is not authoritative")
    b = seal.get("boundary", {})
    if abs(float(b.get("age_ma", -1.0)) - START_AGE_MA) > 1e-12:
        raise RuntimeError("R3.15 sealed boundary is not 250 ka")
    if int(b.get("species", -1)) != 134 or int(b.get("components", -1)) != 295:
        raise RuntimeError("R3.15 sealed boundary cardinality mismatch")
    if abs(float(b.get("population", -1.0)) - 1218.3485572325976) > 1e-9:
        raise RuntimeError("R3.15 sealed population mismatch")
    if _sha256(p["checkpoint_json"]) != R315_CHECKPOINT_JSON_SHA256:
        raise RuntimeError("R3.15 checkpoint JSON SHA mismatch")
    if _sha256(p["checkpoint_npz"]) != R315_CHECKPOINT_NPZ_SHA256:
        raise RuntimeError("R3.15 checkpoint NPZ SHA mismatch")
    if seal.get("artifact_hashes", {}).get("checkpoint_json") not in (None, R315_CHECKPOINT_JSON_SHA256):
        raise RuntimeError("R3.15 seal checkpoint JSON hash disagrees with canonical run")
    if seal.get("artifact_hashes", {}).get("checkpoint_npz") not in (None, R315_CHECKPOINT_NPZ_SHA256):
        raise RuntimeError("R3.15 seal checkpoint NPZ hash disagrees with canonical run")
    if summary.get("verdict") != "PASS_CANONICAL_R315_30MA_TO_250KA_H0_LATE_CENOZOIC_SECULAR_BIOLOGY__PRE_C2_200KA_BRIDGE_CHECKPOINT_READY":
        raise RuntimeError("R3.15 canonical summary verdict mismatch")
    st = r315.load_checkpoint(p["checkpoint_json"], smoke=False)
    if abs(float(st.age_ma) - START_AGE_MA) > 1e-12:
        raise RuntimeError("R3.15 checkpoint load did not reproduce 250 ka")
    parent314 = r315.validate_parent_r314_authority(root)
    # R3.14 intentionally returns A1 as a dict for provider construction.
    # R3.8 has an older concrete NPZ container contract (``a1.files``).  Keep
    # both authorities semantically identical by reopening the same SEALED A1
    # file for the runtime boundary instead of changing either parent stage.
    runtime_a1 = _load_r38_runtime_a1(root)
    return {
        "state": st,
        "a1": runtime_a1,
        "c2": parent314["c2"],
        "clock": parent314["clock"],
        "r315_seal_sha256": _sha256(p["seal"]),
        "r315_audit_sha256": _sha256(p["audit"]),
        "r315_summary_sha256": _sha256(p["summary"]),
        "checkpoint_json_sha256": R315_CHECKPOINT_JSON_SHA256,
        "checkpoint_npz_sha256": R315_CHECKPOINT_NPZ_SHA256,
        "r314_seal_verdict": parent314["seal_verdict"],
        "r314_seal_sha256": parent314["seal_sha256"],
        "r314_clock_sha256": parent314["clock_sha256"],
    }


def _unique_desc(values: list[float], tol: float = 1e-13) -> list[float]:
    out: list[float] = []
    for x in sorted((float(v) for v in values), reverse=True):
        if not out or abs(x - out[-1]) > tol:
            out.append(x)
    return out


def exposure_partition(clock: Mapping[str, Any], older_age_ma: float = START_AGE_MA,
                       younger_age_ma: float = BIOLOGY_END_AGE_MA) -> dict[str, Any]:
    older = float(older_age_ma); younger = float(younger_age_ma)
    if not older > younger:
        raise ValueError("exposure partition requires older > younger age")
    ages = [older, younger, C2_BRIDGE_START_AGE_MA]
    ages.extend(float(x) for x in np.asarray(clock["age_ma"], dtype=float)
                if younger - 1e-12 <= float(x) <= older + 1e-12)
    nodes = _unique_desc(ages)
    if abs(nodes[0] - older) > 1e-12 or abs(nodes[-1] - younger) > 1e-12:
        raise RuntimeError("exposure partition lost macrostep endpoints")
    segments = []
    c2_count = 0
    for a, b in zip(nodes[:-1], nodes[1:]):
        dt = (a - b) * 1e6
        if dt <= 0:
            raise RuntimeError("non-positive exposure segment")
        domain = "C2_200_120KA_BRIDGE" if a <= C2_BRIDGE_START_AGE_MA + 1e-12 else "PRE_C2_SECULAR"
        if domain == "C2_200_120KA_BRIDGE":
            c2_count += 1
            if abs(dt - C2_BRIDGE_STEP_YEARS) > 1e-6:
                raise RuntimeError(f"C2 bridge exposure segment is not 500 years: {a}->{b} = {dt}")
        segments.append({"older_age_ma": a, "younger_age_ma": b, "dt_years": dt, "domain": domain})
    total = sum(float(s["dt_years"]) for s in segments)
    if abs(total - BIOLOGY_MACROSTEP_YEARS) > 1e-6:
        raise RuntimeError("R3.16 exposure partition does not close the 125 kyr biology macrostep")
    if c2_count != EXPECTED_C2_SUBSTEPS_CONSUMED:
        raise RuntimeError(f"R3.16 expected {EXPECTED_C2_SUBSTEPS_CONSUMED} C2 500-y segments, found {c2_count}")
    return {
        "older_age_ma": older,
        "younger_age_ma": younger,
        "node_count": len(nodes),
        "segment_count": len(segments),
        "c2_bridge_segment_count": c2_count,
        "total_years": total,
        "nodes_age_ma": nodes,
        "segments": segments,
    }


def remaining_125_to_120_partition(clock: Mapping[str, Any]) -> dict[str, Any]:
    ages = [BIOLOGY_END_AGE_MA, C2_BRIDGE_END_AGE_MA]
    ages.extend(float(x) for x in np.asarray(clock["age_ma"], dtype=float)
                if C2_BRIDGE_END_AGE_MA - 1e-12 <= float(x) <= BIOLOGY_END_AGE_MA + 1e-12)
    nodes = _unique_desc(ages)
    segs = []
    for a, b in zip(nodes[:-1], nodes[1:]):
        dt = (a-b)*1e6
        if abs(dt-C2_BRIDGE_STEP_YEARS) > 1e-6:
            raise RuntimeError("125->120 ka remainder is not represented by 500-y C2 intervals")
        segs.append({"older_age_ma": a, "younger_age_ma": b, "dt_years": dt})
    if len(segs) != EXPECTED_C2_SUBSTEPS_REMAINING:
        raise RuntimeError("R3.16 expected ten 500-y intervals between 125 and 120 ka")
    return {
        "older_age_ma": BIOLOGY_END_AGE_MA,
        "younger_age_ma": C2_BRIDGE_END_AGE_MA,
        "segment_count": len(segs),
        "total_years": sum(x["dt_years"] for x in segs),
        "segments": segs,
        "biology_advanced": False,
        "role": "UNCONSUMED_C2_REMAINDER_FOR_EXACT_120KA_RESTART_STAGE",
    }


def _time_average_on_nodes(adapter: R316C2BridgeEnvironmentAdapter, nodes: list[float]) -> dict[str, Any]:
    nodes = _unique_desc(nodes)
    states = [adapter.state_at_age(age) for age in nodes]
    total = sum((a-b)*1e6 for a,b in zip(nodes[:-1], nodes[1:]))
    if total <= 0:
        raise RuntimeError("R3.16 exposure nodes have zero duration")
    accum: dict[str, np.ndarray] = {}
    for key in AVERAGED_FIELDS:
        accum[key] = np.zeros_like(np.asarray(states[0][key], dtype=float), dtype=float)
    for i, (a_age, b_age) in enumerate(zip(nodes[:-1], nodes[1:])):
        dt = (a_age-b_age)*1e6
        for key in AVERAGED_FIELDS:
            a = np.asarray(states[i][key], dtype=float)
            b = np.asarray(states[i+1][key], dtype=float)
            if a.shape != accum[key].shape or b.shape != accum[key].shape:
                raise RuntimeError(f"R3.16 exposure field shape drift: {key}")
            accum[key] += 0.5*(a+b)*dt
    avg: dict[str, Any] = {}
    for key, integral in accum.items():
        first = np.asarray(states[0][key], dtype=float)
        if all(np.array_equal(first, np.asarray(st[key], dtype=float)) for st in states[1:]):
            avg[key] = first.copy()
        else:
            avg[key] = integral/total
    avg["land_support"] = np.clip(avg["land_support"], 0.0, 1.0)
    avg["aridity_index"] = np.maximum(avg["aridity_index"], 0.0)
    for key in ("browse_forage", "low_forage", "wetland_forage", "reference_population"):
        avg[key] = np.maximum(avg[key], 0.0)
    avg["total_edible_forage"] = avg["browse_forage"] + avg["low_forage"] + avg["wetland_forage"]
    avg["accessible"] = avg["land_support"] > 1e-9
    return avg


def one_level_refined_exposure_environment(adapter: R316C2BridgeEnvironmentAdapter, clock: Mapping[str, Any]) -> dict[str, Any]:
    part = exposure_partition(clock)
    nodes: list[float] = [float(part["nodes_age_ma"][0])]
    for a,b in zip(part["nodes_age_ma"][:-1], part["nodes_age_ma"][1:]):
        nodes.extend([0.5*(float(a)+float(b)), float(b)])
    return _time_average_on_nodes(adapter, nodes)


def compare_effective_environments(a: Mapping[str, Any], b: Mapping[str, Any]) -> dict[str, Any]:
    rows = {}
    max_abs = 0.0
    for key in AVERAGED_FIELDS + ("total_edible_forage",):
        aa=np.asarray(a[key],dtype=float); bb=np.asarray(b[key],dtype=float)
        if aa.shape != bb.shape:
            rows[key]={"shape_match":False,"max_abs_error":float("inf"),"mean_abs_error":float("inf")}
            max_abs=float("inf")
            continue
        d=np.abs(aa-bb)
        row={"shape_match":True,"max_abs_error":float(np.max(d)) if d.size else 0.0,"mean_abs_error":float(np.mean(d)) if d.size else 0.0}
        rows[key]=row; max_abs=max(max_abs,row["max_abs_error"])
    return {"fields":rows,"global_max_abs_error":max_abs,"role":"DIAGNOSTIC_QUADRATURE_REFINEMENT_NOT_A_NEW_AUTHORITY"}


def effective_environment_from_exposure(adapter: R316C2BridgeEnvironmentAdapter, clock: Mapping[str, Any],
                                        older_age_ma: float = START_AGE_MA,
                                        younger_age_ma: float = BIOLOGY_END_AGE_MA) -> tuple[dict[str, Any], dict[str, Any]]:
    part = exposure_partition(clock, older_age_ma, younger_age_ma)
    nodes = part["nodes_age_ma"]
    avg = _time_average_on_nodes(adapter, nodes)
    avg.update({
        "age_ma": float(younger_age_ma),
        "older_ma": float(older_age_ma),
        "younger_ma": float(younger_age_ma),
        "older_index": -1,
        "younger_index": -1,
        "phase": 1.0,
        "topology": "R316_TIME_INTEGRATED_C2_EXPOSURE_SUBSTRATE",
        "paleogeographic_history_provider": "R314_C2_ADAPTIVE_CLOCK_EXPOSURE_INTEGRAL",
        "biology_forcing_sample_semantics": "TIME_WEIGHTED_ENVIRONMENT_EXPOSURE_ON_ONE_FIXED_125KYR_BIOLOGY_MACROSTEP",
        "adaptive_clock_checkpoint_promoted_to_biology_step": False,
        "environmental_substeps_preserved_as_exposure_quadrature": True,
        "gene_flow_step_cadence_changed": False,
        "lifecycle_gate_cadence_changed": False,
    })
    endpoint = adapter.state_at_age(float(younger_age_ma))
    deltas = {}
    for key in AVERAGED_FIELDS + ("total_edible_forage",):
        aa = np.asarray(avg[key], dtype=float); bb = np.asarray(endpoint[key], dtype=float)
        deltas[key] = {
            "max_abs_effective_vs_endpoint": float(np.max(np.abs(aa-bb))) if aa.size else 0.0,
            "mean_abs_effective_vs_endpoint": float(np.mean(np.abs(aa-bb))) if aa.size else 0.0,
        }
    bridge_nodes = [float(x) for x in nodes if BIOLOGY_END_AGE_MA - 1e-12 <= float(x) <= C2_BRIDGE_START_AGE_MA + 1e-12]
    diagnostics = {
        "partition": part,
        "averaging_rule": "TRAPEZOID_TIME_AVERAGE_OVER_R314_ADAPTIVE_CLOCK_PARTITION",
        "c2_bridge_500y_substeps_consumed": part["c2_bridge_segment_count"],
        "c2_bridge_500y_substeps_total": EXPECTED_C2_SUBSTEPS_TOTAL,
        "c2_bridge_500y_substeps_remaining_to_120ka": EXPECTED_C2_SUBSTEPS_REMAINING,
        "bridge_nodes_used": len(bridge_nodes),
        "endpoint_difference": deltas,
        "adaptive_clock_as_biology_timestep": False,
        "biology_macrostep_years": BIOLOGY_MACROSTEP_YEARS,
        "environmental_information_discarded_by_endpoint_only_sampling": any(
            row["max_abs_effective_vs_endpoint"] > 0.0 for row in deltas.values()
        ),
    }
    return avg, diagnostics


@contextmanager
def patched_r38_effective_bridge_environment(effective_env: Mapping[str, Any]):
    original = r38.bp.environment_at
    def environment_at(age_ma: float, a1: Any, cfg: Any) -> dict[str, Any]:
        if abs(float(age_ma) - BIOLOGY_END_AGE_MA) > 1e-12:
            raise RuntimeError("R3.16 effective bridge substrate is authorized only for the 250->125 ka macrostep")
        return {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in effective_env.items()}
    r38.bp.environment_at = environment_at
    try:
        yield
    finally:
        r38.bp.environment_at = original


def run_bridge_macrostep(parent_state: r38.R38RuntimeState, a1: Mapping[str, Any], metadata_rows: list[dict[str, Any]],
                         c2: IntegratedLateCenozoicProviderC2, clock: Mapping[str, Any],
                         cfg: R316Config | None = None):
    cfg = cfg or R316Config()
    if abs(float(parent_state.age_ma) - START_AGE_MA) > 1e-12:
        raise ValueError("R3.16 requires the exact R3.15 250 ka parent state")
    adapter = R316C2BridgeEnvironmentAdapter(a1, c2)
    effective, exposure = effective_environment_from_exposure(adapter, clock)
    st = r315.r313.r312.r311._clone_state(parent_state)
    with patched_r38_effective_bridge_environment(effective):
        out, records = r38.advance_state(st, a1, metadata_rows, cfg, BIOLOGY_END_AGE_MA)
    if len(records) != EXPECTED_BIOLOGY_STEPS:
        raise RuntimeError("R3.16 must execute exactly one fixed 125 kyr biology macrostep")
    remainder = remaining_125_to_120_partition(clock)
    endpoint120 = adapter.state_at_age(C2_BRIDGE_END_AGE_MA)
    exposure["remainder_125_to_120ka"] = remainder
    exposure["exact_120ka_environment_endpoint"] = {
        "provider": endpoint120.get("provider"),
        "subprovider": endpoint120.get("subprovider"),
        "authority": endpoint120.get("authority"),
        "replay_safe_boundary_continuation": bool(endpoint120.get("replay_safe_boundary_continuation", False)),
        "biology_advanced_to_120ka": False,
    }
    return out, records, exposure, effective


def event_counts(st):
    return r315.event_counts(st)


def delta_event_counts(before, after):
    return r315.delta_event_counts(before, after)


def invariant_report(st, metadata_rows, cfg):
    return r315.invariant_report(st, metadata_rows, cfg)


def species_counts_by_guild(st):
    return r315.species_counts_by_guild(st)


def _save_state_arrays(st: r38.R38RuntimeState, npz_path: Path) -> None:
    r315._save_state_arrays(st, npz_path)


def save_checkpoint(st: r38.R38RuntimeState, out_dir: Path, parent_authority: Mapping[str, Any], cfg: R316Config,
                    run_report: Mapping[str, Any]) -> dict[str, Any]:
    if abs(float(st.age_ma) - BIOLOGY_END_AGE_MA) > 1e-12:
        raise ValueError("R3.16 canonical checkpoint must be exactly 125 ka")
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    stem = "WORLD1_H0_125ka_C2_EXPOSURE_PRESERVING_FIXED_BIOLOGY_PRE_120KA_RESTART_CHECKPOINT_v0_6D1_R3_16"
    jp = out_dir / f"{stem}.json"; npzp = out_dir / f"{stem}.npz"
    _save_state_arrays(st, npzp)
    meta = {
        "schema": SCHEMA, "stage": STAGE, "parent_stage": PARENT_STAGE,
        "age_ma": float(st.age_ma), "elapsed_year": float(st.elapsed_year),
        "event_side": "C2_BRIDGE_EXPOSURE_PRESERVED__125KA_FIXED_BIOLOGY_BOUNDARY__PRE_120KA_RESTART",
        "parent_r315_authority": dict(parent_authority),
        "component_ids": st.component_ids, "root_species": st.root_species, "current_species": st.current_species,
        "registry": st.registry, "child_counters": st.child_counters, "baselines": st.baselines,
        "ri_state": r38._pair_dict_rows(st.ri_state), "clock_state": r38._pair_dict_rows(st.clock_state),
        "ext_state": st.ext_state, "founder_state": st.founder_state, "vicariance_state": st.vicariance_state,
        "reconnection_state": r38._pair_dict_rows(st.reconnection_state), "events": r38._jsonable(st.events),
        "snapshots": r38._jsonable(st.snapshots), "founder_stats_last": r38._jsonable(st.founder_stats_last),
        "gene_flow_closure": r38._jsonable(st.gene_flow_closure), "topology_remap_mass": st.topology_remap_mass,
        "initial_total_population": st.initial_total_population, "config": asdict(cfg), "run_report": run_report,
        "npz_file": npzp.name,
        "governance": {
            "biology_cadence_years": BIOLOGY_MACROSTEP_YEARS,
            "biology_steps": 1,
            "adaptive_clock_used_as_biology_timestep": False,
            "environmental_substeps_preserved_as_exposure_quadrature": True,
            "c2_500y_substeps_consumed": EXPECTED_C2_SUBSTEPS_CONSUMED,
            "c2_500y_substeps_remaining_to_120ka": EXPECTED_C2_SUBSTEPS_REMAINING,
            "gene_flow_step_cadence_changed": False,
            "lifecycle_gate_cadence_changed": False,
            "biology_advanced_to_120ka": False,
            "deep_biological_coupling": False,
            "scientific_parameters_changed": False,
        },
    }
    jp.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {"json": str(jp), "npz": str(npzp), "json_sha256": _sha256(jp), "npz_sha256": _sha256(npzp)}


def load_checkpoint(json_path: Path) -> r38.R38RuntimeState:
    jp = Path(json_path); m = json.loads(jp.read_text(encoding="utf-8"))
    if m.get("schema") != SCHEMA or m.get("stage") != STAGE:
        raise RuntimeError("R3.16 checkpoint metadata mismatch")
    if abs(float(m.get("age_ma", -1.0)) - BIOLOGY_END_AGE_MA) > 1e-12:
        raise RuntimeError("R3.16 checkpoint is not 125 ka")
    z = np.load(jp.parent / m["npz_file"], allow_pickle=False)
    st = r38.R38RuntimeState(
        age_ma=float(m["age_ma"]), elapsed_year=float(m["elapsed_year"]), component_ids=list(m["component_ids"]),
        root_species=list(m["root_species"]), current_species=list(m["current_species"]), guild=z["guild"].astype(np.uint8),
        pop=z["population"].astype(float), trait=z["trait"].astype(float), va=z["va"].astype(float), gen=z["generation_time"].astype(float),
        registry={str(k): dict(v) for k, v in m["registry"].items()}, child_counters={str(k): int(v) for k, v in m["child_counters"].items()},
        current_accessible=z["current_accessible"].astype(bool), baselines=m["baselines"],
        ri_state={k: float(v) for k, v in r38._pair_dict_from_rows(m["ri_state"]).items()},
        clock_state={k: float(v) for k, v in r38._pair_dict_from_rows(m["clock_state"]).items()},
        ext_state=m["ext_state"], founder_state=m["founder_state"], vicariance_state=m["vicariance_state"],
        reconnection_state={k: dict(v) for k, v in r38._pair_dict_from_rows(m["reconnection_state"]).items()},
        events=list(m["events"]), snapshots=list(m["snapshots"]), founder_stats_last=list(m["founder_stats_last"]),
        gene_flow_closure=dict(m["gene_flow_closure"]), topology_remap_mass=float(m["topology_remap_mass"]),
        initial_total_population=float(m["initial_total_population"]),
        reduced_state=r38.ReducedGeneticLifecycleState(
            z["reduced_va_within"].astype(float), z["reduced_ancestry_covariance"].astype(float),
            z["reduced_neutral_segregation_potential"].astype(float), z["reduced_adaptive_coordinate"].astype(float),
        ),
    )
    st._lat = z["lat"].astype(float); st._lon = z["lon"].astype(float)
    return st
