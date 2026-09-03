from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pytest

from arcana_worldsim.state_query.r50_query import (
    DEFAULT_DOMAINS,
    EXPECTED_PARENT_HASHES,
    EXPECTED_R456_VERDICT,
    R50AuthorityResolver,
    R50QueryContract,
    R50QueryError,
    discover_r456_authority,
    sha256_file,
)

ROOT = Path(__file__).resolve().parents[1]


def test_exact_parent_hashes_close():
    for rel, expected in EXPECTED_PARENT_HASHES.items():
        p = ROOT / rel
        assert p.is_file(), rel
        assert sha256_file(p) == expected, rel


def test_r456_semantic_scanner_accepts_exact_closure(tmp_path: Path):
    d = tmp_path / "outputs" / "v0_6D1_R4_56_SEAL"
    d.mkdir(parents=True)
    obj = {
        "stage": "v0.6D1-R4.56",
        "verdict": EXPECTED_R456_VERDICT,
        "exact_frozen_jobs": 23,
        "closed_jobs": 23,
        "gaps": 0,
        "multi_engine_full_revalidation_closed": True,
        "numeric_cross_engine_corroboration_claimed": False,
        "canonical_state_changed": False,
        "deep_biological_coupling": False,
    }
    (d / "R4_56_FINAL.json").write_text(json.dumps(obj), encoding="utf-8")
    got = discover_r456_authority(tmp_path)
    assert got["status"] == "R456_RUNTIME_AUTHORITY_VERIFIED"
    assert all(got["checks"].values())


def test_20ka_exact_and_17p5_variable_specific_resolution():
    with R50AuthorityResolver(ROOT, allow_unverified_r456=True) as r:
        q20 = R50QueryContract(query_id="T20", target_age_ka=20.0)
        q175 = R50QueryContract(query_id="T175", target_age_ka=17.5)
        a = r.resolve(q20)
        b = r.resolve(q175)

        assert a["provenance"]["population_summary"]["mode"] == "EXACT"
        assert a["provenance"]["population_detail"]["mode"] == "EXACT"
        assert a["provenance"]["environment"]["mode"] == "EXACT"
        assert a["provenance"]["flora"]["mode"] == "EXACT"
        assert a["provenance"]["fauna"]["mode"] == "EXACT"

        assert b["provenance"]["population_summary"]["mode"] == "EXACT"
        assert b["provenance"]["population_detail"]["mode"] == "BOUNDED_SPATIAL_RECONSTRUCTION"
        assert b["provenance"]["population_detail"]["source_ages_ka"] == [20.0, 15.0]
        for name in ("environment", "flora", "fauna"):
            assert b["provenance"][name]["mode"] == "BRACKETED_LINEAR"
            assert b["provenance"][name]["source_ages_ka"] == [20.0, 15.0]
            assert b["provenance"][name]["weight_younger"] == pytest.approx(0.5)

        assert a["arrays"]["environment_fields"].shape == (90, 180, 7)
        assert a["arrays"]["producer_landscape"].shape == (36, 90, 180, 4)
        assert b["arrays"]["fauna_partner_trajectory_state"].shape == (32, 2, 24, 9)
        assert b["domain_coverage"]["fauna"].startswith("PARTIAL_")
        assert b["domain_coverage"]["surface_paleogeography"].startswith("PARTIAL_")


def test_17p5_population_detail_is_constrained_to_exact_summary():
    with R50AuthorityResolver(ROOT, allow_unverified_r456=True) as r:
        out = r.resolve(R50QueryContract(query_id="T175_CONSTRAINT", target_age_ka=17.5))
        summary = out["arrays"]["population_summary"]
        detail = out["arrays"]["deme_state"]
        active = out["arrays"]["deme_active"]
        names = list(map(str, out["arrays"]["population_summary_variable_names"]))
        pi = names.index("population_proxy")
        di = names.index("active_demes")
        np.testing.assert_allclose(detail[..., 0].sum(axis=-1), summary[..., pi], rtol=2e-6, atol=2e-3)
        np.testing.assert_array_equal(active.sum(axis=-1), np.rint(summary[..., di]).astype(int))
        assert np.all(detail[..., 1] >= 0) and np.all(detail[..., 1] <= 89)
        assert np.all(detail[..., 2] >= 0) and np.all(detail[..., 2] < 180)


def test_query_is_deterministic_and_parent_immutable():
    before = {rel: sha256_file(ROOT / rel) for rel in EXPECTED_PARENT_HASHES}
    with R50AuthorityResolver(ROOT, allow_unverified_r456=True) as r:
        q = R50QueryContract(query_id="TDET", target_age_ka=17.5)
        a = r.resolve(q)
        b = r.resolve(q)
        assert a["semantic_state_sha256"] == b["semantic_state_sha256"]
        assert a["governance"]["randomness_used"] is False
        assert a["governance"]["full_history_rerun_performed"] is False
        assert a["governance"]["external_engine_execution_performed"] is False
        assert a["governance"]["canonical_state_changed"] is False
    after = {rel: sha256_file(ROOT / rel) for rel in EXPECTED_PARENT_HASHES}
    assert before == after


def test_native_grid_region_slice_and_wrapped_longitude_window():
    region = {"grid_row_min": 10, "grid_row_max": 12, "grid_col_min": 178, "grid_col_max": 1}
    with R50AuthorityResolver(ROOT, allow_unverified_r456=True) as r:
        out = r.resolve(R50QueryContract(query_id="TREGION", target_age_ka=17.5, region=region))
        np.testing.assert_array_equal(out["arrays"]["grid_row_indices"], [10, 11, 12])
        np.testing.assert_array_equal(out["arrays"]["grid_col_indices"], [178, 179, 0, 1])
        assert out["arrays"]["environment_fields"].shape == (3, 4, 7)
        assert out["arrays"]["producer_landscape"].shape == (36, 3, 4, 4)


def test_fail_closed_on_extrapolation_or_canonical_write():
    with R50AuthorityResolver(ROOT, allow_unverified_r456=True) as r:
        with pytest.raises(R50QueryError):
            r.resolve(R50QueryContract(query_id="TOUT", target_age_ka=20.5, requested_domains=DEFAULT_DOMAINS))
        with pytest.raises(R50QueryError):
            r.resolve(R50QueryContract(query_id="TCANON", target_age_ka=17.5, canonical_write=True))
        with pytest.raises(R50QueryError):
            r.resolve(R50QueryContract(query_id="TEXTRAP", target_age_ka=17.5, allow_temporal_extrapolation=True))


def test_interpolation_can_be_explicitly_disabled():
    with R50AuthorityResolver(ROOT, allow_unverified_r456=True) as r:
        r.resolve(R50QueryContract(query_id="T20_NO_INTERP", target_age_ka=20.0, allow_temporal_interpolation=False))
        with pytest.raises(R50QueryError):
            r.resolve(R50QueryContract(query_id="T175_NO_INTERP", target_age_ka=17.5, allow_temporal_interpolation=False))
        with pytest.raises(R50QueryError):
            r.resolve(R50QueryContract(
                query_id="T175_POP_ONLY_NO_INTERP",
                target_age_ka=17.5,
                requested_domains=("population",),
                allow_temporal_interpolation=False,
            ))


def test_population_detail_uses_dense_cha2_authority_when_available():
    with R50AuthorityResolver(ROOT, allow_unverified_r456=True) as r:
        out = r.resolve(R50QueryContract(
            query_id="TCHA2_HALFSTEP",
            target_age_ka=12.925,
            requested_domains=("population",),
        ))
        p = out["provenance"]["population_detail"]
        assert p["mode"] == "BOUNDED_SPATIAL_RECONSTRUCTION"
        assert p["source_ages_ka"] == pytest.approx([12.95, 12.9])
