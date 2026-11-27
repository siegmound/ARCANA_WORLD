"""C10 regressions for replay, geometry, native deck and the no-solve boundary."""
from pathlib import Path

import numpy as np
import pytest

from experiments.r6_thermo_provider_pilot_v1 import c10_boundary as bc
from experiments.r6_thermo_provider_pilot_v1 import c10_native as native
from experiments.r6_thermo_provider_pilot_v1 import c10_vertical as vertical
from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def prepared():
    return c10.prepare(ROOT)


def test_c09_replay_and_archive_identity(prepared):
    replay = prepared[0]["C09_REPLAY.json"]
    assert len(replay["replayed_reports"]) == 10
    assert len(replay["native_byte_replay"]) == 3
    assert replay["C09_EXIT"] is None
    assert replay["development_archive_manifest_sha256"] != c10.PIN
    with pytest.raises(ValueError, match="C08_SOURCE_PIN"):
        c10.verify_c09(c10.DEV)


def test_cut_endpoints_and_shared_nodes(prepared):
    reports, _, _, _, _ = prepared
    traces = reports["CONTINUOUS_BOUNDARY_TRACE_CANDIDATES.json"]["candidates"]
    package = reports["COMPLETE_CANDIDATE_INPUT_PACKAGE.json"]
    for trace in traces.values():
        rows = trace["rows"]
        assert len({r["parent_node_id"] for r in rows}) == len({r["runtime_node_id"] for r in rows}) == 32
        distal = [r for r in rows if r["source_distal_plate_id"] is not None]
        assert len(distal) == 18
        assert all(r["source_distal_south_east_m_s"] == r["prescribed_south_east_m_s"] for r in distal)
        assert all(cut["endpoints_exact"] and np.all(np.diff(cut["s_m"]) > 0) for cut in trace["cuts"].values())
    shared = [r for r in package["reporting_plate_binding"] if len(r["all_source_plate_ids"]) > 1]
    assert shared
    assert all(r["source_PRE_owner_plate_id"] in r["all_source_plate_ids"]
               and r["sided_fault_assignment"] is None for r in shared)


def test_transport_and_native_azimuth():
    a = np.array([1., 0., 0.])
    b = np.array([0., 1., 0.])
    v = np.array([0., 3., 4.])
    np.testing.assert_array_equal(bc.transport(v, a, b), [-3., 0., 4.])
    for south, east in ((1., 0.), (0., 1.), (-1., 0.), (0., -1.), (0., 0.)):
        np.testing.assert_allclose(bc.decode_native(*bc.angle_mag(south, east)), [south,east],
                                   rtol=0., atol=2e-15)
    for kind in ("linear_arc", bc.PREFERRED):
        assert bc.blend(0., kind) == 0.
        assert bc.blend(1., kind) == 1.


def test_perimeter_rank_compatibility(prepared):
    for design in prepared[0]["REGIONAL_CONSTRAINT_ANALYSIS.json"]["options"].values():
        assert (design["rank"], design["unconstrained_dof"]) == (64, 98)
        assert design["remaining_rigid_rotation_modes"] == 0
        assert design["stiffness_rank"] is None
        assert design["max_rhs_consistency_residual_m_s"] < 2e-22
        assert all(v == 1 for v in design["constraint_singular_values"])


def test_land_reference_column_has_sea_level_datum(prepared):
    _, _, profiles, _, _ = prepared
    profile = next(iter(profiles.values()))
    d = vertical.reference_stress([profile], [1.], 1000., 2000.)
    assert d["reference_pressure_at_base_Pa"] == 1000.*1000.*vertical.G
    assert d["native_1km_column_pressure_Pa"] > d["reference_pressure_at_base_Pa"]
    assert d["sigZZB_Pa"] < 0 and d["tauZZ_N_m"] < 0


def test_deck_serialization_and_compatibility_guards(prepared):
    reports, files, _, _, _ = prepared
    package = reports["COMPLETE_CANDIDATE_INPUT_PACKAGE.json"]
    p = package["lr_native_parameters"]
    assert files["regional.in"] == native.serialize_lr(p)
    assert files["regional_dry.in"] == native.serialize_lr(dict(p, Biot=0.))
    assert files["regional_compatibility_2km.in"] == native.serialize_lr(dict(p, zBAsth=2000.))
    assert len(files["regional.in"].splitlines()) == len(native.LR_FIELDS) + 1
    assert (p["trHMax"], p["iConve"], p["pltRef"]) == (0.,0,"RF")
    assert p["maxItr"] == 50 and p["okDelV"] == 1e-11
    for z in (0., 400., -1000.):
        with pytest.raises(ValueError, match="C10_BASAL_COMPATIBILITY_DEPTH"):
            native.lr_values(package["existing_pre_authority"],
                             reports["CONSTITUTIVE_BASELINE.json"]["C09_model"], 1.,
                             compatibility_depth=z)
    assert len(files["controlled.bcs"].splitlines()) == 33
    assert len(package["feg_columns"]) == 81


def test_fixed_and_basal_probe_cannot_advance(prepared):
    source = native.generated_source((ROOT/native.VENDOR/"SHELLS_v5.0.f90").read_text())
    assert "CALL ReadBC" in source and "call THOnB" in source
    assert "C10_STOP_AFTER_FIXED_BEFORE_PURE" in source
    assert "call pure" not in source.lower()
    assert "call viscos" not in source.lower()
    assert "call solver" not in source.lower()
    for report in (*prepared[0].values(), c10.acceptance()):
        assert report["physical_T1"] is None
        assert report["mechanical_solve_authorized"] is False
        assert report["authorial_selection_confirmed"] is False
        assert report["physical_material_assignments"] == 0
        assert report["WORLD_HISTORY_PRODUCTION_AUTHORIZED"] is False
