from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import math
import numpy as np

MODES = ("E", "th", "p", "I", "N")
LATENT_TRAITS = (
    "coupling_E", "coupling_th", "coupling_p", "coupling_I", "coupling_N",
    "uptake", "regulation", "tolerance", "plasticity", "repair",
)
YEAR_S = 365.25 * 24.0 * 3600.0


def sigmoid(x):
    x = np.asarray(x, dtype=float)
    return 1.0 / (1.0 + np.exp(-x))


def phenotype_from_latent(latent: np.ndarray | Mapping[str, float]) -> dict[str, Any]:
    if isinstance(latent, Mapping):
        z = np.asarray([float(latent.get(k, 0.0)) for k in LATENT_TRAITS], dtype=float)
    else:
        z = np.asarray(latent, dtype=float)
        if z.shape[-1] != len(LATENT_TRAITS):
            raise ValueError("Deep latent vector must have 10 traits")
    return {
        "coupling": sigmoid(z[..., :5]),
        "uptake": sigmoid(z[..., 5]),
        "regulation": sigmoid(z[..., 6]),
        "tolerance": sigmoid(z[..., 7]),
        "plasticity": sigmoid(z[..., 8]),
        "repair": sigmoid(z[..., 9]),
    }


@dataclass(frozen=True)
class PassiveUptakeConfig:
    passive_max_fraction_per_restore_time: float = 0.01
    return_flow_fraction: float = 0.50
    regulation_load_reduction_gain: float = 0.60
    reference_pressure_floor: float = 1.0e-15

    def validate(self) -> None:
        if not (0.0 <= self.passive_max_fraction_per_restore_time <= 1.0):
            raise ValueError("invalid passive fraction")
        if not (0.0 <= self.return_flow_fraction <= 1.0):
            raise ValueError("invalid return fraction")
        if self.regulation_load_reduction_gain < 0.0:
            raise ValueError("invalid regulation gain")


@dataclass
class DemeDeepSidecar:
    """Deep state owned by the v0.6A wrapper, not by SEALED D3 source."""
    latent_mean: np.ndarray
    latent_additive_variance: np.ndarray
    acclimatization: np.ndarray
    remodeling: np.ndarray
    recoverable_load: np.ndarray
    injury: np.ndarray

    @classmethod
    def initialize(cls, n_demes: int, normalized_va: float = 0.012) -> "DemeDeepSidecar":
        if n_demes < 0 or normalized_va < 0:
            raise ValueError("invalid sidecar initialization")
        return cls(
            latent_mean=np.zeros((n_demes, 10), dtype=float),
            latent_additive_variance=np.full((n_demes, 10), float(normalized_va), dtype=float),
            acclimatization=np.zeros(n_demes, dtype=float),
            remodeling=np.zeros(n_demes, dtype=float),
            recoverable_load=np.zeros(n_demes, dtype=float),
            injury=np.zeros(n_demes, dtype=float),
        )


def contact_acceptance_by_deme_mode(
    latent_mean: np.ndarray,
    *,
    acclimatization: np.ndarray | float = 0.0,
    regulation_gain: float = 0.60,
) -> np.ndarray:
    """Dimensionless biological acceptance/contact response.

    No joule/individual or physical-individual conversion appears here.
    Shape: [deme, mode].
    """
    z = np.asarray(latent_mean, dtype=float)
    if z.ndim != 2 or z.shape[1] != 10:
        raise ValueError("latent_mean must be [deme,10]")
    ph = phenotype_from_latent(z)
    acc = np.asarray(acclimatization, dtype=float)
    if acc.ndim == 0:
        acc = np.full(z.shape[0], float(acc))
    if acc.shape != (z.shape[0],):
        raise ValueError("acclimatization shape mismatch")
    operating = 0.4 + 0.6 * np.clip(acc, 0.0, 1.0)
    divisor = 1.0 + float(regulation_gain) * ph["regulation"] * operating
    return np.maximum(ph["uptake"][:, None] * ph["coupling"] / divisor[:, None], 0.0)


def reference_acceptance_by_mode(regulation_gain: float = 0.60) -> np.ndarray:
    # v0.4 reference latent state is Z_X=0; sigmoid(0)=0.5.
    z = np.zeros((1, 10), dtype=float)
    return contact_acceptance_by_deme_mode(z, regulation_gain=regulation_gain)[0]


def biological_pressure(
    population: np.ndarray,
    reference_population: np.ndarray,
    deme_guild: np.ndarray,
    latent_mean: np.ndarray,
    *,
    acclimatization: np.ndarray | float = 0.0,
    regulation_gain: float = 0.60,
    floor: float = 1.0e-15,
) -> dict[str, np.ndarray]:
    """Map D3 population units to a dimensionless passive-acceptance pressure.

    population: [deme, y, x] in D3 WorldSim units.
    reference_population: [guild, y, x], used only as an opportunity/abundance
    normalization anchor. It is NOT K and NOT a physical N.

    The saturation B = D/(D+D*) is invariant if both D3 population and the
    reference anchor are rescaled by the same arbitrary unit factor.
    """
    pop = np.maximum(np.asarray(population, dtype=float), 0.0)
    ref = np.maximum(np.asarray(reference_population, dtype=float), 0.0)
    guild = np.asarray(deme_guild, dtype=int)
    if pop.ndim != 3:
        raise ValueError("population must be [deme,y,x]")
    if ref.ndim != 3 or ref.shape[1:] != pop.shape[1:]:
        raise ValueError("reference_population shape mismatch")
    if guild.shape != (pop.shape[0],):
        raise ValueError("deme_guild shape mismatch")
    if np.any((guild < 1) | (guild > ref.shape[0])):
        raise ValueError("guild id outside reference_population")

    theta = contact_acceptance_by_deme_mode(
        latent_mean, acclimatization=acclimatization, regulation_gain=regulation_gain
    )  # [d,5]
    # demand/acceptance pressure by site and mode
    demand = np.einsum("dyx,dm->myx", pop, theta, optimize=True)

    theta0 = reference_acceptance_by_mode(regulation_gain=regulation_gain)
    ref_total = np.sum(ref, axis=0)
    reference = theta0[:, None, None] * ref_total[None, :, :]
    # Avoid a zero denominator over cells with no environmental reference.
    # Such cells also cannot receive a biological pressure without explicit D3
    # population; if they do, floor makes the saturation tend to 1 but the
    # physical supply/accessibility gate still remains mandatory.
    denom = demand + np.maximum(reference, float(floor))
    saturation = np.divide(demand, denom, out=np.zeros_like(demand), where=denom > 0)
    saturation = np.clip(saturation, 0.0, 1.0)

    weights = pop[:, None, :, :] * theta[:, :, None, None]
    wsum = np.sum(weights, axis=0)
    allocation_fraction = np.divide(
        weights,
        wsum[None, :, :, :],
        out=np.zeros_like(weights),
        where=wsum[None, :, :, :] > 0,
    )
    return {
        "deme_mode_acceptance": theta,
        "mode_site_demand": demand,
        "mode_site_reference": reference,
        "mode_site_saturation": saturation,
        "deme_mode_site_allocation_fraction": allocation_fraction,
        "reference_population_semantics": np.asarray("NORMALIZATION_ANCHOR_NOT_K_NOT_PHYSICAL_N"),
    }


def local_passive_uptake_rate_per_year(
    saturation: np.ndarray,
    c_car_by_mode: np.ndarray,
    zeta_by_mode: np.ndarray,
    restore_time_years: np.ndarray,
    cfg: PassiveUptakeConfig,
) -> np.ndarray:
    """Bounded gross fractional rate lambda_gross [1/year]."""
    cfg.validate()
    sat = np.asarray(saturation, dtype=float)
    ccar = np.clip(np.asarray(c_car_by_mode, dtype=float), 0.0, 1.0)
    zeta = np.clip(np.asarray(zeta_by_mode, dtype=float), 0.0, 1.0)
    tau = np.asarray(restore_time_years, dtype=float)
    if sat.shape != ccar.shape or sat.shape != zeta.shape:
        raise ValueError("site field shape mismatch")
    if tau.shape not in ((5,), sat.shape):
        raise ValueError("restore_time_years must be [5] or site-shaped")
    if np.any(tau <= 0):
        raise ValueError("restore times must be positive")
    if tau.shape == (5,):
        tau = tau[:, None, None]
    conductance = np.clip(ccar * zeta, 0.0, 1.0)
    return cfg.passive_max_fraction_per_restore_time * np.clip(sat, 0.0, 1.0) * conductance / tau


def analytic_replenished_component_step(
    surface_energy_j: np.ndarray,
    equilibrium_energy_j: np.ndarray,
    restore_time_year: np.ndarray | float,
    lambda_gross_per_year: np.ndarray,
    dt_year: float,
    *,
    return_flow_fraction: float,
    finite_source_buffer_j: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Exact constant-coefficient surface reservoir + passive uptake step.

    dE/dt = (E_eq-E)/tau - (1-r)*lambda_gross*E

    The integral of E is analytic, so gross uptake, return, net sink and restore
    input close algebraically. If a finite source buffer is supplied and the
    exact restore demand exceeds it, the step FAILS CLOSED rather than inventing
    energy. A later production stage may replace this with a piecewise
    buffer-exhaustion solution.
    """
    E0 = np.maximum(np.asarray(surface_energy_j, dtype=float), 0.0)
    Eeq = np.maximum(np.asarray(equilibrium_energy_j, dtype=float), 0.0)
    lam = np.maximum(np.asarray(lambda_gross_per_year, dtype=float), 0.0)
    tau = np.asarray(restore_time_year, dtype=float)
    if np.any(tau <= 0) or dt_year < 0:
        raise ValueError("invalid time")
    r = float(return_flow_fraction)
    if not 0.0 <= r <= 1.0:
        raise ValueError("invalid return fraction")
    net_lam = (1.0 - r) * lam
    k = 1.0 / tau + net_lam
    Einf = (Eeq / tau) / k
    expk = np.exp(-k * float(dt_year))
    E1 = Einf + (E0 - Einf) * expk
    integral_E_year = Einf * float(dt_year) + (E0 - Einf) * (1.0 - expk) / k
    gross = lam * integral_E_year
    returned = r * gross
    net = gross - returned
    restored = Eeq * float(dt_year) / tau - integral_E_year / tau
    # Negative "restore" means ordinary relaxation exported energy because E0>Eeq.
    # Track it as dissipation/export rather than a negative source draw.
    source_input = np.maximum(restored, 0.0)
    relaxation_export = np.maximum(-restored, 0.0)
    if finite_source_buffer_j is not None:
        buf = np.maximum(np.asarray(finite_source_buffer_j, dtype=float), 0.0)
        if np.any(source_input > buf + 1e-9):
            raise RuntimeError("finite Deep source buffer exhausted: FAIL_CLOSED")
        buffer_after = buf - source_input
    else:
        buffer_after = np.full_like(E1, np.nan)
    closure = E0 + source_input + returned - gross - relaxation_export - E1
    return {
        "surface_energy_before_j": E0,
        "surface_energy_after_j": np.maximum(E1, 0.0),
        "gross_uptake_j": gross,
        "return_flow_j": returned,
        "net_biological_sink_j": net,
        "source_restore_input_j": source_input,
        "relaxation_export_j": relaxation_export,
        "source_buffer_after_j": buffer_after,
        "closure_error_j": closure,
    }


def analytic_decaying_component_step(
    surface_energy_j: np.ndarray,
    decay_time_year: float,
    lambda_gross_per_year: np.ndarray,
    dt_year: float,
    *,
    return_flow_fraction: float,
) -> dict[str, np.ndarray]:
    """Exact CHA-1-like decaying component with passive uptake."""
    E0 = np.maximum(np.asarray(surface_energy_j, dtype=float), 0.0)
    lam = np.maximum(np.asarray(lambda_gross_per_year, dtype=float), 0.0)
    if decay_time_year <= 0 or dt_year < 0:
        raise ValueError("invalid time")
    r = float(return_flow_fraction)
    k = 1.0 / float(decay_time_year) + (1.0-r)*lam
    e = np.exp(-k*float(dt_year))
    E1 = E0*e
    integral = E0*(1.0-e)/k
    gross = lam*integral
    returned = r*gross
    net = gross-returned
    dissipated = E0*(1.0-e)/(float(decay_time_year)*k)
    closure = E0 + returned - gross - dissipated - E1
    return {
        "surface_energy_before_j": E0,
        "surface_energy_after_j": E1,
        "gross_uptake_j": gross,
        "return_flow_j": returned,
        "net_biological_sink_j": net,
        "physical_decay_dissipation_j": dissipated,
        "closure_error_j": closure,
    }


def additive_photo_equilibrium_energy(
    base_background_energy_j: np.ndarray,
    photo_share: float = 0.05,
    photo_modes: tuple[str, ...] = ("E", "th"),
) -> np.ndarray:
    """5% additive photo-Deep candidate. Input mode axis order is MODES."""
    base = np.maximum(np.asarray(base_background_energy_j, dtype=float), 0.0)
    if base.shape[0] != 5:
        raise ValueError("mode axis must have length 5")
    if photo_share < 0:
        raise ValueError("photo_share must be nonnegative")
    out = np.zeros_like(base)
    for i,m in enumerate(MODES):
        if m in photo_modes:
            out[i] = float(photo_share)*base[i]
    return out


def deep_off_passthrough(value: Any, *, deep_enabled: bool) -> Any:
    """Hard bypass used by integration wrappers to guarantee Deep-OFF parity."""
    if deep_enabled:
        raise RuntimeError("deep_off_passthrough is only valid when Deep is disabled")
    return value


def apply_species_viability_to_d3_target(
    d3_target_population: Mapping[str, float],
    species_viability: Mapping[str, float],
    *,
    deep_enabled: bool,
) -> dict[str, float]:
    """Minimal sidecar target modifier; exact identity if Deep is OFF.

    It does not alter any D3 RI/speciation gate and is intentionally not wired
    into SEALED D3 source in v0.6A.
    """
    targets = {str(k): float(v) for k,v in d3_target_population.items()}
    if not deep_enabled:
        return targets
    out = {}
    for sid, target in targets.items():
        v = float(np.clip(species_viability.get(sid, 1.0), 0.0, 1.0))
        out[sid] = target*v
    return out


GOVERNANCE = {
    "D3_source_modified": False,
    "reference_population_is_K": False,
    "reference_population_is_physical_N": False,
    "drift_individual_equivalents_used_for_energy": False,
    "direct_Deep_speciation_operator": False,
    "directional_mutation_operator": False,
    "active_magic": False,
    "photo_deep_additive_share_E_th": 0.05,
}
