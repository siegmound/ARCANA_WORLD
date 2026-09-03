from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any
import numpy as np

from arcana_worldsim.post_cha1.paleogeographic_history import (
    build_transition_schedule,
    event_reconstructed_land_support,
)

STATUS = "PASS_LATE_CENOZOIC_30_0_PALEOGEOGRAPHIC_EVENT_RECONSTRUCTION_CANDIDATE"
PROVIDER = "PLATE_CORE_CONSTRAINED_ENDPOINT_EVENT_RECONSTRUCTION_A1_C2_2_30_0_MA"


@dataclass(frozen=True)
class LateCenozoicPaleogeographyConfig:
    older_ma: float = 30.0
    younger_ma: float = 0.0
    phase_min: float = 0.05
    phase_max: float = 0.95
    transition_width_years: float = 1_000_000.0
    recent_plate_freeze_start_ma: float = 0.12
    major_plate_speed_bound_cm_per_year: float = 7.0


def build_late_cenozoic_schedule(a1: Mapping[str, Any], cfg: LateCenozoicPaleogeographyConfig | None = None) -> dict:
    cfg = cfg or LateCenozoicPaleogeographyConfig()
    out = build_transition_schedule(
        a1,
        older_ma=cfg.older_ma,
        younger_ma=cfg.younger_ma,
        phase_min=cfg.phase_min,
        phase_max=cfg.phase_max,
    )
    out = dict(out)
    out["provider"] = PROVIDER
    out["status"] = STATUS
    out["semantic_status"] = (
        "DERIVED_ENDPOINT_CONSTRAINED_RECONSTRUCTION_NOT_INDEPENDENT_GEOLOGICAL_OBSERVATION"
    )
    out["recent_plate_freeze_displacement_bound_km"] = (
        cfg.recent_plate_freeze_start_ma * 1_000_000.0
        * cfg.major_plate_speed_bound_cm_per_year / 100_000.0
    )
    return out


def land_support_at_age(a1: Mapping[str, Any], age_ma: float,
                        cfg: LateCenozoicPaleogeographyConfig | None = None):
    cfg = cfg or LateCenozoicPaleogeographyConfig()
    support, sched = event_reconstructed_land_support(
        a1,
        float(age_ma),
        older_ma=cfg.older_ma,
        younger_ma=cfg.younger_ma,
        phase_min=cfg.phase_min,
        phase_max=cfg.phase_max,
        transition_width_years=cfg.transition_width_years,
    )
    return support, sched


def physical_paleogeography_state(a1: Mapping[str, Any], age_ma: float,
                                  cfg: LateCenozoicPaleogeographyConfig | None = None) -> dict:
    """Materialize only the governed late-Cenozoic terrestrial-support state.

    Climate, aridity, flora, sea-level/glacial corrections, and biological state are
    deliberately outside v0.6.4A.  Ages <= 0.12 Ma are expected to be handed to the
    sealed v0.6.1 recent-paleoclimate provider, with the 0 Ma tectonic raster frozen
    over that short interval subject to the documented displacement bound.
    """
    cfg = cfg or LateCenozoicPaleogeographyConfig()
    age = float(age_ma)
    if age < cfg.younger_ma - 1e-12 or age > cfg.older_ma + 1e-12:
        raise ValueError(f"Age {age} Ma outside v0.6.4A 30->0 Ma domain")
    support, sched = land_support_at_age(a1, age, cfg)
    return {
        "age_ma": age,
        "land_support": support,
        "accessible": support > 1e-9,
        "provider": PROVIDER,
        "status": STATUS,
        "event_diagnostics": sched["diagnostics"],
        "recent_paleoclimate_handoff_required": bool(age <= cfg.recent_plate_freeze_start_ma + 1e-12),
        "recent_paleoclimate_authority": "v0.6.1 SEALED_PALEOCLIMATE_HISTORY",
        "climate_materialized_by_v0_6_4A": False,
        "flora_materialized_by_v0_6_4A": False,
        "biology_materialized_by_v0_6_4A": False,
    }
