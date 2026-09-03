from __future__ import annotations

"""D3.3B2.0 heritable trophic-mode quantitative-genetics authority.

This module introduces one bounded continuous phenotype, ``tau``:

    tau = 0  -> plant-resource acquisition pole
    tau = 1  -> animal/prey-resource acquisition pole

D3.3B2.0 deliberately does *not* use tau to assign guilds or alter ecological
carrying/opportunity fields.  It is a latent heritable state only.  Mutation
adds additive variance and never directly moves the mean.  Mean direction is
provided solely by selection/resource opportunity and reproductive exchange.
"""

import math
import numpy as np

from . import diversification_adequacy as da

STATUS = "PASS_D3_3B2_0_HERITABLE_TROPHIC_MODE_QUANTITATIVE_GENETICS_CANDIDATE"


def initialize_state(deme_guild: np.ndarray, cfg):
    """Initialize tau from the already-existing trophic partition only.

    The poles are intentionally close to, but not exactly on, the mathematical
    boundaries so the bounded trait retains ordinary standing variation without
    a clipping-created mutation direction.
    """
    g = np.asarray(deme_guild, dtype=int)
    plant_anchor = float(cfg.trophic_mode_initial_plant_anchor)
    animal_anchor = float(cfg.trophic_mode_initial_animal_anchor)
    tau = np.where(g <= 4, plant_anchor, animal_anchor).astype(float)
    scale2 = max(float(cfg.trophic_mode_scale) ** 2, 1e-30)
    va = np.full(len(g), float(cfg.trophic_mode_initial_normalized_va) * scale2, dtype=float)
    return tau, va


def opportunity_targets(pop: np.ndarray, root_idx: np.ndarray, root_species_ids: list[str],
                        species_guild: np.ndarray, sub: dict, cfg) -> np.ndarray:
    """Return population-weighted local animal-resource opportunity in [0, 1].

    Plant and prey supports reuse the already-authorized D3.2A resource fields.
    Each constituent field is robustly normalized by the existing resource
    provider before the two trophic channels are compared.  The result is an
    *candidate environmental selection target*, not a guild label or a transition trigger.
    D3.3B2.0 does not activate this target in the world replay because the
    normalized forage and prey channels do not yet share a calibrated energetic
    currency; it is retained only for diagnostics and B2.1 design work.
    """
    nspecies = len(root_species_ids)
    sp = da.ar._root_species_population(pop, root_idx, nspecies)
    plants, prey = da._resource_fields(sp, species_guild, sub)
    plant_support = np.mean(plants, axis=0)
    animal_support = np.mean(prey, axis=0)
    den = plant_support + animal_support
    local = np.divide(animal_support, den, out=np.full_like(den, 0.5), where=den > 1e-15)

    targets = np.full(len(pop), np.nan, dtype=float)
    for i in range(len(pop)):
        p = np.maximum(np.asarray(pop[i], dtype=float), 0.0)
        n = float(p.sum())
        if n > 0.0:
            targets[i] = float(np.sum(p * local) / n)
    return np.clip(targets, 0.0, 1.0)


def selection_update(tau: np.ndarray, va: np.ndarray, targets: np.ndarray,
                     root_idx: np.ndarray, root_species_ids: list[str], metadata: dict,
                     dt_years: float, cfg) -> np.ndarray:
    """Exact local response toward resource opportunity for fixed VA over dt.

    d tau / dt = k q (target - tau), where q is normalized additive variance.
    Mutation is absent from this operator and therefore cannot move tau.
    """
    if bool(getattr(cfg, "trophic_mode_common_currency_enabled", False)):
        return _b21_selection_update(tau, va, targets, root_idx, root_species_ids, metadata, dt_years, cfg)

    out = np.asarray(tau, dtype=float).copy()
    scale2 = max(float(cfg.trophic_mode_scale) ** 2, 1e-30)
    timescale = max(float(cfg.trophic_mode_response_timescale_years), 1e-30)
    dt = max(float(dt_years), 0.0)
    for i, si0 in enumerate(root_idx):
        if not np.isfinite(targets[i]):
            continue
        sid = root_species_ids[int(si0)]
        rel = max(float(metadata[sid]["relative_reproduction_rate"]), 1e-9)
        q = max(float(va[i]) / scale2, 0.0)
        rate = rel * q / timescale
        retention = math.exp(-rate * dt)
        out[i] = float(targets[i]) + (float(out[i]) - float(targets[i])) * retention
    return np.clip(out, 0.0, 1.0)


def advance_variance(va: np.ndarray, tau_before: np.ndarray, targets: np.ndarray,
                     populations: np.ndarray, generation_time: np.ndarray,
                     dt_years: float, cfg) -> np.ndarray:
    """Exact Riccati homeostasis for normalized trophic-mode additive variance.

    dq/dt = mu - a q - b q^2

    ``a`` contains selection depletion, deterministic finite-population drift
    depletion, and any baseline stabilizing depletion.  Mutation contributes
    only ``mu`` and never a mean increment.
    """
    out = np.asarray(va, dtype=float).copy()
    scale = max(float(cfg.trophic_mode_scale), 1e-15)
    scale2 = scale * scale
    dt = max(float(dt_years), 0.0)
    legacy_mu = max(float(cfg.trophic_mode_mutation_variance_supply_normalized_per_myr), 0.0) / 1_000_000.0
    b = max(float(cfg.trophic_mode_nonlinear_stabilizing_variance_depletion_per_myr_per_q), 0.0) / 1_000_000.0
    qceil = max(float(cfg.trophic_mode_variance_ceiling_normalized), 0.0)

    for i in range(len(out)):
        q0 = max(float(out[i]) / scale2, 0.0)
        gt = max(float(generation_time[i]), 1e-9)
        pressure = 0.0
        if np.isfinite(targets[i]):
            if bool(getattr(cfg, "trophic_mode_common_currency_enabled", False)):
                # In B2.1 ``targets`` carries the net directional selection signal
                # in log-opportunity units, not a direct trait target.
                pressure = min((float(targets[i]) / max(float(cfg.trophic_mode_selection_signal_scale), 1e-30)) ** 2,
                               float(cfg.trophic_mode_selection_pressure_ceiling))
            else:
                pressure = min(((float(targets[i]) - float(tau_before[i])) / scale) ** 2,
                               float(cfg.trophic_mode_selection_pressure_ceiling))
        selection_lambda = max(float(cfg.trophic_mode_selection_variance_depletion_per_generation), 0.0) * pressure / gt
        ne = max(
            float(cfg.drift_min_effective_size),
            max(float(populations[i]), 0.0) * float(cfg.drift_individual_equivalents_per_population_unit),
        )
        drift_lambda = 1.0 / max(2.0 * ne * gt, 1e-30)
        baseline_lambda = max(float(cfg.trophic_mode_baseline_stabilizing_variance_depletion_per_generation), 0.0) / gt
        a = selection_lambda + drift_lambda + baseline_lambda
        mu = legacy_mu

        if b <= 0.0:
            if a < 1e-24:
                qn = q0 + mu * dt
            else:
                ret = math.exp(-a * dt)
                qn = q0 * ret + (mu / a) * (1.0 - ret)
        else:
            disc = math.sqrt(max(a * a + 4.0 * b * mu, 0.0))
            if disc < 1e-24:
                qn = q0
            else:
                rp = (-a + disc) / (2.0 * b)
                rn = (-a - disc) / (2.0 * b)
                den0 = q0 - rn
                c0 = 0.0 if abs(den0) < 1e-30 else (q0 - rp) / den0
                c = c0 * math.exp(-disc * dt)
                den = 1.0 - c
                qn = rp if abs(den) < 1e-30 else (rp - c * rn) / den
        out[i] = min(max(qn, 0.0), qceil) * scale2
    return out



def common_opportunity_currency(pop: np.ndarray, root_idx: np.ndarray, root_species_ids: list[str],
                                species_guild: np.ndarray, sub: dict, cfg,
                                current_species: list[str] | None = None,
                                current_guild: np.ndarray | None = None):
    """Return plant/animal opportunity in one WorldSim support currency.

    B2.3 may build the prey field from *current functional guilds* rather than
    immutable D1/root guilds, and may exclude the focal species from its own prey
    opportunity.  This prevents a plant lineage that is evolving animal-ward from
    being selected to eat itself.  Cannibalism is deliberately not an authority in
    this layer.  With the B2.3 switches OFF, the exact B2.1 legacy semantics are
    retained.
    """
    use_current = bool(getattr(cfg, "trophic_mode_current_functional_prey_field_enabled", False)) \
        and current_guild is not None and len(current_guild) == len(pop)
    exclude_self = bool(getattr(cfg, "trophic_mode_exclude_same_species_from_prey_opportunity", False)) \
        and current_species is not None and len(current_species) == len(pop)

    own_herbivore = {}
    if use_current:
        current_herbivores = np.zeros_like(np.asarray(pop[0], dtype=float))
        for i in range(len(pop)):
            if int(current_guild[i]) <= 4:
                q = np.maximum(np.asarray(pop[i], dtype=float), 0.0)
                current_herbivores += q
                if exclude_self:
                    sid = str(current_species[i])
                    own_herbivore[sid] = own_herbivore.get(sid, np.zeros_like(q)) + q
    else:
        nspecies = len(root_species_ids)
        sp = da.ar._root_species_population(pop, root_idx, nspecies)
        sg = np.asarray(species_guild, dtype=int)
        current_herbivores = np.maximum(sp[sg <= 4].sum(axis=0), 0.0)

    forage = np.maximum(np.asarray(sub["total_edible_forage"], dtype=float), 0.0)
    ref = np.asarray(sub["reference_population"], dtype=float)
    reference_herbivores = np.maximum(ref[:4].sum(axis=0), 0.0)
    accessible = np.asarray(sub.get("accessible", np.ones_like(forage, dtype=bool)), dtype=bool)

    forage_total = float(np.sum(forage[accessible]))
    href_total = float(np.sum(reference_herbivores[accessible]))
    plant_to_support = href_total / max(forage_total, 1e-30)
    plant_field = plant_to_support * forage

    positive_ref = reference_herbivores[accessible & (reference_herbivores > 0.0)]
    reference_scale = float(np.mean(positive_ref)) if positive_ref.size else 1.0
    floor = max(float(cfg.trophic_mode_common_support_floor_fraction), 0.0) * max(reference_scale, 1e-30)
    clip_log = max(float(cfg.trophic_mode_log_opportunity_clip), 0.0)

    nd = len(pop)
    plant_support = np.full(nd, np.nan, dtype=float)
    animal_support = np.full(nd, np.nan, dtype=float)
    log_ratio = np.full(nd, np.nan, dtype=float)
    animal_share = np.full(nd, np.nan, dtype=float)
    for i in range(nd):
        p = np.maximum(np.asarray(pop[i], dtype=float), 0.0)
        n = float(p.sum())
        if n <= 0.0:
            continue
        w = p / n
        P = float(np.sum(w * plant_field))
        animal_field = current_herbivores
        if use_current and exclude_self:
            animal_field = np.maximum(current_herbivores - own_herbivore.get(str(current_species[i]), 0.0), 0.0)
        A = float(np.sum(w * animal_field))
        plant_support[i] = P
        animal_support[i] = A
        Pr = P + floor
        Ar = A + floor
        lr = math.log(max(Ar, 1e-300) / max(Pr, 1e-300))
        log_ratio[i] = float(np.clip(lr, -clip_log, clip_log)) if clip_log > 0.0 else lr
        animal_share[i] = Ar / max(Ar + Pr, 1e-300)

    diag = {
        "plant_to_reference_support_factor": plant_to_support,
        "global_reference_herbivore_support": href_total,
        "global_edible_forage": forage_total,
        "regularization_floor_support_units": floor,
        "current_functional_prey_field_enabled": bool(use_current),
        "focal_same_species_prey_excluded": bool(use_current and exclude_self),
        "currency_semantics": "REFERENCE_EQUIVALENT_HERBIVORE_SUPPORT_NOT_PHYSICAL_JOULES_NOT_DEMOGRAPHIC_K",
    }
    return plant_support, animal_support, log_ratio, animal_share, diag


def specialization_signal(tau: np.ndarray, cfg) -> np.ndarray:
    """Intrinsic symmetric specialization landscape with stable historical anchors.

    For equal plant/animal opportunity the initialized plant and animal anchors are
    exact equilibria, while 0.5 is an unstable separator.  The maximum restoring
    magnitude between an anchor and 0.5 equals
    ``trophic_mode_specialization_barrier_log_ratio``.  Therefore an opposite-mode
    opportunity advantage must exceed that barrier to drive a complete crossing;
    ordinary mixed environments do not create an omnivory attractor.
    """
    z = np.asarray(tau, dtype=float)
    a = float(cfg.trophic_mode_initial_plant_anchor)
    b = float(cfg.trophic_mode_initial_animal_anchor)
    mid = 0.5 * (a + b)
    half = max(0.5 * (b - a), 1e-12)
    x = (z - mid) / half
    # max |x(1-x^2)| on [-1,1] is 2/(3*sqrt(3)).
    norm = 2.0 / (3.0 * math.sqrt(3.0))
    B = max(float(cfg.trophic_mode_specialization_barrier_log_ratio), 0.0)
    return B * x * (1.0 - x * x) / norm


def directional_selection_signal(tau: np.ndarray, log_opportunity_ratio: np.ndarray, cfg) -> np.ndarray:
    """Net state-derived selection signal in log-opportunity units."""
    lr = np.asarray(log_opportunity_ratio, dtype=float)
    sig = lr + specialization_signal(tau, cfg)
    lim = max(float(cfg.trophic_mode_selection_signal_clip), 0.0)
    if lim > 0.0:
        sig = np.clip(sig, -lim, lim)
    return sig


def _b21_selection_update(tau: np.ndarray, va: np.ndarray, log_opportunity_ratio: np.ndarray,
                          root_idx: np.ndarray, root_species_ids: list[str], metadata: dict,
                          dt_years: float, cfg) -> np.ndarray:
    """Continuous-time B2.1 directional response integrated with bounded RK4.

    Mutation is absent.  Opportunity is held fixed over the outer ecological
    step, while the specialization term is reevaluated as tau moves.  Internal
    integration uses a fixed physical-time ceiling rather than frame count, so
    changing the outer geological timestep does not redefine the biology.
    """
    out = np.asarray(tau, dtype=float).copy()
    scale2 = max(float(cfg.trophic_mode_scale) ** 2, 1e-30)
    timescale = max(float(cfg.trophic_mode_response_timescale_years), 1e-30)
    dt = max(float(dt_years), 0.0)
    max_h = max(float(cfg.trophic_mode_selection_internal_max_step_years), 1.0)
    nsub = max(1, int(math.ceil(dt / max_h))) if dt > 0.0 else 1
    h = dt / nsub if nsub else 0.0

    for i, si0 in enumerate(root_idx):
        if not np.isfinite(log_opportunity_ratio[i]) or h <= 0.0:
            continue
        sid = root_species_ids[int(si0)]
        rel = max(float(metadata[sid]["relative_reproduction_rate"]), 1e-9)
        q = max(float(va[i]) / scale2, 0.0)
        prefactor = rel * q / timescale
        L = float(log_opportunity_ratio[i])

        def rhs(z):
            zz = np.asarray([z], dtype=float)
            return prefactor * float(directional_selection_signal(zz, np.asarray([L]), cfg)[0])

        z = float(out[i])
        for _ in range(nsub):
            k1 = rhs(z)
            k2 = rhs(z + 0.5 * h * k1)
            k3 = rhs(z + 0.5 * h * k2)
            k4 = rhs(z + h * k3)
            z += (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
            z = float(np.clip(z, 0.0, 1.0))
        out[i] = z
    return out


def time_scaled_gene_flow_matrix(gene_flow: np.ndarray, intrinsic_ri: np.ndarray,
                                 dt_years: float, reference_step_years: float) -> np.ndarray:
    """Convert the legacy per-step exchange pressure to an equivalent dt fraction.

    Existing WorldSim contact/gene-flow calibration exports a fraction per
    numerical step.  B2 must survive adaptive temporal resolution, so the new
    trophic trait interprets that fraction at an explicit reference interval and
    compounds it continuously: m(dt)=1-(1-m_ref)^(dt/dt_ref).  We return a
    matrix that, after the existing (1-RI) factor inside the moment mixer, yields
    that time-scaled effective exchange.
    """
    g=np.clip(np.asarray(gene_flow,dtype=float),0.0,1.0)
    ri=np.clip(np.asarray(intrinsic_ri,dtype=float),0.0,1.0)
    ref=max(float(reference_step_years),1e-30); dt=max(float(dt_years),0.0)
    avail=1.0-ri
    mref=np.clip(g*avail,0.0,1.0-1e-15)
    mdt=1.0-np.power(1.0-mref,dt/ref)
    out=np.divide(mdt,avail,out=np.zeros_like(mdt),where=avail>1e-15)
    np.fill_diagonal(out,0.0)
    return np.clip(out,0.0,1.0)

def equilibrium_q(cfg, *, population_units: float = 1e9, generation_time_years: float = 5.0,
                  selection_pressure: float = 0.0) -> float:
    """Analytical local equilibrium diagnostic under fixed coefficients."""
    gt = max(float(generation_time_years), 1e-9)
    ne = max(float(cfg.drift_min_effective_size), float(population_units) * float(cfg.drift_individual_equivalents_per_population_unit))
    a = (
        max(float(cfg.trophic_mode_selection_variance_depletion_per_generation), 0.0) * max(float(selection_pressure), 0.0) / gt
        + 1.0 / max(2.0 * ne * gt, 1e-30)
        + max(float(cfg.trophic_mode_baseline_stabilizing_variance_depletion_per_generation), 0.0) / gt
    )
    mu = max(float(cfg.trophic_mode_mutation_variance_supply_normalized_per_myr), 0.0) / 1_000_000.0
    b = max(float(cfg.trophic_mode_nonlinear_stabilizing_variance_depletion_per_myr_per_q), 0.0) / 1_000_000.0
    if b <= 0.0:
        return float(mu / a) if a > 0 else float("inf")
    return float((-a + math.sqrt(max(a * a + 4.0 * b * mu, 0.0))) / (2.0 * b))
