from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pytest

from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
from arcana_worldsim.scientific_engines import r313_longterm_postcha1_reassembly as r313
from arcana_worldsim.scientific_engines import r315_late_cenozoic_secular_biology as r315

ROOT = Path(__file__).resolve().parents[1]


def _metadata_rows():
    data = json.loads((ROOT / "references/v0_6D1_R3/D1_SPECIES_METADATA.json").read_text(encoding="utf-8"))
    return data["species"] if isinstance(data, dict) and "species" in data else data


def _a1():
    return np.load(ROOT / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz", allow_pickle=False)


def _parent_state():
    return r313.load_checkpoint(
        ROOT / "local_runs/v0_6D1_R3_13/WORLD1_H0_30Ma_LONG_TERM_POST_CHA1_DIVERSIFICATION_REASSEMBLY_CHECKPOINT_v0_6D1_R3_13.json"
    )


class OldProviderProxy:
    """Test-only provider that reproduces the pre-R3.14 D3 environment exactly."""
    def __init__(self, a1, cfg):
        self.a1 = a1
        self.cfg = cfg
        self._environment_at = r38.bp.environment_at

    def state_at(self, age_ma: float):
        return self._environment_at(float(age_ma), self.a1, r38.r34.barrier_cfg(self.cfg))


def test_config_freezes_250ka_prebridge_boundary():
    cfg = r315.R315Config()
    assert cfg.biology_cadence_years == 125_000.0
    assert cfg.end_age_ma == 0.25
    assert cfg.adaptive_clock_used_as_biology_timestep is False


def test_config_rejects_changed_endpoint():
    with pytest.raises(ValueError):
        r315.R315Config(end_age_ma=0.125)


def test_scheduler_separation_stops_before_200ka_bridge():
    fake_clock = {"age_ma": np.asarray([30.0, 0.2, 0.12, 0.0])}
    rep = r315.biology_scheduler_separation_report(fake_clock)
    assert rep["biology_interval_count"] == 238
    assert rep["biology_checkpoint_count"] == 239
    assert rep["biology_end_age_ma"] == 0.25
    assert rep["all_r315_biology_checkpoints_older_than_c2_bridge_start"] is True
    assert rep["c2_200_120ka_bridge_crossed"] is False
    assert rep["next_nominal_biology_checkpoint_age_ma"] == 0.125
    assert rep["next_nominal_biology_step_would_cross_c2_200ka_bridge_start"] is True


def test_adapter_refuses_c2_bridge_and_recent_domain():
    a1 = _a1(); cfg = r315.R315Config(); proxy = OldProviderProxy(a1, cfg)
    ad = r315.R315D3EnvironmentAdapter(a1, proxy)
    with pytest.raises(ValueError):
        ad.state_at_age(0.2)
    with pytest.raises(ValueError):
        ad.state_at_age(0.12)


def test_adapter_emits_d3_schema_and_fixed_cadence_semantics():
    a1 = _a1(); cfg = r315.R315Config(); proxy = OldProviderProxy(a1, cfg)
    ad = r315.R315D3EnvironmentAdapter(a1, proxy)
    env = ad.state_at_age(29.875)
    for key in ("land_support", "accessible", "temperature_c", "aridity_index", "browse_forage", "low_forage", "wetland_forage", "total_edible_forage", "reference_population"):
        assert key in env
    assert env["adaptive_clock_checkpoint_promoted_to_biology_step"] is False
    assert env["biology_forcing_sample_semantics"] == "ENDPOINT_STATE_ON_FIXED_125KYR_R38_CADENCE"


def test_30ma_full_d3_substrate_is_exact_for_proxy():
    a1 = _a1(); cfg = r315.R315Config(); proxy = OldProviderProxy(a1, cfg)
    rep = r315.validate_30ma_full_d3_substrate_handoff(a1, r315.R315D3EnvironmentAdapter(a1, proxy), cfg)
    assert rep["full_d3_substrate_identity_exact"] is True
    assert all(row["exact"] for row in rep["fields"].values())


def test_context_manager_restores_environment_function():
    a1 = _a1(); cfg = r315.R315Config(); proxy = OldProviderProxy(a1, cfg)
    ad = r315.R315D3EnvironmentAdapter(a1, proxy)
    original = r38.bp.environment_at
    with r315.patched_r38_late_cenozoic_environment(ad):
        assert r38.bp.environment_at is not original
    assert r38.bp.environment_at is original


def test_smoke_proxy_runtime_is_exactly_equivalent_to_existing_r38_semantics():
    a1 = _a1(); md = _metadata_rows(); cfg = r315.R315Config(); parent = _parent_state()
    # Existing R38 endpoint-state semantics.
    direct_state = r313.r312.r311._clone_state(parent)
    direct, direct_records = r38.advance_state(direct_state, a1, md, cfg, r315.SMOKE_END_AGE_MA)
    # Same semantics through the R3.15 C2->D3 injection surface, with a proxy
    # returning the exact pre-R3.14 environment.
    proxy = OldProviderProxy(a1, cfg)
    bound, bound_records = r315.run_secular_biology(parent, a1, md, proxy, cfg, r315.SMOKE_END_AGE_MA)
    cmp = r38.compare_runtime_states(direct, bound)
    # Scientific state and telemetry records are exact. Snapshot bracket labels
    # intentionally identify the new C2 provider instead of the old A1 bracket.
    assert all(row["same"] for row in cmp["arrays"].values())
    assert all(row["same"] for row in cmp["reduced_state"].values())
    assert all(v for k, v in cmp["exact_fields"].items() if k != "snapshots")
    assert cmp["exact_fields"]["snapshots"] is False
    assert direct_records == bound_records


def test_run_rejects_crossing_200ka_bridge():
    a1 = _a1(); md = _metadata_rows(); cfg = r315.R315Config(); parent = _parent_state(); proxy = OldProviderProxy(a1, cfg)
    with pytest.raises(ValueError):
        r315.run_secular_biology(parent, a1, md, proxy, cfg, 0.125)


def test_run_rejects_off_cadence_endpoint():
    a1 = _a1(); md = _metadata_rows(); cfg = r315.R315Config(); parent = _parent_state(); proxy = OldProviderProxy(a1, cfg)
    with pytest.raises(ValueError):
        r315.run_secular_biology(parent, a1, md, proxy, cfg, 29.9)


def test_checkpoint_roundtrip_smoke(tmp_path: Path):
    a1 = _a1(); md = _metadata_rows(); cfg = r315.R315Config(); parent = _parent_state(); proxy = OldProviderProxy(a1, cfg)
    st, recs = r315.run_secular_biology(parent, a1, md, proxy, cfg, r315.SMOKE_END_AGE_MA)
    ck = r315.save_checkpoint(st, tmp_path, {"test": True}, cfg, {"records": len(recs)}, smoke=True)
    reload = r315.load_checkpoint(Path(ck["json"]), smoke=True)
    assert r38.compare_runtime_states(st, reload)["equivalent"] is True


def test_no_scientific_parameter_change_vs_r313_defaults():
    a = r315.R315Config(); b = r313.R313Config()
    for key in (
        "biology_cadence_years", "transport_cadence_years", "mutation_variance_supply_normalized_per_myr",
        "nonlinear_stabilizing_variance_depletion_per_myr_per_q", "variance_ceiling_normalized", "body_mass_scale",
        "speciation_check_interval_years", "ordinary_extinction_check_interval_years",
        "deme_fission_check_interval_years", "reconnection_check_interval_years",
    ):
        assert getattr(a, key) == getattr(b, key), key
