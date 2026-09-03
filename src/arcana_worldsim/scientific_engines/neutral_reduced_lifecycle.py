from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .segregation_aware_admixture import (
    transform_segregation_potential,
    validate_segregation_potential,
)


@dataclass(frozen=True)
class NeutralLifecycleStepResult:
    va_within: np.ndarray
    segregation_potential: np.ndarray
    diagnostics: dict[str, Any]

    def __post_init__(self) -> None:
        v = np.asarray(self.va_within, dtype=float)
        s = np.asarray(self.segregation_potential, dtype=float)
        if v.ndim != 2 or s.shape != (v.shape[0], v.shape[0], v.shape[1]):
            raise ValueError("neutral lifecycle state shape mismatch")
        if np.any(~np.isfinite(v)) or np.any(v < -1e-12):
            raise ValueError("invalid VA state")
        validate_segregation_potential(s, tolerance=1e-8)
        vv = np.maximum(v, 0.0).copy(); vv.setflags(write=False)
        ss = s.copy(); ss.setflags(write=False)
        object.__setattr__(self, "va_within", vv)
        object.__setattr__(self, "segregation_potential", ss)


def _validate_transition(transition: np.ndarray, n: int) -> np.ndarray:
    p = np.asarray(transition, dtype=float)
    if p.shape != (n, n) or np.any(~np.isfinite(p)) or np.min(p) < -1e-12:
        raise ValueError("transition must be finite non-negative square matrix")
    if not np.allclose(p.sum(axis=1), 1.0, atol=1e-12, rtol=0.0):
        raise ValueError("transition must be row-stochastic")
    return p


def advance_neutral_one_generation(
    va_within: np.ndarray,
    segregation_potential: np.ndarray,
    transition: np.ndarray,
    effective_size: np.ndarray | float,
) -> NeutralLifecycleStepResult:
    """Exact reduced first/second-moment recursion for neutral WF migration+drift.

    State closure is exact for additive diallelic allele-frequency moments:

      1. migration mixes allele frequencies linearly;
      2. genic VA receives the exact segregation term from S;
      3. Wright-Fisher sampling loses VA_i/(2 N_e,i);
      4. the same lost VA is transferred to pairwise S as independent drift
         displacement, i.e. loss_i + loss_j.

    Recombination does not alter allele frequencies or genic VA/S and therefore
    does not enter this neutral frequency-state recursion.  It acts only on the
    separate ancestry/LD covariance reservoir owned by R3.7.
    """
    v = np.asarray(va_within, dtype=float)
    s = np.asarray(segregation_potential, dtype=float)
    if v.ndim != 2 or s.shape != (v.shape[0], v.shape[0], v.shape[1]):
        raise ValueError("VA/S shape mismatch")
    if np.any(v < -1e-12) or np.any(~np.isfinite(v)):
        raise ValueError("invalid VA")
    validate_segregation_potential(s, tolerance=1e-8)
    n, t = v.shape
    p = _validate_transition(transition, n)
    ne = np.asarray(effective_size, dtype=float)
    if ne.ndim == 0:
        ne = np.full(n, float(ne))
    if ne.shape != (n,) or np.any(~np.isfinite(ne)) or np.any(ne <= 0):
        raise ValueError("effective_size must be positive scalar or per-deme vector")

    genic_injection = 0.5 * np.einsum("ij,ik,jkt->it", p, p, s, optimize=True)
    va_after_migration = p @ v + genic_injection
    s_after_migration = transform_segregation_potential(s, p, tolerance=1e-8)

    drift_loss = va_after_migration / (2.0 * ne[:, None])
    va_after_drift = np.maximum(va_after_migration - drift_loss, 0.0)
    s_after_drift = s_after_migration.copy()
    for ti in range(t):
        inc = drift_loss[:, ti, None] + drift_loss[None, :, ti]
        np.fill_diagonal(inc, 0.0)
        s_after_drift[:, :, ti] += inc
    validate_segregation_potential(s_after_drift, tolerance=1e-7)

    # In this neutral closed system the population-summed genic information is
    # redistributed between within-deme VA and between-deme squared distance;
    # no empirical coefficient is introduced.
    return NeutralLifecycleStepResult(
        va_after_drift,
        s_after_drift,
        {
            "migration_genic_injection_total": np.sum(genic_injection, axis=0).tolist(),
            "drift_va_loss_total": np.sum(drift_loss, axis=0).tolist(),
            "minimum_drift_retention_one_generation": float(np.min(1.0 - 1.0/(2.0*ne))),
            "maximum_drift_retention_one_generation": float(np.max(1.0 - 1.0/(2.0*ne))),
            "new_drift_coefficient_introduced": False,
            "recombination_changes_frequency_state": False,
            "canonical_write_allowed": False,
        },
    )


def advance_neutral_generations(
    va_within: np.ndarray,
    segregation_potential: np.ndarray,
    transition: np.ndarray,
    effective_size: np.ndarray | float,
    generations: int,
) -> NeutralLifecycleStepResult:
    """Iterate the exact generation-scale reduced recursion used by NEMO B2."""
    g = int(generations)
    if g < 0 or g != generations:
        raise ValueError("generations must be a non-negative integer")
    v = np.asarray(va_within, dtype=float).copy()
    s = np.asarray(segregation_potential, dtype=float).copy()
    total_mig = np.zeros(v.shape[1], dtype=float)
    total_drift = np.zeros(v.shape[1], dtype=float)
    last_diag: dict[str, Any] = {}
    for _ in range(g):
        step = advance_neutral_one_generation(v, s, transition, effective_size)
        v = np.asarray(step.va_within)
        s = np.asarray(step.segregation_potential)
        total_mig += np.asarray(step.diagnostics["migration_genic_injection_total"], dtype=float)
        total_drift += np.asarray(step.diagnostics["drift_va_loss_total"], dtype=float)
        last_diag = step.diagnostics
    return NeutralLifecycleStepResult(
        v,
        s,
        {
            **last_diag,
            "generations": g,
            "cumulative_migration_genic_injection_total": total_mig.tolist(),
            "cumulative_drift_va_loss_total": total_drift.tolist(),
            "semantics": "EXACT_NEUTRAL_WRIGHT_FISHER_FREQUENCY_MOMENT_RECURSION",
            "canonical_write_allowed": False,
        },
    )
