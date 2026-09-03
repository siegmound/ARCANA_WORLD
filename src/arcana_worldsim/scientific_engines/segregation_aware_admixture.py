from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import numpy as np


@dataclass(frozen=True)
class SegregationAwareAdmixtureConfig:
    """Governed reduced-order admixture model introduced in v0.6D1-R3.7.

    `recombination_fraction_per_generation` is an explicit architecture
    parameter for the transient ancestry/LD covariance state.  The R3.7
    reference benchmark uses 0.5 because the NEMO 2.4.2 reference uses free
    recombination.  This value is NOT promoted to World-1 production by R3.7.
    """

    maximum_total_exchange_fraction_per_deme: float = 0.45
    recombination_fraction_per_generation: float = 0.5
    euclidean_tolerance: float = 1.0e-9

    def __post_init__(self) -> None:
        if not (0.0 < self.maximum_total_exchange_fraction_per_deme <= 1.0):
            raise ValueError("maximum_total_exchange_fraction_per_deme must be in (0,1]")
        if not (0.0 <= self.recombination_fraction_per_generation <= 0.5):
            raise ValueError("recombination_fraction_per_generation must be in [0,0.5]")
        if self.euclidean_tolerance <= 0:
            raise ValueError("euclidean_tolerance must be positive")


def qtl_segregation_potential(effect_sizes: np.ndarray, allele_frequencies: np.ndarray) -> np.ndarray:
    """Return pairwise trait-specific segregation potential S_ij.

    For additive diallelic QTLs with ARCANA/NEMO effect `a_l` and allele
    frequency p_il:

        S_ij = 2 * sum_l a_l^2 (p_il - p_jl)^2

    If a destination is formed by weights w_j over source demes, the exact
    increase in *genic* additive variance caused by mixing allele frequencies is

        0.5 * sum_j sum_k w_j w_k S_jk.

    This is intentionally different from whole-trait mixture variance
    0.5*sum_jk w_j w_k (z_j-z_k)^2, whose cross-locus covariance terms are not
    durable genic VA.
    """
    a = np.asarray(effect_sizes, dtype=float)
    p = np.asarray(allele_frequencies, dtype=float)
    if a.ndim != 2:
        raise ValueError("effect_sizes must be trait x locus")
    if p.ndim != 3 or p.shape[1:] != a.shape:
        raise ValueError("allele_frequencies must be deme x trait x locus and match effects")
    if np.any(~np.isfinite(a)) or np.any(~np.isfinite(p)):
        raise ValueError("QTL arrays must be finite")
    if np.any(p < -1e-12) or np.any(p > 1.0 + 1e-12):
        raise ValueError("allele frequencies must lie in [0,1]")
    # nd x nd x trait x locus
    dp = p[:, None, :, :] - p[None, :, :, :]
    s = 2.0 * np.sum((a[None, None, :, :] ** 2) * (dp ** 2), axis=-1)
    # Numerical hygiene.
    s = np.maximum(s, 0.0)
    for t in range(s.shape[2]):
        np.fill_diagonal(s[:, :, t], 0.0)
    return s


def validate_segregation_potential(potential: np.ndarray, *, tolerance: float = 1e-9) -> dict[str, float]:
    """Validate that each trait slice is a squared-Euclidean distance matrix.

    S_ij is a squared distance in latent allele-frequency/effect space.  The
    centered Gram matrix therefore has to be positive semidefinite (up to
    floating-point tolerance).  Invalid state is rejected rather than silently
    projected onto another genetic process.
    """
    s = np.asarray(potential, dtype=float)
    if s.ndim != 3 or s.shape[0] != s.shape[1]:
        raise ValueError("segregation potential must be deme x deme x trait")
    if np.any(~np.isfinite(s)):
        raise ValueError("segregation potential must be finite")
    if np.min(s) < -tolerance:
        raise ValueError("segregation potential cannot be negative")
    if not np.allclose(s, np.swapaxes(s, 0, 1), atol=tolerance, rtol=0.0):
        raise ValueError("segregation potential must be symmetric")
    n = s.shape[0]
    if n == 0:
        return {"minimum_centered_gram_eigenvalue": 0.0, "max_diagonal_abs": 0.0}
    max_diag = max(float(np.max(np.abs(np.diag(s[:, :, t])))) for t in range(s.shape[2]))
    if max_diag > tolerance:
        raise ValueError("segregation potential diagonal must be zero")
    h = np.eye(n) - np.ones((n, n), dtype=float) / n
    min_eig = math.inf
    for t in range(s.shape[2]):
        gram = -0.5 * h @ s[:, :, t] @ h
        ev = np.linalg.eigvalsh(0.5 * (gram + gram.T))
        min_eig = min(min_eig, float(np.min(ev)))
    if min_eig < -tolerance:
        raise ValueError("segregation potential is not squared-Euclidean")
    return {
        "minimum_centered_gram_eigenvalue": float(min_eig),
        "max_diagonal_abs": float(max_diag),
    }


def build_exchange_transition(
    population_total: np.ndarray,
    gene_flow: np.ndarray,
    intrinsic_ri: np.ndarray,
    current_species_index: np.ndarray,
    cfg: SegregationAwareAdmixtureConfig = SegregationAwareAdmixtureConfig(),
) -> tuple[np.ndarray, dict[str, Any]]:
    """Build the row-stochastic mean/allele-frequency mixing operator P.

    Edge construction and the 45% aggregate cap are deliberately identical to
    D3.3A `gene_flow_moment_mix`; only the variance semantics are changed.
    Reproductive identity is current-species-bound, matching R3.4.
    """
    n = np.maximum(np.asarray(population_total, dtype=float), 0.0)
    g = np.asarray(gene_flow, dtype=float)
    ri = np.asarray(intrinsic_ri, dtype=float)
    sid = np.asarray(current_species_index)
    nd = n.size
    if g.shape != (nd, nd) or ri.shape != (nd, nd) or sid.shape != (nd,):
        raise ValueError("exchange/RI/species shapes do not match population")
    if np.any(~np.isfinite(g)) or np.any(~np.isfinite(ri)):
        raise ValueError("gene flow and RI must be finite")

    edges: list[list[float | int]] = []
    outgoing = np.zeros(nd, dtype=float)
    for i in range(nd):
        if n[i] <= 0:
            continue
        for j in range(i + 1, nd):
            if sid[i] != sid[j] or n[j] <= 0:
                continue
            mix = float(g[i, j]) * (1.0 - float(ri[i, j]))
            if mix <= 0:
                continue
            harmonic = 2.0 * n[i] * n[j] / max(n[i] + n[j], 1e-30)
            exchange = max(0.0, mix * harmonic)
            if exchange <= 0:
                continue
            edges.append([i, j, exchange])
            outgoing[i] += exchange
            outgoing[j] += exchange

    p = np.eye(nd, dtype=float)
    total_exchange = 0.0
    max_out_fraction = 0.0
    for i, j, exchange0 in edges:
        i = int(i); j = int(j)
        si = 1.0 if outgoing[i] <= 0 else min(
            1.0, cfg.maximum_total_exchange_fraction_per_deme * n[i] / outgoing[i]
        )
        sj = 1.0 if outgoing[j] <= 0 else min(
            1.0, cfg.maximum_total_exchange_fraction_per_deme * n[j] / outgoing[j]
        )
        x = float(exchange0) * min(si, sj)
        if x <= 0:
            continue
        wi = x / n[i]
        wj = x / n[j]
        p[i, i] -= wi; p[i, j] += wi
        p[j, j] -= wj; p[j, i] += wj
        total_exchange += x
        max_out_fraction = max(max_out_fraction, wi, wj)

    if np.min(p) < -1e-12 or not np.allclose(p.sum(axis=1), 1.0, atol=1e-12, rtol=0.0):
        raise RuntimeError("derived exchange transition is not row-stochastic")
    # Symmetric mass exchange means the population-weighted stationary measure
    # is conserved even for unequal deme population sizes.
    mass_err = float(np.max(np.abs(n @ p - n))) if nd else 0.0
    if mass_err > 1e-8 * max(1.0, float(np.sum(n))):
        raise RuntimeError("exchange transition violates population-weighted mass closure")
    return p, {
        "edge_count": int(len(edges)),
        "total_pair_exchange_mass": float(total_exchange),
        "maximum_single_edge_out_fraction": float(max_out_fraction),
        "population_weighted_transition_closure_max_abs": mass_err,
    }


def transform_segregation_potential(
    potential: np.ndarray,
    transition: np.ndarray,
    *,
    tolerance: float = 1e-9,
) -> np.ndarray:
    """Advance latent trait-specific genetic distances under linear migration.

    Because S is a squared-Euclidean distance matrix, classical double
    centering recovers a Gram matrix of latent allele-frequency/effect vectors.
    Migration acts linearly on those vectors (X' = P X), so P B P^T gives the
    exact reduced-order update without reconstructing individual loci.
    """
    s = np.asarray(potential, dtype=float)
    p = np.asarray(transition, dtype=float)
    validate_segregation_potential(s, tolerance=tolerance)
    n, _, nt = s.shape
    if p.shape != (n, n):
        raise ValueError("transition shape mismatch")
    if np.min(p) < -tolerance or not np.allclose(p.sum(axis=1), 1.0, atol=tolerance, rtol=0.0):
        raise ValueError("transition must be row-stochastic")
    if n == 0:
        return s.copy()
    h = np.eye(n) - np.ones((n, n), dtype=float) / n
    out = np.empty_like(s)
    for t in range(nt):
        b = -0.5 * h @ s[:, :, t] @ h
        bp = p @ b @ p.T
        diag = np.diag(bp)
        d = diag[:, None] + diag[None, :] - 2.0 * bp
        d[np.abs(d) < 1e-14] = 0.0
        if np.min(d) < -10.0 * tolerance:
            raise RuntimeError("migration produced invalid segregation potential")
        d = np.maximum(d, 0.0)
        d = 0.5 * (d + d.T)
        np.fill_diagonal(d, 0.0)
        out[:, :, t] = d
    return out


def recombination_decay_factors(
    generation_time_years: np.ndarray,
    dt_years: float,
    recombination_fraction_per_generation: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Return retention of inherited and uniformly injected ancestry covariance.

    For pairwise LD/cross-locus covariance, recombination gives D'=(1-r)D per
    generation in the reference model.  Existing covariance therefore retains
    exp(-lambda*g).  For covariance injected continuously and uniformly across
    the interval, the exact average end-of-interval retention is
    (1-exp(-lambda*g))/(lambda*g).
    """
    gt = np.asarray(generation_time_years, dtype=float)
    if np.any(gt <= 0) or dt_years < 0:
        raise ValueError("generation times must be positive and dt non-negative")
    r = float(recombination_fraction_per_generation)
    if not (0.0 <= r <= 0.5):
        raise ValueError("recombination fraction must be in [0,0.5]")
    g = float(dt_years) / gt
    if r == 0.0 or dt_years == 0:
        return np.ones_like(gt), np.ones_like(gt)
    lam_g = -math.log1p(-r)
    x = lam_g * g
    inherited = np.exp(-x)
    uniform = np.ones_like(x)
    nz = x > 1e-12
    uniform[nz] = -np.expm1(-x[nz]) / x[nz]
    # series near zero
    uniform[~nz] = 1.0 - 0.5 * x[~nz]
    return inherited, uniform


def segregation_aware_gene_flow_mix(
    trait: np.ndarray,
    va_within: np.ndarray,
    ancestry_covariance: np.ndarray,
    segregation_potential: np.ndarray,
    population_total: np.ndarray,
    gene_flow: np.ndarray,
    intrinsic_ri: np.ndarray,
    current_species_index: np.ndarray,
    generation_time_years: np.ndarray,
    dt_years: float,
    cfg: SegregationAwareAdmixtureConfig = SegregationAwareAdmixtureConfig(),
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    """Segregation-aware replacement candidate for whole-trait moment mixing.

    Mean migration semantics are unchanged.  Persistent within-deme VA is
    updated from the pairwise segregation potential S, while the residual
    whole-trait mixture covariance is kept in a separate signed ancestry/LD
    reservoir and allowed to recombine away.

    R3.7 is a validation candidate: this function does not write canonical
    state and is not called by the production R3.5 runtime.
    """
    z = np.asarray(trait, dtype=float)
    v = np.maximum(np.asarray(va_within, dtype=float), 0.0)
    c = np.asarray(ancestry_covariance, dtype=float)
    s = np.asarray(segregation_potential, dtype=float)
    n = np.maximum(np.asarray(population_total, dtype=float), 0.0)
    gt = np.asarray(generation_time_years, dtype=float)
    if z.ndim != 2 or v.shape != z.shape or c.shape != z.shape:
        raise ValueError("trait/within VA/ancestry covariance shapes must match")
    nd, nt = z.shape
    if s.shape != (nd, nd, nt) or n.shape != (nd,) or gt.shape != (nd,):
        raise ValueError("segregation potential/population/generation-time shape mismatch")
    if np.any(~np.isfinite(z)) or np.any(~np.isfinite(v)) or np.any(~np.isfinite(c)):
        raise ValueError("state arrays must be finite")
    validate_segregation_potential(s, tolerance=cfg.euclidean_tolerance)

    p, flow_diag = build_exchange_transition(n, gene_flow, intrinsic_ri, current_species_index, cfg)
    z_new = p @ z

    # Exact genic-variance mixture using pairwise latent genetic distances.
    base_within = p @ v
    genic_injection = 0.5 * np.einsum("ij,ik,jkt->it", p, p, s, optimize=True)
    v_new = np.maximum(base_within + genic_injection, 0.0)

    # Whole-trait mixture variance, separated from the genic part.  The residual
    # is signed because cross-locus covariance/LD can be positive or negative.
    mean_mixture = p @ (z * z) - z_new * z_new
    ancestry_injection = mean_mixture - genic_injection
    ancestry_pre_recombination = p @ c + ancestry_injection

    inherited_retention, uniform_injection_retention = recombination_decay_factors(
        gt, dt_years, cfg.recombination_fraction_per_generation
    )
    c_new = (
        (p @ c) * inherited_retention[:, None]
        + ancestry_injection * uniform_injection_retention[:, None]
    )

    s_new = transform_segregation_potential(s, p, tolerance=cfg.euclidean_tolerance)

    # Before recombination, genic+ancestry reproduces exactly the old total
    # second-moment mixture, so the repair changes biological partitioning, not
    # transport of means or the instantaneous total mixture moment.
    total_before = v + c
    legacy_pre = p @ (total_before + z * z) - z_new * z_new
    repaired_pre = v_new + ancestry_pre_recombination
    pre_recomb_closure = float(np.max(np.abs(legacy_pre - repaired_pre))) if repaired_pre.size else 0.0

    first_before = (n[:, None] * z).sum(axis=0)
    first_after = (n[:, None] * z_new).sum(axis=0)
    diagnostics: dict[str, Any] = {
        **flow_diag,
        "first_moment_conservation_max_abs": float(np.max(np.abs(first_after - first_before))) if z.size else 0.0,
        "pre_recombination_total_variance_closure_max_abs": pre_recomb_closure,
        "genic_injection_total": np.sum(genic_injection, axis=0).tolist(),
        "ancestry_injection_total": np.sum(ancestry_injection, axis=0).tolist(),
        "ancestry_abs_before_recombination_total": np.sum(np.abs(ancestry_pre_recombination), axis=0).tolist(),
        "ancestry_abs_after_recombination_total": np.sum(np.abs(c_new), axis=0).tolist(),
        "recombination_fraction_per_generation": float(cfg.recombination_fraction_per_generation),
        "minimum_inherited_ancestry_retention": float(np.min(inherited_retention)) if inherited_retention.size else 1.0,
        "maximum_uniform_injection_retention": float(np.max(uniform_injection_retention)) if uniform_injection_retention.size else 1.0,
        "canonical_write_allowed": False,
        "production_runtime_bound": False,
    }
    return z_new, v_new, c_new, s_new, diagnostics
