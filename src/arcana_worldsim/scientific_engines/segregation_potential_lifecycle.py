from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence
import math

import numpy as np

from .segregation_aware_admixture import (
    validate_segregation_potential,
    transform_segregation_potential,
)


@dataclass(frozen=True)
class SegregationPotentialLifecycleConfig:
    """Governed lifecycle configuration for v0.6D1-R3.7A.

    `effective_polygenic_dimension` is *not* a World-1 production constant in
    R3.7A.  It is the explicit reduced-order participation number K_eff used to
    translate a known heritable directional trait response into the minimum
    trait-aligned segregation displacement

        dh = dz / sqrt(2 K_eff).

    The NEMO/QTL reference architecture uses 64 loci per trait.  Production
    binding remains fail-closed until the isolation/divergence/reconnection
    calibration is accepted.
    """

    effective_polygenic_dimension: float | None = None
    euclidean_tolerance: float = 1.0e-9

    def __post_init__(self) -> None:
        if self.effective_polygenic_dimension is not None and self.effective_polygenic_dimension <= 0:
            raise ValueError("effective_polygenic_dimension must be positive when provided")
        if self.euclidean_tolerance <= 0:
            raise ValueError("euclidean_tolerance must be positive")


@dataclass(frozen=True)
class ReducedGeneticLifecycleState:
    """R3.7A reduced genetic state; arrays are copied and made read-only."""

    va_within: np.ndarray
    ancestry_covariance: np.ndarray
    neutral_segregation_potential: np.ndarray
    adaptive_coordinate: np.ndarray

    def __post_init__(self) -> None:
        v = np.asarray(self.va_within, dtype=float)
        c = np.asarray(self.ancestry_covariance, dtype=float)
        sn = np.asarray(self.neutral_segregation_potential, dtype=float)
        h = np.asarray(self.adaptive_coordinate, dtype=float)
        if v.ndim != 2 or c.shape != v.shape or h.shape != v.shape:
            raise ValueError("VA/ancestry/adaptive arrays must be deme x trait and shape-matched")
        if sn.shape != (v.shape[0], v.shape[0], v.shape[1]):
            raise ValueError("neutral segregation potential must be deme x deme x trait")
        if np.any(~np.isfinite(v)) or np.any(v < -1e-12) or np.any(~np.isfinite(c)) or np.any(~np.isfinite(h)):
            raise ValueError("reduced genetic state contains invalid values")
        validate_segregation_potential(sn)
        for name, arr in (("va_within", v), ("ancestry_covariance", c),
                          ("neutral_segregation_potential", sn), ("adaptive_coordinate", h)):
            cp = np.array(arr, copy=True)
            cp.setflags(write=False)
            object.__setattr__(self, name, cp)

    @property
    def deme_count(self) -> int:
        return int(self.va_within.shape[0])

    @property
    def trait_count(self) -> int:
        return int(self.va_within.shape[1])

    @property
    def total_segregation_potential(self) -> np.ndarray:
        return compose_total_segregation_potential(
            self.neutral_segregation_potential, self.adaptive_coordinate
        )


def reproductive_pair_authority_mask(current_species: Sequence[str] | np.ndarray) -> np.ndarray:
    sid = np.asarray(current_species)
    if sid.ndim != 1:
        raise ValueError("current_species must be one-dimensional")
    mask = sid[:, None] == sid[None, :]
    np.fill_diagonal(mask, True)
    return mask


def initialize_minimum_information_state(
    va_within: np.ndarray,
    current_species: Sequence[str] | np.ndarray,
) -> tuple[ReducedGeneticLifecycleState, dict[str, Any]]:
    """Initialize R3.7A at the 210 Ma common state without hidden genomics.

    No authoritative pre-210 within-species allele-frequency divergence exists
    in the rebased common state.  Therefore same-current-species demes start at
    zero segregation distance. Cross-species entries are zero placeholders and
    explicitly non-authoritative; they are never licensed for gene flow.
    """
    v = np.asarray(va_within, dtype=float)
    sid = np.asarray(current_species)
    if v.ndim != 2 or sid.shape != (v.shape[0],):
        raise ValueError("state/species shape mismatch")
    n, t = v.shape
    state = ReducedGeneticLifecycleState(
        va_within=np.maximum(v, 0.0),
        ancestry_covariance=np.zeros_like(v),
        neutral_segregation_potential=np.zeros((n, n, t), dtype=float),
        adaptive_coordinate=np.zeros_like(v),
    )
    mask = reproductive_pair_authority_mask(sid)
    return state, {
        "semantic_status": "MINIMUM_INFORMATION_210MA_INITIALIZATION",
        "same_species_authoritative_pair_count": int(np.sum(np.triu(mask, 1))),
        "cross_species_pair_count_non_authoritative": int(np.sum(np.triu(~mask, 1))),
        "hidden_genomic_divergence_invented": False,
        "canonical_write_allowed": False,
        "production_runtime_bound": False,
    }


def compose_total_segregation_potential(
    neutral_potential: np.ndarray,
    adaptive_coordinate: np.ndarray,
) -> np.ndarray:
    sn = np.asarray(neutral_potential, dtype=float)
    h = np.asarray(adaptive_coordinate, dtype=float)
    if h.ndim != 2 or sn.shape != (h.shape[0], h.shape[0], h.shape[1]):
        raise ValueError("neutral/adaptive state shape mismatch")
    validate_segregation_potential(sn)
    dh = h[:, None, :] - h[None, :, :]
    s = sn + dh * dh
    validate_segregation_potential(s)
    return s


def advance_directional_selection_coordinate(
    adaptive_coordinate: np.ndarray,
    trait_before: np.ndarray,
    trait_after_selection: np.ndarray,
    *,
    effective_polygenic_dimension: float | Sequence[float] | np.ndarray,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Map an already-authorized heritable trait response into latent distance.

    For K_eff equally participating additive directions, the minimum-distance
    aligned polygenic response satisfies S = dz^2/(2 K_eff).  The function does
    not decide the trait response; it consumes the response already produced by
    ARCANA selection authority.  K_eff must be supplied explicitly.
    """
    h = np.asarray(adaptive_coordinate, dtype=float)
    z0 = np.asarray(trait_before, dtype=float)
    z1 = np.asarray(trait_after_selection, dtype=float)
    if h.shape != z0.shape or z1.shape != z0.shape:
        raise ValueError("adaptive/trait shape mismatch")
    k = np.asarray(effective_polygenic_dimension, dtype=float)
    if k.ndim == 0:
        k = np.full(h.shape[1], float(k))
    if k.shape != (h.shape[1],) or np.any(~np.isfinite(k)) or np.any(k <= 0):
        raise ValueError("effective_polygenic_dimension must be positive scalar or trait vector")
    dz = z1 - z0
    dh = dz / np.sqrt(2.0 * k[None, :])
    out = h + dh
    return out, {
        "trait_response_max_abs": float(np.max(np.abs(dz))) if dz.size else 0.0,
        "adaptive_coordinate_increment_max_abs": float(np.max(np.abs(dh))) if dh.size else 0.0,
        "effective_polygenic_dimension": k.tolist(),
        "mapping_semantics": "MINIMUM_DISTANCE_TRAIT_ALIGNED_POLYGENIC_RESPONSE",
        "production_calibration_authorized": False,
    }


def drift_retention_factor(
    effective_size: np.ndarray,
    generation_time_years: np.ndarray,
    dt_years: float,
) -> np.ndarray:
    ne = np.asarray(effective_size, dtype=float)
    gt = np.asarray(generation_time_years, dtype=float)
    if ne.shape != gt.shape or np.any(ne <= 0) or np.any(gt <= 0) or dt_years < 0:
        raise ValueError("invalid Ne/generation time/dt")
    return np.exp(-float(dt_years) / np.maximum(2.0 * ne * gt, 1e-300))


def advance_neutral_potential_by_drift(
    neutral_potential: np.ndarray,
    va_before_drift: np.ndarray,
    effective_size: np.ndarray,
    generation_time_years: np.ndarray,
    dt_years: float,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Expected finite-Ne transfer from within-deme VA to between-deme S.

    D3.3A uses lambda_drift = 1/(2 Ne g).  For a neutral additive locus this
    removes within-deme genic variance by the same exponential factor. The
    expected squared allele-frequency divergence of two independently drifting
    demes grows by the sum of the two lost within-deme VA contributions.  This
    therefore reuses the existing D3.3A drift authority, not a new drift rate.
    """
    sn = np.asarray(neutral_potential, dtype=float)
    v = np.asarray(va_before_drift, dtype=float)
    if v.ndim != 2 or sn.shape != (v.shape[0], v.shape[0], v.shape[1]):
        raise ValueError("drift state shape mismatch")
    validate_segregation_potential(sn)
    r = drift_retention_factor(np.asarray(effective_size, float), np.asarray(generation_time_years, float), dt_years)
    lost = np.maximum(v, 0.0) * (1.0 - r[:, None])
    out = sn.copy()
    for t in range(v.shape[1]):
        inc = lost[:, t, None] + lost[None, :, t]
        np.fill_diagonal(inc, 0.0)
        out[:, :, t] += inc
    validate_segregation_potential(out, tolerance=1e-8)
    return out, lost, {
        "drift_retention_min": float(np.min(r)) if r.size else 1.0,
        "drift_retention_max": float(np.max(r)) if r.size else 1.0,
        "within_va_expected_loss_total": np.sum(lost, axis=0).tolist(),
        "segregation_increment_semantics": "PAIR_INCREMENT_EQUALS_SUM_OF_D3_3A_EXPECTED_WITHIN_VA_DRIFT_LOSSES",
        "new_drift_rate_introduced": False,
    }


def mutation_supply_effect_on_segregation_potential(neutral_potential: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    """D3.3A mutation supply has zero deterministic directional S increment.

    The surviving D3.3A `mu` is a within-deme standing-variance supply, not a
    locus-frequency mutation matrix.  Mapping it to deterministic between-deme
    allele-frequency displacement would invent hidden genomic dynamics. Random
    between-deme divergence from finite populations is already handled through
    the drift transfer above.
    """
    sn = np.asarray(neutral_potential, dtype=float)
    validate_segregation_potential(sn)
    return sn.copy(), {
        "deterministic_segregation_increment": 0.0,
        "mu_changed": False,
        "semantics": "D3_3A_MUTATION_SUPPLY_IS_WITHIN_DEME_ONLY__NO_HIDDEN_ALLELE_FREQUENCY_DIRECTION_INVENTED",
    }


def transform_lifecycle_state_by_migration(
    state: ReducedGeneticLifecycleState,
    transition: np.ndarray,
) -> ReducedGeneticLifecycleState:
    p = np.asarray(transition, dtype=float)
    n = state.deme_count
    if p.shape != (n, n) or np.any(p < -1e-12) or not np.allclose(p.sum(axis=1), 1.0, atol=1e-12, rtol=0.0):
        raise ValueError("transition must be row-stochastic and match state")
    # VA/C are not advanced here: R3.7 owns their segregation-aware mixture.
    # This helper only advances the latent geometry used by the lifecycle model.
    sn = transform_segregation_potential(state.neutral_segregation_potential, p)
    h = p @ state.adaptive_coordinate
    return ReducedGeneticLifecycleState(
        va_within=state.va_within,
        ancestry_covariance=state.ancestry_covariance,
        neutral_segregation_potential=sn,
        adaptive_coordinate=h,
    )


def fission_clone_state(
    state: ReducedGeneticLifecycleState,
    parent_index: int,
) -> tuple[ReducedGeneticLifecycleState, dict[str, Any]]:
    """Clone reduced genetic state at an instantaneous deme fission.

    The daughter starts at the same latent genetic point as its parent. Thus the
    parent-daughter S is exactly zero at fission, while both have identical
    distances to every pre-existing deme. Divergence begins only after the split
    via drift, selection and/or later migration history.
    """
    n, t = state.deme_count, state.trait_count
    i = int(parent_index)
    if i < 0 or i >= n:
        raise IndexError("parent_index out of range")
    v = np.concatenate([state.va_within, state.va_within[i:i+1]], axis=0)
    c = np.concatenate([state.ancestry_covariance, state.ancestry_covariance[i:i+1]], axis=0)
    h = np.concatenate([state.adaptive_coordinate, state.adaptive_coordinate[i:i+1]], axis=0)
    sn = np.zeros((n+1, n+1, t), dtype=float)
    sn[:n, :n] = state.neutral_segregation_potential
    sn[n, :n] = state.neutral_segregation_potential[i, :, :]
    sn[:n, n] = state.neutral_segregation_potential[:, i, :]
    sn[n, n] = 0.0
    out = ReducedGeneticLifecycleState(v, c, sn, h)
    total = out.total_segregation_potential
    return out, {
        "parent_index": i,
        "daughter_index": n,
        "parent_daughter_segregation_max_abs": float(np.max(np.abs(total[i, n]))) if t else 0.0,
        "semantic_status": "EXACT_CLONAL_LATENT_STATE_AT_FISSION_INSTANT",
    }


def _barycenter_distance_to_external(s: np.ndarray, group: np.ndarray, weights: np.ndarray, k: int) -> float:
    # ||sum_i w_i x_i - x_k||^2 = sum_i w_i d_ik^2 - 1/2 sum_ij w_i w_j d_ij^2
    within = 0.5 * float(weights @ s[np.ix_(group, group)] @ weights)
    return float(weights @ s[group, k] - within)


def coalesce_group_state(
    state: ReducedGeneticLifecycleState,
    trait_mean: np.ndarray,
    population_mass: np.ndarray,
    group_indices: Iterable[int],
    *,
    survivor_index: int | None = None,
) -> tuple[ReducedGeneticLifecycleState, np.ndarray, np.ndarray, dict[str, Any]]:
    """Exact reduced-order pooling for persistent same-species coalescence.

    Returns (state, pooled_trait_mean_rows, retained_old_indices, diagnostics).
    The merged deme is a population-weighted latent barycenter. Its within VA
    receives the exact genic segregation term from total S; the residual whole-
    trait mixture variance enters signed ancestry/LD covariance, not persistent
    VA. No recombination is applied instantaneously at the event.
    """
    z = np.asarray(trait_mean, dtype=float)
    mass = np.asarray(population_mass, dtype=float)
    group = np.asarray(sorted(set(int(x) for x in group_indices)), dtype=int)
    n, t = state.deme_count, state.trait_count
    if z.shape != (n, t) or mass.shape != (n,) or np.any(mass < 0):
        raise ValueError("trait/mass shape mismatch")
    if group.size < 2 or np.any(group < 0) or np.any(group >= n):
        raise ValueError("coalescence group must contain >=2 valid demes")
    total_mass = float(np.sum(mass[group]))
    if total_mass <= 0:
        raise ValueError("cannot coalesce zero-mass group")
    w = mass[group] / total_mass
    survivor = int(group[0] if survivor_index is None else survivor_index)
    if survivor not in set(group.tolist()):
        raise ValueError("survivor must be in group")

    total_s = state.total_segregation_potential
    genic = 0.5 * np.einsum("i,j,ijt->t", w, w, total_s[np.ix_(group, group, np.arange(t))], optimize=True)
    pooled_va = w @ state.va_within[group] + genic
    pooled_mean = w @ z[group]
    mean_mix = w @ (z[group] * z[group]) - pooled_mean * pooled_mean
    pooled_c = w @ state.ancestry_covariance[group] + (mean_mix - genic)
    pooled_h = w @ state.adaptive_coordinate[group]

    keep = np.array([i for i in range(n) if i not in set(group.tolist()) or i == survivor], dtype=int)
    newpos = {old: p for p, old in enumerate(keep.tolist())}
    si = newpos[survivor]
    m = len(keep)
    sn = np.zeros((m, m, t), dtype=float)
    # copy unaffected distances first
    for a, oa in enumerate(keep):
        for b, ob in enumerate(keep):
            if oa == survivor or ob == survivor:
                continue
            sn[a, b] = state.neutral_segregation_potential[oa, ob]
    # exact latent barycenter distance for neutral subspace
    for b, ob in enumerate(keep):
        if ob == survivor:
            continue
        for ti in range(t):
            d = _barycenter_distance_to_external(state.neutral_segregation_potential[:, :, ti], group, w, int(ob))
            sn[si, b, ti] = sn[b, si, ti] = max(0.0, d)

    v = state.va_within[keep].copy(); v[si] = pooled_va
    c = state.ancestry_covariance[keep].copy(); c[si] = pooled_c
    h = state.adaptive_coordinate[keep].copy(); h[si] = pooled_h
    zout = z[keep].copy(); zout[si] = pooled_mean
    out = ReducedGeneticLifecycleState(v, c, sn, h)

    first_before = np.sum(mass[group, None] * z[group], axis=0)
    first_after = total_mass * pooled_mean
    return out, zout, keep, {
        "group_indices": group.tolist(),
        "survivor_old_index": survivor,
        "survivor_new_index": si,
        "population_total": total_mass,
        "first_moment_conservation_max_abs": float(np.max(np.abs(first_after - first_before))),
        "genic_segregation_increment": genic.tolist(),
        "ancestry_covariance_injection": (mean_mix - genic).tolist(),
        "event_semantics": "SEGREGATION_AWARE_PERSISTENT_SECONDARY_CONTACT_COALESCENCE",
        "despeciation_authorized": False,
    }


def speciation_identity_transition(
    state: ReducedGeneticLifecycleState,
    current_species: Sequence[str],
    daughter_indices: Iterable[int],
    daughter_species_id: str,
) -> tuple[ReducedGeneticLifecycleState, list[str], dict[str, Any]]:
    """Speciation changes reproductive identity but does not reset genetics."""
    sid = [str(x) for x in current_species]
    if len(sid) != state.deme_count:
        raise ValueError("species/state size mismatch")
    idx = sorted(set(int(x) for x in daughter_indices))
    if not idx or any(i < 0 or i >= state.deme_count for i in idx):
        raise ValueError("invalid daughter indices")
    before_s = state.total_segregation_potential.copy()
    before_v = state.va_within.copy()
    for i in idx:
        sid[i] = str(daughter_species_id)
    return state, sid, {
        "daughter_indices": idx,
        "daughter_species_id": str(daughter_species_id),
        "genetic_state_reset": False,
        "segregation_state_change_max_abs": float(np.max(np.abs(state.total_segregation_potential - before_s))),
        "va_state_change_max_abs": float(np.max(np.abs(state.va_within - before_v))),
        "cross_species_gene_flow_authorized": False,
        "future_coalescence_across_species_authorized": False,
    }


def remap_identity_transition(state: ReducedGeneticLifecycleState) -> tuple[ReducedGeneticLifecycleState, dict[str, Any]]:
    """Pure spatial support remapping leaves deme genetic identity unchanged."""
    return state, {
        "genetic_state_changed": False,
        "semantics": "PALEOGEOGRAPHIC_SUPPORT_REMAP_PRESERVES_DEME_GENETIC_IDENTITY",
    }


def remove_deme_state(state: ReducedGeneticLifecycleState, remove_indices: Iterable[int]) -> tuple[ReducedGeneticLifecycleState, np.ndarray]:
    rem = set(int(x) for x in remove_indices)
    keep = np.asarray([i for i in range(state.deme_count) if i not in rem], dtype=int)
    if any(i < 0 or i >= state.deme_count for i in rem):
        raise IndexError("remove index out of range")
    sn = state.neutral_segregation_potential[np.ix_(keep, keep, np.arange(state.trait_count))]
    return ReducedGeneticLifecycleState(
        state.va_within[keep], state.ancestry_covariance[keep], sn, state.adaptive_coordinate[keep]
    ), keep
