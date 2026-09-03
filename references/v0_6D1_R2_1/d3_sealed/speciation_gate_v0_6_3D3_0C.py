from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json, math
import numpy as np


@dataclass(frozen=True)
class SpeciationGateConfig:
    gene_flow_contact_ceiling: float = 0.15
    trait_drive_onset: float = 0.50
    trait_drive_saturation: float = 1.50
    ri_build_rate_per_generation: float = 2.0e-5
    ri_decay_rate_per_generation: float = 5.0e-5
    isolation_reconnection_erosion: float = 1.0
    minimum_effective_isolation_generations: float = 50_000.0
    minimum_intrinsic_RI: float = 0.65
    minimum_trait_distance: float = 1.00
    maximum_effective_exchange_pressure: float = 0.25
    minimum_branch_population_fraction: float = 0.05
    minimum_complement_population_fraction: float = 0.05
    minimum_absolute_population: float = 0.01


def _read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def contact_connectivity_from_d30b_gene_flow(gene_flow: float, ceiling: float = 0.15) -> float:
    """Recover D3.0B's dt-independent spatial contact kernel.

    D3.0B used G = ceiling * overlap * exp(-d/(4 Ldisp)).  G itself was a
    coupling coefficient applied per numerical step and is therefore not promoted
    as biological gene flow.  Dividing by the fixed ceiling recovers only the
    dimensionless contact/connectivity term in [0,1].
    """
    return float(np.clip(gene_flow / max(ceiling, 1e-15), 0.0, 1.0))


def effective_exchange_pressure(contact_connectivity: float, intrinsic_ri: float) -> float:
    return float(np.clip(contact_connectivity, 0.0, 1.0) * (1.0 - np.clip(intrinsic_ri, 0.0, 1.0)))


def ecological_isolation_drive(trait_distance: float, cfg: SpeciationGateConfig) -> float:
    den = max(cfg.trait_drive_saturation - cfg.trait_drive_onset, 1e-15)
    return float(np.clip((trait_distance - cfg.trait_drive_onset) / den, 0.0, 1.0))


def advance_pair_state(
    intrinsic_ri: float,
    isolation_clock_generations: float,
    delta_generations: float,
    contact_connectivity: float,
    trait_distance: float,
    cfg: SpeciationGateConfig | None = None,
):
    """Advance intrinsic RI + biological isolation clock.

    RI follows dR/dg = a(1-R)-bR and is integrated analytically for fixed input
    during the interval.  This makes RI evolution insensitive to solver frame
    count.  The isolation clock is expressed directly in effective generations;
    contact erodes it, while strong RI suppresses effective exchange and allows
    isolation to remain persistent even after secondary contact.
    """
    cfg = cfg or SpeciationGateConfig()
    dg = max(float(delta_generations), 0.0)
    p = float(np.clip(contact_connectivity, 0.0, 1.0))
    r0 = float(np.clip(intrinsic_ri, 0.0, 1.0))
    drive = ecological_isolation_drive(trait_distance, cfg)
    e0 = effective_exchange_pressure(p, r0)
    a = cfg.ri_build_rate_per_generation * drive * (1.0 - e0)
    b = cfg.ri_decay_rate_per_generation * e0
    if a + b > 0.0 and dg > 0.0:
        req = a / (a + b)
        r1 = req + (r0 - req) * math.exp(-(a + b) * dg)
    else:
        r1 = r0
    r1 = float(np.clip(r1, 0.0, 1.0))
    e1 = effective_exchange_pressure(p, r1)
    emid = 0.5 * (e0 + e1)
    isolation_gain = (1.0 - emid) ** 2
    reconnect_loss = cfg.isolation_reconnection_erosion * emid
    clock = max(0.0, float(isolation_clock_generations) + (isolation_gain - reconnect_loss) * dg)
    return {
        "intrinsic_RI": r1,
        "effective_exchange_pressure": e1,
        "isolation_clock_generations": float(clock),
        "ecological_isolation_drive": drive,
    }


def evaluate_pair_gate(
    *, isolation_clock_generations: float, intrinsic_ri: float,
    trait_distance: float, contact_connectivity: float,
    branch_population: float, complement_population: float,
    species_population: float, cfg: SpeciationGateConfig | None = None,
):
    cfg = cfg or SpeciationGateConfig()
    e = effective_exchange_pressure(contact_connectivity, intrinsic_ri)
    species_population = max(float(species_population), 1e-15)
    branch_fraction = float(branch_population) / species_population
    comp_fraction = float(complement_population) / species_population
    checks = {
        "biological_time": float(isolation_clock_generations) >= cfg.minimum_effective_isolation_generations,
        "intrinsic_RI": float(intrinsic_ri) >= cfg.minimum_intrinsic_RI,
        "trait_distance": float(trait_distance) >= cfg.minimum_trait_distance,
        "effective_exchange": e <= cfg.maximum_effective_exchange_pressure,
        "branch_viability": (float(branch_population) >= cfg.minimum_absolute_population and
                             branch_fraction >= cfg.minimum_branch_population_fraction),
        "complement_viability": (float(complement_population) >= cfg.minimum_absolute_population and
                                 comp_fraction >= cfg.minimum_complement_population_fraction),
    }
    return {
        "gate_ready": bool(all(checks.values())),
        "checks": checks,
        "effective_exchange_pressure": e,
        "branch_population_fraction": branch_fraction,
        "complement_population_fraction": comp_fraction,
    }



def evaluate_branch_gate(*, cross_pair_states: list[dict], branch_population: float,
                         complement_population: float, species_population: float,
                         cfg: SpeciationGateConfig | None = None):
    """Conservative component-level gate for a future lineage split."""
    cfg = cfg or SpeciationGateConfig()
    if not cross_pair_states:
        return {"gate_ready": False, "reason": "NO_CROSS_PAIR_EVIDENCE", "checks": {}}
    pair_checks = []
    for x in cross_pair_states:
        pair_checks.append(evaluate_pair_gate(
            isolation_clock_generations=float(x["isolation_clock_generations"]),
            intrinsic_ri=float(x["intrinsic_RI"]),
            trait_distance=float(x["trait_distance"]),
            contact_connectivity=float(x["contact_connectivity"]),
            branch_population=branch_population, complement_population=complement_population,
            species_population=species_population, cfg=cfg))
    structural = {
        "all_cross_pairs_biological_time": all(x["checks"]["biological_time"] for x in pair_checks),
        "all_cross_pairs_intrinsic_RI": all(x["checks"]["intrinsic_RI"] for x in pair_checks),
        "all_cross_pairs_trait_distance": all(x["checks"]["trait_distance"] for x in pair_checks),
        "all_cross_pairs_effective_exchange": all(x["checks"]["effective_exchange"] for x in pair_checks),
        "branch_viability": pair_checks[0]["checks"]["branch_viability"],
        "complement_viability": pair_checks[0]["checks"]["complement_viability"],
    }
    return {
        "gate_ready": bool(all(structural.values())),
        "checks": structural,
        "cross_pair_count": len(cross_pair_states),
        "max_effective_exchange_pressure": max(x["effective_exchange_pressure"] for x in pair_checks),
        "min_intrinsic_RI": min(float(x["intrinsic_RI"]) for x in cross_pair_states),
        "min_isolation_clock_generations": min(float(x["isolation_clock_generations"]) for x in cross_pair_states),
        "min_trait_distance": min(float(x["trait_distance"]) for x in cross_pair_states),
    }

def simulate_calibration_scenario(phases, cfg: SpeciationGateConfig | None = None,
                                  step_generations: float = 100.0,
                                  initial_ri: float = 0.0, initial_clock: float = 0.0):
    cfg = cfg or SpeciationGateConfig()
    ri, clock = float(initial_ri), float(initial_clock)
    last_p = 0.0
    last_td = 0.0
    for phase in phases:
        total = float(phase["generations"])
        last_p = float(phase["contact_connectivity"])
        last_td = float(phase["trait_distance"])
        n = max(1, int(math.ceil(total / max(step_generations, 1e-12))))
        dg = total / n
        for _ in range(n):
            state = advance_pair_state(ri, clock, dg, last_p, last_td, cfg)
            ri = state["intrinsic_RI"]
            clock = state["isolation_clock_generations"]
    return {
        "intrinsic_RI": ri,
        "isolation_clock_generations": clock,
        "contact_connectivity": last_p,
        "trait_distance": last_td,
        "effective_exchange_pressure": effective_exchange_pressure(last_p, ri),
    }


def load_parent(root: Path):
    root = Path(root)
    p = root / "inputs/D3_0B_PARENT"
    diag = _read_json(p / "dynamic_deme_diagnostics.json")
    audit = _read_json(p / "dynamic_deme_audit.json")
    if diag.get("semantic_status") != "PASS_DYNAMIC_DEME_GENE_FLOW_COUPLING_CANDIDATE":
        raise ValueError("D3.0C requires passing D3.0B diagnostics")
    if not str(audit.get("status", "")).startswith("PASS_DYNAMIC_DEME"):
        raise ValueError("D3.0C requires passing D3.0B audit")
    state = np.load(p / "dynamic_deme_state.npz")
    graph = _read_json(p / "gene_flow_graph.json")
    return diag, audit, state, graph


def calibrate_parent_endpoint(root: Path, cfg: SpeciationGateConfig | None = None):
    cfg = cfg or SpeciationGateConfig()
    diag, audit, z, graph = load_parent(root)
    deme_ids = [str(x) for x in z["deme_id"].tolist()]
    id_to_idx = {d:i for i,d in enumerate(deme_ids)}
    totals = z["deme_total_history"][-1].astype(float)
    gen = z["generation_time_proxy_years"].astype(float)
    rows = []
    old_upper_gen = []
    ready_zero_clock = 0
    ready_old_clock_upper_bound = 0
    for rec in graph["pairs"]:
        i, j = id_to_idx[rec["deme_a"]], id_to_idx[rec["deme_b"]]
        p = contact_connectivity_from_d30b_gene_flow(rec["gene_flow"], cfg.gene_flow_contact_ceiling)
        # D3.0B RI is retained only as a seed diagnostic. It is not retroactively
        # interpreted as calibrated intrinsic RI.
        ri_seed = float(rec["RI"])
        pair_gen = max(float(gen[i]), float(gen[j]))
        old_years = float(rec["isolation_persistence_years"])
        old_gen = old_years / max(pair_gen, 1e-15)
        old_upper_gen.append(old_gen)
        spop = float(totals[z["deme_species_index"] == z["deme_species_index"][i]].sum())
        branch = float(min(totals[i], totals[j]))
        complement = max(0.0, spop - branch)
        ev0 = evaluate_pair_gate(
            isolation_clock_generations=0.0, intrinsic_ri=ri_seed,
            trait_distance=float(rec["trait_distance"]), contact_connectivity=p,
            branch_population=branch, complement_population=complement,
            species_population=spop, cfg=cfg,
        )
        ev_old = evaluate_pair_gate(
            isolation_clock_generations=old_gen, intrinsic_ri=ri_seed,
            trait_distance=float(rec["trait_distance"]), contact_connectivity=p,
            branch_population=branch, complement_population=complement,
            species_population=spop, cfg=cfg,
        )
        ready_zero_clock += int(ev0["gate_ready"])
        ready_old_clock_upper_bound += int(ev_old["gate_ready"])
        rows.append({
            "species_id": rec["species_id"], "deme_a": rec["deme_a"], "deme_b": rec["deme_b"],
            "D3_0B_gene_flow_step_coupling": float(rec["gene_flow"]),
            "contact_connectivity": p,
            "trait_distance": float(rec["trait_distance"]),
            "D3_0B_diagnostic_RI_seed": ri_seed,
            "pair_generation_time_proxy_years": pair_gen,
            "old_provisional_persistence_generation_upper_bound": old_gen,
            "calibrated_clock_initialization": 0.0,
            "effective_exchange_pressure_at_endpoint": effective_exchange_pressure(p, ri_seed),
            "gate_ready_with_calibrated_zero_clock": bool(ev0["gate_ready"]),
            "gate_ready_even_if_old_clock_were_used": bool(ev_old["gate_ready"]),
            "gate_checks_zero_clock": ev0["checks"],
        })
    old_upper_gen = np.asarray(old_upper_gen, dtype=float)
    summary = {
        "version": "0.6.3D3.0C",
        "parent": "0.6.3D3.0B",
        "semantic_status": "PASS_BIOLOGICAL_TIME_SPECIATION_GATE_CALIBRATION_CANDIDATE",
        "pair_count": len(rows),
        "calibrated_clock_initialization_at_D3_0B_endpoint": "ZERO_NO_RETROACTIVE_PROMOTION",
        "reason": "D3.0B did not export a timestep-independent reproductive-exchange trajectory; its old persistence counter used provisional thresholds known to be uncalibrated.",
        "gate_ready_pairs_zero_clock": ready_zero_clock,
        "gate_ready_pairs_even_if_old_persistence_upper_bound_used": ready_old_clock_upper_bound,
        "old_provisional_generation_upper_bound_min": float(old_upper_gen.min()),
        "old_provisional_generation_upper_bound_median": float(np.median(old_upper_gen)),
        "old_provisional_generation_upper_bound_max": float(old_upper_gen.max()),
        "D3_0B_G_promoted_as_biological_gene_flow": False,
        "D3_0B_RI_promoted_as_intrinsic_RI": False,
        "speciation_enabled": False,
        "species_fusion_enabled": False,
        "adaptive_radiation_enabled": False,
    }
    return summary, rows
