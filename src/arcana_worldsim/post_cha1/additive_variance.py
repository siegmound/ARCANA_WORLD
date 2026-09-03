from __future__ import annotations

from dataclasses import dataclass, asdict
import math
import numpy as np


STATUS = "PASS_ADDITIVE_GENETIC_VARIANCE_DYNAMICS_CALIBRATION_CANDIDATE"


@dataclass(frozen=True)
class AdditiveVarianceConfig:
    # Mutation retains the D3.1 normalized variance-supply convention. It is a
    # variance source only and never directly shifts a trait mean.
    mutation_variance_supply_normalized_per_myr: float = 0.002
    mutation_variance_ceiling_normalized: float = 0.05

    # D3.3A long-horizon homeostasis controls. Disabled by default so all
    # D3.1A-D3.2D release paths remain bit-identical. When enabled, the legacy
    # per-Myr mutation supply is converted to a per-generation supply using the
    # reference generation time, and standing VA is continuously depleted by
    # stabilizing selection around the local optimum. This affects variance
    # only; it never applies a directional trait-mean shift.
    variance_homeostasis_enabled: bool = False
    mutation_supply_generation_scaled: bool = False
    mutation_supply_reference_generation_years: float = 5.0
    baseline_stabilizing_variance_depletion_per_generation: float = 0.0
    nonlinear_stabilizing_variance_depletion_per_myr_per_q: float = 0.0

    # Recalibrated candidate coefficients. The v0.6.3C documents recover the
    # process semantics but the original numerical source is not available.
    selection_variance_depletion_per_generation: float = 2.0e-6
    selection_pressure_ceiling: float = 4.0

    # Population units in WorldSim are effective macrofaunal abundance units,
    # not literal breeders. This factor is therefore explicitly a calibration
    # proxy used only to map abundance to an effective drift reservoir.
    drift_individual_equivalents_per_population_unit: float = 250_000.0
    drift_min_effective_size: float = 500.0

    # Gene-flow exchange is inherited from D3.1's contact kernel. This cap only
    # protects the moment exchange operator if many pairwise edges coincide.
    maximum_total_exchange_fraction_per_deme: float = 0.45

    def to_dict(self):
        return asdict(self)


def trait_scales(meta: dict, body_mass_scale: float) -> np.ndarray:
    return np.array([
        max(float(meta["thermal_niche_sigma_c"]), 1e-6),
        max(float(meta["aridity_niche_sigma"]) / 1.55, 1e-4),
        max(float(body_mass_scale), 1e-6),
    ], dtype=float)


def normalize_variance(va: np.ndarray, scales: np.ndarray) -> np.ndarray:
    return np.asarray(va, dtype=float) / np.maximum(scales * scales, 1e-30)


def denormalize_variance(q: np.ndarray, scales: np.ndarray) -> np.ndarray:
    return np.asarray(q, dtype=float) * scales * scales


def mutation_supply(va: np.ndarray, scales: np.ndarray, dt_years: float,
                    cfg: AdditiveVarianceConfig) -> np.ndarray:
    q = normalize_variance(va, scales)
    q = q + cfg.mutation_variance_supply_normalized_per_myr * (dt_years / 1_000_000.0)
    q = np.clip(q, 0.0, cfg.mutation_variance_ceiling_normalized)
    return denormalize_variance(q, scales)


def selection_depletion(va: np.ndarray, trait_before: np.ndarray, targets: np.ndarray,
                        scales: np.ndarray, generation_time_years: float,
                        dt_years: float, cfg: AdditiveVarianceConfig) -> np.ndarray:
    """Deplete VA under sustained directional/stabilizing response pressure.

    `targets` contains thermal and drought targets. Body mass intentionally has
    no directional target in D3.1/D3.1A and therefore gets zero selection
    depletion here. The pressure is standardized by each trait's niche scale.
    """
    out = np.asarray(va, dtype=float).copy()
    if not np.all(np.isfinite(targets[:2])):
        return out
    generations = max(float(dt_years) / max(float(generation_time_years), 1e-9), 0.0)
    pressure = np.zeros(3, dtype=float)
    pressure[:2] = ((np.asarray(targets[:2], dtype=float) - np.asarray(trait_before[:2], dtype=float))
                    / np.maximum(scales[:2], 1e-12)) ** 2
    pressure = np.clip(pressure, 0.0, cfg.selection_pressure_ceiling)
    decay = np.exp(-cfg.selection_variance_depletion_per_generation * pressure * generations)
    out *= decay
    return np.maximum(out, 0.0)


def drift_depletion(va: np.ndarray, population_total: float, generation_time_years: float,
                    dt_years: float, cfg: AdditiveVarianceConfig) -> np.ndarray:
    """Finite-population loss of VA using an explicit effective-size proxy.

    This is deterministic expected drift depletion; D3.1A does not add
    stochastic directional mean-trait kicks.
    """
    generations = max(float(dt_years) / max(float(generation_time_years), 1e-9), 0.0)
    ne = max(
        cfg.drift_min_effective_size,
        max(float(population_total), 0.0) * cfg.drift_individual_equivalents_per_population_unit,
    )
    # Wright-Fisher expectation: heterozygosity/variance retention is close to
    # exp(-g/(2Ne)) over g generations.
    retention = math.exp(-generations / max(2.0 * ne, 1e-12))
    return np.maximum(np.asarray(va, dtype=float) * retention, 0.0)


def gene_flow_moment_mix(trait: np.ndarray, va: np.ndarray, population_total: np.ndarray,
                         gene_flow: np.ndarray, intrinsic_ri: np.ndarray,
                         root_species_index: np.ndarray,
                         cfg: AdditiveVarianceConfig):
    """Mix first/second moments under symmetric reproductive exchange.

    The operator simultaneously mixes means and VA. It conserves the
    population-weighted first and second trait moments within each root lineage
    (apart from a protective edge scaling if aggregate exchange would exceed the
    configured fraction of a deme).
    """
    z = np.asarray(trait, dtype=float)
    v = np.maximum(np.asarray(va, dtype=float), 0.0)
    n = np.maximum(np.asarray(population_total, dtype=float), 0.0)
    nd, nt = z.shape

    first = n[:, None] * z
    second = n[:, None] * (v + z * z)
    d_first = np.zeros_like(first)
    d_second = np.zeros_like(second)

    edges = []
    outgoing = np.zeros(nd, dtype=float)
    for i in range(nd):
        if n[i] <= 0:
            continue
        for j in range(i + 1, nd):
            if root_species_index[i] != root_species_index[j] or n[j] <= 0:
                continue
            mix = float(gene_flow[i, j]) * (1.0 - float(intrinsic_ri[i, j]))
            if mix <= 0:
                continue
            harmonic = 2.0 * n[i] * n[j] / max(n[i] + n[j], 1e-30)
            exchange = max(0.0, mix * harmonic)
            if exchange <= 0:
                continue
            edges.append([i, j, exchange])
            outgoing[i] += exchange
            outgoing[j] += exchange

    # Symmetric per-edge scale using the tightest endpoint constraint.
    edge_scale = np.ones(len(edges), dtype=float)
    for k, (i, j, _) in enumerate(edges):
        si = 1.0 if outgoing[i] <= 0 else min(
            1.0, cfg.maximum_total_exchange_fraction_per_deme * n[i] / outgoing[i]
        )
        sj = 1.0 if outgoing[j] <= 0 else min(
            1.0, cfg.maximum_total_exchange_fraction_per_deme * n[j] / outgoing[j]
        )
        edge_scale[k] = min(si, sj)

    total_exchange = 0.0
    for scale, (i, j, exchange0) in zip(edge_scale, edges):
        x = float(exchange0 * scale)
        if x <= 0:
            continue
        total_exchange += x
        d_first[i] += x * (z[j] - z[i])
        d_first[j] += x * (z[i] - z[j])
        m2i = v[i] + z[i] * z[i]
        m2j = v[j] + z[j] * z[j]
        d_second[i] += x * (m2j - m2i)
        d_second[j] += x * (m2i - m2j)

    first_new = first + d_first
    second_new = second + d_second
    z_new = z.copy()
    v_new = v.copy()
    alive = n > 0
    z_new[alive] = first_new[alive] / n[alive, None]
    v_new[alive] = second_new[alive] / n[alive, None] - z_new[alive] * z_new[alive]
    v_new = np.maximum(v_new, 0.0)

    diagnostics = {
        "total_pair_exchange_mass": float(total_exchange),
        "first_moment_conservation_max_abs": float(np.max(np.abs(first_new.sum(axis=0) - first.sum(axis=0)))),
        "second_moment_conservation_max_abs": float(np.max(np.abs(second_new.sum(axis=0) - second.sum(axis=0)))),
        "edge_count": len(edges),
    }
    return z_new, v_new, diagnostics


def advance_nonflow_variance(va: np.ndarray, trait_before_selection: np.ndarray,
                             targets: np.ndarray, populations: np.ndarray,
                             generation_time: np.ndarray, root_idx: np.ndarray,
                             root_species_ids: list[str], metadata: dict,
                             body_mass_scale: float, dt_years: float,
                             cfg: AdditiveVarianceConfig):
    """Advance selection depletion + drift + mutation as one continuous ODE.

    For normalized additive variance q and locally constant coefficients over a
    numerical step:

        dq/dt = mu_q - (lambda_selection + lambda_drift) q

    This has an exact exponential step solution. It avoids a dt-dependent
    mutation floor in tiny demes that appeared when depletion and supply were
    split into sequential end-of-step operators.
    """
    out = np.asarray(va, dtype=float).copy()
    components = []
    dt = max(float(dt_years), 0.0)
    legacy_mu_per_year = cfg.mutation_variance_supply_normalized_per_myr / 1_000_000.0

    for di, si0 in enumerate(root_idx):
        sid = root_species_ids[int(si0)]
        scales = trait_scales(metadata[sid], body_mass_scale)
        q0 = normalize_variance(out[di], scales)
        gen_time = max(float(generation_time[di]), 1e-9)

        pressure = np.zeros(3, dtype=float)
        if np.all(np.isfinite(targets[di][:2])):
            pressure[:2] = ((np.asarray(targets[di][:2], dtype=float)
                             - np.asarray(trait_before_selection[di][:2], dtype=float))
                            / np.maximum(scales[:2], 1e-12)) ** 2
        pressure = np.clip(pressure, 0.0, cfg.selection_pressure_ceiling)

        lambda_selection = (
            cfg.selection_variance_depletion_per_generation * pressure / gen_time
        )
        if cfg.variance_homeostasis_enabled and cfg.mutation_supply_generation_scaled:
            mu_per_year = (
                legacy_mu_per_year
                * max(float(cfg.mutation_supply_reference_generation_years), 1e-9)
                / gen_time
            )
        else:
            mu_per_year = legacy_mu_per_year
        if cfg.variance_homeostasis_enabled:
            lambda_baseline = np.full(
                3,
                max(float(cfg.baseline_stabilizing_variance_depletion_per_generation), 0.0)
                / gen_time,
                dtype=float,
            )
            quadratic_depletion_per_year = (
                max(float(cfg.nonlinear_stabilizing_variance_depletion_per_myr_per_q), 0.0)
                / 1_000_000.0
            )
        else:
            lambda_baseline = np.zeros(3, dtype=float)
            quadratic_depletion_per_year = 0.0
        ne = max(
            cfg.drift_min_effective_size,
            max(float(populations[di]), 0.0)
            * cfg.drift_individual_equivalents_per_population_unit,
        )
        lambda_drift_scalar = 1.0 / max(2.0 * ne * gen_time, 1e-30)
        lambda_drift = np.full(3, lambda_drift_scalar, dtype=float)
        lambda_total = lambda_selection + lambda_baseline + lambda_drift

        q_after_selection = q0 * np.exp(-(lambda_selection + lambda_baseline) * dt)
        q_after_drift = q_after_selection * np.exp(-lambda_drift * dt)

        retention = np.exp(-lambda_total * dt)
        q_new = np.empty_like(q0)
        if quadratic_depletion_per_year <= 0.0:
            small = lambda_total < 1e-18
            q_new[small] = q0[small] + mu_per_year * dt
            q_new[~small] = (
                q0[~small] * retention[~small]
                + (mu_per_year / lambda_total[~small]) * (1.0 - retention[~small])
            )
        else:
            # Exact Riccati step for dq/dt = mu - a*q - b*q^2.
            # This is the long-horizon stabilizing-selection approximation: the
            # depletion of standing variance is negligible at small q and grows
            # with q^2, producing an internal mutation-selection equilibrium.
            b = float(quadratic_depletion_per_year)
            for ti in range(len(q0)):
                a = float(lambda_total[ti]); mu = float(mu_per_year)
                disc = math.sqrt(max(a*a + 4.0*b*mu, 0.0))
                if disc < 1e-24:
                    q_new[ti] = q0[ti]
                    continue
                r_pos = (-a + disc) / (2.0*b)
                r_neg = (-a - disc) / (2.0*b)
                denom0 = float(q0[ti] - r_neg)
                c0 = 0.0 if abs(denom0) < 1e-30 else float((q0[ti] - r_pos) / denom0)
                c = c0 * math.exp(-disc * dt)
                denom = 1.0 - c
                q_new[ti] = r_pos if abs(denom) < 1e-30 else (r_pos - c*r_neg) / denom
        q_new = np.clip(q_new, 0.0, cfg.mutation_variance_ceiling_normalized)
        out[di] = denormalize_variance(q_new, scales)

        components.append({
            "deme_index": int(di),
            "species_id": sid,
            "q_before": q0.tolist(),
            "q_after_selection": q_after_selection.tolist(),
            "q_after_drift": q_after_drift.tolist(),
            "q_after_mutation": q_new.tolist(),
            "selection_pressure": pressure.tolist(),
            "lambda_selection_per_year": lambda_selection.tolist(),
            "lambda_baseline_stabilizing_per_year": lambda_baseline.tolist(),
            "lambda_drift_per_year": lambda_drift.tolist(),
            "mutation_supply_normalized_per_year": float(mu_per_year),
            "variance_homeostasis_enabled": bool(cfg.variance_homeostasis_enabled),
            "mutation_supply_generation_scaled": bool(cfg.mutation_supply_generation_scaled),
            "nonlinear_stabilizing_variance_depletion_per_year_per_q": float(quadratic_depletion_per_year),
            "integration_semantics": (
                "EXACT_CONSTANT_COEFFICIENT_RICCATI_ODE_STEP"
                if quadratic_depletion_per_year > 0.0
                else "EXACT_CONSTANT_COEFFICIENT_LINEAR_ODE_STEP"
            ),
        })
    return out, components


def normalized_variance_matrix(va: np.ndarray, root_idx: np.ndarray,
                               root_species_ids: list[str], metadata: dict,
                               body_mass_scale: float) -> np.ndarray:
    rows = []
    for di, si0 in enumerate(root_idx):
        sid = root_species_ids[int(si0)]
        scales = trait_scales(metadata[sid], body_mass_scale)
        rows.append(normalize_variance(va[di], scales))
    return np.asarray(rows, dtype=float)


def normalized_variance_summary(va: np.ndarray, root_idx: np.ndarray,
                                root_species_ids: list[str], metadata: dict,
                                body_mass_scale: float) -> dict:
    q = normalized_variance_matrix(va, root_idx, root_species_ids, metadata, body_mass_scale)
    if q.size == 0:
        return {"min": 0.0, "median": 0.0, "p95": 0.0, "max": 0.0, "mean": 0.0}
    flat = q.reshape(-1)
    return {
        "min": float(np.min(flat)),
        "median": float(np.median(flat)),
        "p95": float(np.percentile(flat, 95)),
        "max": float(np.max(flat)),
        "mean": float(np.mean(flat)),
    }
