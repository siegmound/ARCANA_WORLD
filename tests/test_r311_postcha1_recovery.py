from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.scientific_engines import r311_postcha1_recovery as r311
from arcana_worldsim.scientific_engines.r39_precha1_continuation import R39Config


def test_parent_r310_authority_is_exact_sealed_boundary():
    a = r311.validate_parent_r310_authority(ROOT)
    st = a["state"]
    assert st.age_ma == 65.5
    assert st.elapsed_year == 144_500_000.0
    assert len(set(st.current_species)) == 93
    assert len(st.component_ids) == 207
    assert a["checkpoint_json_sha256"] == "5ea3f6cad09e2b6e09a6ff795a89dbd370ca0ca049f20c04e8d53fbeb8dd6469"
    assert a["checkpoint_npz_sha256"] == "d31ae5aaeb53422809e173c20308e69af334ef8d2d535484ae51141b9dff58a8"


def test_r311_scientific_parameters_are_parent_authority_not_retuned():
    cfg = r311.R311Config()
    parent = R39Config()
    fields = [
        "biology_cadence_years", "transport_cadence_years", "speciation_check_interval_years",
        "ordinary_extinction_check_interval_years", "founder_minimum_persistence_years",
        "vicariance_persistence_min_years", "reconnection_persistence_min_years",
        "mutation_variance_supply_normalized_per_myr", "nonlinear_stabilizing_variance_depletion_per_myr_per_q",
        "selection_variance_depletion_per_generation", "variance_ceiling_normalized",
        "migration_reference_years", "migration_fraction_ceiling", "gene_flow_ceiling_per_step",
        "minimum_effective_isolation_generations", "minimum_intrinsic_ri", "minimum_trait_distance",
        "maximum_effective_exchange_pressure", "adaptive_k_eff",
    ]
    for f in fields:
        assert getattr(cfg, f) == getattr(parent, f), f
    assert cfg.end_age_ma == 61.0
    assert cfg.adaptive_radiation_semantics.startswith("ORDINARY_R37I_R38")


def test_lifecycle_thaw_preserves_scientific_state_and_accumulated_persistence():
    parent = r311.validate_parent_r310_authority(ROOT)["state"]
    thawed, diag = r311.thaw_lifecycle_timers(parent)
    assert thawed.age_ma == parent.age_ma
    assert thawed.elapsed_year == parent.elapsed_year
    for name in ("guild", "pop", "trait", "va", "gen", "current_accessible"):
        assert np.array_equal(np.asarray(getattr(thawed, name)), np.asarray(getattr(parent, name)))
    for name in ("va_within", "ancestry_covariance", "neutral_segregation_potential", "adaptive_coordinate"):
        assert np.array_equal(np.asarray(getattr(thawed.reduced_state, name)), np.asarray(getattr(parent.reduced_state, name)))
    assert thawed.ri_state == parent.ri_state
    assert thawed.clock_state == parent.clock_state
    assert diag["shifted"] == {"founder": 3, "vicariance": 207, "reconnection": 2, "ordinary_extinction": 0}
    for key, old in parent.founder_state.items():
        new = thawed.founder_state[key]
        assert new["first_seen_elapsed_year"] == old["first_seen_elapsed_year"]
        assert new["continuous_persistence_years"] == old["continuous_persistence_years"]
        assert new["last_seen_elapsed_year"] == parent.elapsed_year
    for key, old in parent.reconnection_state.items():
        new = thawed.reconnection_state[key]
        assert new["first_seen_elapsed_year"] == old["first_seen_elapsed_year"]
        assert new["continuous_persistence_years"] == old["continuous_persistence_years"]
        assert new["last_seen_elapsed_year"] == parent.elapsed_year
    assert r311.event_counts(thawed)["post_CHA1_ordinary_lifecycle_thaw"] == 1
    assert r311.event_counts(thawed)["CHA1_species_extinction"] == 212


def test_lifecycle_thaw_does_not_mutate_parent():
    parent = r311.validate_parent_r310_authority(ROOT)["state"]
    founder_before = {k: dict(v) for k, v in parent.founder_state.items()}
    recon_before = {k: dict(v) for k, v in parent.reconnection_state.items()}
    _thawed, _diag = r311.thaw_lifecycle_timers(parent)
    assert parent.founder_state == founder_before
    assert parent.reconnection_state == recon_before
    assert r311.event_counts(parent)["post_CHA1_ordinary_lifecycle_thaw"] == 0


def test_canonical_window_is_exactly_plus_half_to_plus_five_myr_after_impact():
    assert r311.IMPACT_AGE_MA - r311.START_AGE_MA == 0.5
    assert r311.IMPACT_AGE_MA - r311.END_AGE_MA == 5.0
    assert int(round((r311.START_AGE_MA - r311.END_AGE_MA) * 1e6 / r311.R311Config().biology_cadence_years)) == 36
