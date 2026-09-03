from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.linalg import expm, logm

from arcana_worldsim.post_cha1 import additive_variance as av
from .nemo_benchmarks import NemoBenchmarkScenario


@dataclass(frozen=True)
class CadenceNormalizationSpec:
    arcana_interval_years: float = 125_000.0
    arcana_substep_years: float = 25_000.0
    mutation_q_per_myr: float = 0.002
    nonlinear_b_per_myr_per_q: float = 0.9876543209876544
    q_star: float = 0.045
    drift_individual_equivalents_per_population_unit: float = 250_000_000.0
    drift_min_effective_size: float = 500.0
    maximum_total_exchange_fraction_per_deme: float = 0.45

    def __post_init__(self) -> None:
        if self.arcana_interval_years <= 0 or self.arcana_substep_years <= 0:
            raise ValueError("cadences must be positive")
        ratio = self.arcana_interval_years / self.arcana_substep_years
        if abs(ratio - round(ratio)) > 1e-12:
            raise ValueError("ARCANA interval must be an integer multiple of substep")
        expected = float(np.sqrt(self.mutation_q_per_myr / self.nonlinear_b_per_myr_per_q))
        if abs(expected - self.q_star) > 1e-12:
            raise ValueError("q_star must equal sqrt(mu/b) for the locked R3.5 authority")

    @property
    def substeps(self) -> int:
        return int(round(self.arcana_interval_years / self.arcana_substep_years))


def arcana_offdiag_to_stochastic(exchange: np.ndarray) -> np.ndarray:
    g = np.asarray(exchange, dtype=float)
    if g.ndim != 2 or g.shape[0] != g.shape[1]:
        raise ValueError("exchange must be square")
    if np.any(g < -1e-15) or np.max(np.abs(np.diag(g))) > 1e-15:
        raise ValueError("ARCANA exchange must be non-negative with zero diagonal")
    rows = g.sum(axis=1)
    if np.any(rows > 1.0 + 1e-12):
        raise ValueError("exchange row sum exceeds one")
    d = g.copy()
    np.fill_diagonal(d, 1.0 - rows)
    return d


def stochastic_interval_to_subinterval(
    interval_matrix: np.ndarray,
    interval_years: float,
    subinterval_years: float,
    *,
    atol: float = 1e-10,
) -> np.ndarray:
    """Cadence-normalize a finite-step Markov dispersal matrix.

    The interval matrix is interpreted as a finite-step transition operator.
    We compute a continuous-time generator with logm and exponentiate it over
    the requested subinterval. Non-embeddable inputs are rejected rather than
    silently projected onto a different biological process.
    """
    d = np.asarray(interval_matrix, dtype=float)
    if d.ndim != 2 or d.shape[0] != d.shape[1]:
        raise ValueError("interval_matrix must be square")
    if interval_years <= 0 or subinterval_years <= 0 or subinterval_years > interval_years:
        raise ValueError("invalid interval lengths")
    if np.any(d < -atol) or not np.allclose(d.sum(axis=1), 1.0, atol=atol, rtol=0.0):
        raise ValueError("interval_matrix must be row-stochastic")
    q = logm(d) / float(interval_years)
    if np.max(np.abs(np.imag(q))) > 1e-9:
        raise ValueError("finite-step dispersal matrix has no accepted real generator")
    q = np.real(q)
    # A valid CTMC generator has non-negative off-diagonal entries and rows sum zero.
    off = q - np.diag(np.diag(q))
    if np.min(off) < -1e-10 or not np.allclose(q.sum(axis=1), 0.0, atol=1e-9, rtol=0.0):
        raise ValueError("finite-step dispersal matrix is not embeddable as an accepted CTMC generator")
    sub = np.real(expm(q * float(subinterval_years)))
    sub[np.abs(sub) < 1e-15] = 0.0
    if np.min(sub) < -1e-10 or not np.allclose(sub.sum(axis=1), 1.0, atol=1e-9, rtol=0.0):
        raise ValueError("derived subinterval dispersal matrix is invalid")
    sub = np.maximum(sub, 0.0)
    sub /= sub.sum(axis=1, keepdims=True)
    return sub


def interval_exchange_to_nemo_generation(
    exchange: np.ndarray,
    interval_years: float,
    generation_time_years: float,
) -> np.ndarray:
    if generation_time_years <= 0:
        raise ValueError("generation_time_years must be positive")
    return stochastic_interval_to_subinterval(
        arcana_offdiag_to_stochastic(exchange), interval_years, generation_time_years
    )


def edge_hazard_substep_exchange(exchange: np.ndarray, n_substeps: int) -> np.ndarray:
    """Symmetry-preserving hazard conversion for the ARCANA pairwise moment operator.

    gene_flow_moment_mix consumes symmetric pairwise effective-exchange edges,
    not a Markov transition matrix. Each edge is therefore cadence-normalized
    independently: g_sub = 1 - (1-g_interval)^(1/n). This keeps symmetry and
    avoids the five-fold overmixing produced by naively repeating the 125-kyr
    edge matrix at 25-kyr cadence.
    """
    g = np.asarray(exchange, dtype=float)
    if n_substeps < 1:
        raise ValueError("n_substeps must be >=1")
    if np.any(g < -1e-15) or np.any(g > 1.0 + 1e-12):
        raise ValueError("exchange entries must be in [0,1]")
    if np.max(np.abs(np.diag(g))) > 1e-15:
        raise ValueError("ARCANA exchange diagonal must be zero")
    out = 1.0 - np.power(np.maximum(1.0 - g, 0.0), 1.0 / float(n_substeps))
    np.fill_diagonal(out, 0.0)
    return out


def _variance_cfg(spec: CadenceNormalizationSpec) -> av.AdditiveVarianceConfig:
    return av.AdditiveVarianceConfig(
        mutation_variance_supply_normalized_per_myr=spec.mutation_q_per_myr,
        mutation_variance_ceiling_normalized=1.0,  # diagnostic non-binding ceiling
        variance_homeostasis_enabled=True,
        mutation_supply_generation_scaled=False,
        mutation_supply_reference_generation_years=5.0,
        baseline_stabilizing_variance_depletion_per_generation=0.0,
        nonlinear_stabilizing_variance_depletion_per_myr_per_q=spec.nonlinear_b_per_myr_per_q,
        selection_variance_depletion_per_generation=2.0e-8,
        selection_pressure_ceiling=4.0,
        drift_individual_equivalents_per_population_unit=spec.drift_individual_equivalents_per_population_unit,
        drift_min_effective_size=spec.drift_min_effective_size,
        maximum_total_exchange_fraction_per_deme=spec.maximum_total_exchange_fraction_per_deme,
    )


def simulate_arcana_cadence_probe(
    scenario: NemoBenchmarkScenario,
    *,
    macrosteps: int = 40,
    substeps_per_macrostep: int = 1,
    rate_normalize_exchange: bool = True,
    spec: CadenceNormalizationSpec = CadenceNormalizationSpec(),
) -> dict:
    if macrosteps < 1 or substeps_per_macrostep < 1:
        raise ValueError("macrosteps and substeps_per_macrostep must be positive")
    if len(scenario.phases) != 1:
        raise ValueError("cadence probe currently requires a single-phase scenario")
    if spec.substeps != 5:
        raise ValueError("R3.6C authority expects 125 kyr / 25 kyr = 5")

    z2 = np.asarray(scenario.normalized_trait_means, dtype=float).copy()
    q2 = np.asarray(scenario.normalized_additive_variance, dtype=float).copy()
    nd = z2.shape[0]
    # Add a passive body axis so we execute the exact D3.3A 3-axis operator.
    z = np.column_stack([z2, np.zeros(nd)])
    va = np.column_stack([q2, np.full(nd, spec.q_star)])
    # Keep ARCANA population semantics unchanged: these are WorldSim abundance
    # units, not literal NEMO breeders. R3.6C therefore does NOT compare absolute
    # drift between engines. Cross-engine inference uses admixture excess over a
    # matched no-flow control and population-size sensitivity on the NEMO side.
    pop = scenario.population_individuals.astype(float)
    gen = np.full(nd, scenario.generation_time_years, dtype=float)
    roots = np.zeros(nd, dtype=int)
    root_ids = ["REFERENCE_SPECIES"]
    metadata = {
        "REFERENCE_SPECIES": {
            "thermal_niche_sigma_c": 1.0,
            "aridity_niche_sigma": 1.55,
        }
    }
    ri = np.zeros((nd, nd), dtype=float)
    targets = z[:, :2].copy()  # isolate admixture/homeostasis; no directional pressure
    cfg = _variance_cfg(spec)

    interval_g = np.asarray(scenario.phases[0].exchange_matrix, dtype=float)
    if substeps_per_macrostep == 1:
        g = interval_g
        dt = spec.arcana_interval_years
    else:
        if substeps_per_macrostep != spec.substeps:
            raise ValueError("R3.6C only authorizes 1x125k or 5x25k cadence probes")
        g = edge_hazard_substep_exchange(interval_g, substeps_per_macrostep) if rate_normalize_exchange else interval_g
        dt = spec.arcana_interval_years / substeps_per_macrostep

    telemetry = []
    for macro in range(macrosteps):
        for sub in range(substeps_per_macrostep):
            z_before = z.copy()
            z, va, flow = av.gene_flow_moment_mix(z, va, pop, g, ri, roots, cfg)
            va, comp = av.advance_nonflow_variance(
                va, z_before, targets, pop, gen, roots, root_ids, metadata,
                1.0, dt, cfg,
            )
            telemetry.append({
                "macrostep": macro,
                "substep": sub,
                "max_q": float(np.max(va[:, :2])),
                "mean_q": float(np.mean(va[:, :2])),
                "trait_spread": float(np.max(z[:, :2]) - np.min(z[:, :2])),
                "pair_exchange_mass": float(flow["total_pair_exchange_mass"]),
            })

    return {
        "schema": "ARCANA_R36C_CADENCE_PROBE_V1",
        "scenario": scenario.name,
        "macrosteps": macrosteps,
        "substeps_per_macrostep": substeps_per_macrostep,
        "rate_normalize_exchange": bool(rate_normalize_exchange),
        "dt_years": dt,
        "final_trait_mean": z[:, :2].tolist(),
        "final_additive_variance_q": va[:, :2].tolist(),
        "final_max_q": float(np.max(va[:, :2])),
        "final_mean_q": float(np.mean(va[:, :2])),
        "telemetry": telemetry,
        "locks": {"mu": spec.mutation_q_per_myr, "b": spec.nonlinear_b_per_myr_per_q, "q_star": spec.q_star},
    }


def build_three_way_reference_plan(
    scenario: NemoBenchmarkScenario,
    *,
    spec: CadenceNormalizationSpec = CadenceNormalizationSpec(),
) -> dict:
    if len(scenario.phases) != 1:
        raise ValueError("R3.6C initial three-way plan requires a single-phase scenario")
    interval = arcana_offdiag_to_stochastic(scenario.phases[0].exchange_matrix)
    nemo_per_generation = interval_exchange_to_nemo_generation(
        scenario.phases[0].exchange_matrix,
        spec.arcana_interval_years,
        scenario.generation_time_years,
    )
    five25 = edge_hazard_substep_exchange(scenario.phases[0].exchange_matrix, spec.substeps)
    # Verify Markov cadence normalization by composition.
    n_gen = spec.arcana_interval_years / scenario.generation_time_years
    # n_gen is huge; use generator equivalence rather than repeated matrix_power.
    regen = stochastic_interval_to_subinterval(interval, spec.arcana_interval_years, spec.arcana_interval_years)
    payload = {
        "schema": "ARCANA_R36C_THREE_WAY_REFERENCE_PLAN_V1",
        "scenario": scenario.name,
        "arcana_125k_offdiag_exchange": scenario.phases[0].exchange_matrix.tolist(),
        "arcana_125k_stochastic_matrix": interval.tolist(),
        "arcana_25k_pairwise_exchange": five25.tolist(),
        "nemo_per_generation_stochastic_matrix": nemo_per_generation.tolist(),
        "generation_time_years": scenario.generation_time_years,
        "generations_per_125k_interval": n_gen,
        "cadence": {"arcana_macro_years": spec.arcana_interval_years, "arcana_quantgen_substep_years": spec.arcana_substep_years},
        "authority": {
            "canonical_write_allowed": False,
            "automatic_calibration_allowed": False,
            "mu_b_qstar_locked": True,
            "nemo_is_reference_only": True,
        },
        "checks": {
            "interval_roundtrip_identity": bool(np.allclose(regen, interval, atol=1e-12, rtol=0.0)),
            "nemo_rows_sum_one": bool(np.allclose(nemo_per_generation.sum(axis=1), 1.0, atol=1e-12, rtol=0.0)),
        },
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["semantic_sha256"] = sha256(blob).hexdigest()
    return payload


def write_three_way_plan(plan: dict, path: str | Path) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def embeddable_reference_exchange_from_edge_targets(exchange: np.ndarray, interval_years: float) -> np.ndarray:
    """Build a NEW embeddable stress-reference interval from symmetric edge targets.

    This is not a projection of an ARCANA production matrix and must never be
    substituted into canonical replay. It is only for cross-engine benchmark
    construction when an arbitrary finite-step stress matrix is not exactly
    embeddable in a per-generation continuous-time migration process.
    """
    g = np.asarray(exchange, dtype=float)
    if g.ndim != 2 or g.shape[0] != g.shape[1] or not np.allclose(g, g.T, atol=1e-12, rtol=0.0):
        raise ValueError("reference edge targets must be symmetric square matrix")
    if np.max(np.abs(np.diag(g))) > 1e-15 or np.any(g < 0) or np.any(g >= 0.5):
        raise ValueError("edge targets must have zero diagonal and lie in [0,0.5)")
    n = g.shape[0]
    q = np.zeros((n,n), dtype=float)
    for i in range(n):
        for j in range(i+1,n):
            p = float(g[i,j])
            if p <= 0: continue
            # Two-state exact mapping p(T)=0.5*(1-exp(-2 lambda T)).
            lam = -np.log1p(-2.0*p) / (2.0*float(interval_years))
            q[i,j] = q[j,i] = lam
    np.fill_diagonal(q, -q.sum(axis=1))
    d = np.real(expm(q*float(interval_years)))
    if np.min(d) < -1e-12 or not np.allclose(d.sum(axis=1),1.0,atol=1e-12,rtol=0.0):
        raise ValueError("failed to construct embeddable reference")
    d=np.maximum(d,0); d/=d.sum(axis=1,keepdims=True)
    out=d.copy(); np.fill_diagonal(out,0.0)
    return out
