from __future__ import annotations
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arcana_worldsim.scientific_engines.r323_functional_ensemble import (
    TRAITS, GUILD_DESCRIPTORS, RATE_REGIMES, R323Config, _guild_target, _ou_step,
    derived_capabilities, trait_calibration_registry, _population_weighted_species_ensemble,
)


def test_trait_count_and_unique():
    assert len(TRAITS) == 31
    assert len(set(TRAITS)) == 31


def test_six_generic_guild_descriptors_only():
    assert sorted(GUILD_DESCRIPTORS) == [1,2,3,4,5,6]
    s = json.dumps(GUILD_DESCRIPTORS)
    assert "human" not in s.lower()
    assert "sapien" not in s.lower()


def test_guild_targets_are_weak_and_finite():
    for gid in GUILD_DESCRIPTORS:
        z = _guild_target(gid)
        assert z.shape == (31,)
        assert np.isfinite(z).all()
        assert np.max(np.abs(z)) < 1.0


def test_rate_regimes_ordered_by_lability():
    assert RATE_REGIMES["CONSERVATIVE"]["diffusion_per_sqrt_myr"] < RATE_REGIMES["BASELINE"]["diffusion_per_sqrt_myr"] < RATE_REGIMES["LABILE"]["diffusion_per_sqrt_myr"]
    assert RATE_REGIMES["CONSERVATIVE"]["half_life_myr"] > RATE_REGIMES["BASELINE"]["half_life_myr"] > RATE_REGIMES["LABILE"]["half_life_myr"]


def test_ou_zero_time_exact_identity():
    rng = np.random.default_rng(1)
    x = np.arange(31, dtype=float)
    y = _ou_step(x, np.zeros(31), 0.0, 20.0, 0.1, rng)
    assert np.array_equal(x, y)


def test_ou_is_deterministic_for_same_seed():
    x = np.zeros(31)
    theta = np.ones(31)*0.1
    a = _ou_step(x, theta, 10.0, 20.0, 0.1, np.random.default_rng(5))
    b = _ou_step(x, theta, 10.0, 20.0, 0.1, np.random.default_rng(5))
    assert np.array_equal(a, b)


def test_derived_capabilities_are_bounded():
    e = np.random.default_rng(3).normal(size=(7, 5, 31))
    t, q = derived_capabilities(e)
    assert t.shape == (7,5) and q.shape == (7,5)
    assert np.all((t >= 0) & (t <= 1))
    assert np.all((q >= 0) & (q <= 1))


def test_derived_capabilities_improve_with_dependencies():
    base = np.zeros((1,1,31))
    high = base.copy()
    high[:] = 2.0
    t0,q0 = derived_capabilities(base)
    t1,q1 = derived_capabilities(high)
    assert t1[0,0] > t0[0,0]
    assert q1[0,0] > q0[0,0]


def test_calibration_registry_complete_and_no_human_anchor():
    rows = trait_calibration_registry()
    assert len(rows) == 31
    assert [x["trait_id"] for x in rows] == TRAITS
    text = json.dumps(rows).lower()
    assert "human_anchor" not in text
    assert all(len(x["empirical_source_set"]) >= 2 for x in rows)


def test_heritability_is_metadata_not_va():
    rows = trait_calibration_registry()
    assert all(x["heritability_or_va_model"]["type"] == "HERITABILITY_PRIOR_METADATA_ONLY_NOT_COMPONENT_VA" for x in rows)


def test_no_named_worldsim_lineage_in_calibration_rows():
    text = json.dumps(trait_calibration_registry())
    for prefix in ("HSG_", "BRW_", "LVF_", "RPT_", "CAR_", "APX_"):
        assert prefix not in text


def test_default_ensemble_size_is_large_integrated_stage():
    cfg = R323Config()
    assert cfg.replicates_per_regime == 32
    assert len(RATE_REGIMES) * cfg.replicates_per_regime == 96


def test_species_ensemble_is_population_weighted_from_components():
    e = np.zeros((2, 3, 31), dtype=float)
    e[:, 0, :] = 1.0
    e[:, 1, :] = 3.0
    e[:, 2, :] = 7.0
    comps = [
        {"species_id": "A", "population_total": 1.0},
        {"species_id": "A", "population_total": 3.0},
        {"species_id": "B", "population_total": 2.0},
    ]
    s = _population_weighted_species_ensemble(e, comps, ["A", "B"])
    assert s.shape == (2, 2, 31)
    assert np.allclose(s[:, 0, :], 2.5)
    assert np.allclose(s[:, 1, :], 7.0)
