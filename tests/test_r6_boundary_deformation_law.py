"""Fail-closed boundary and junction fixtures; no forward transition is run."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "r6_bind_boundary_deformation_and_junction_law.py"
SPEC = importlib.util.spec_from_file_location("r6_boundary_law", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.mark.parametrize(("normal", "tangent", "label"), [
    (0.2, 0.1, "divergent oblique two-plate fixture"),
    (-0.2, 0.1, "convergent oblique two-plate fixture"),
    (0.0, 0.2, "shear two-plate fixture"),
])
def test_unsupported_boundary_motion_blocks_instead_of_creating_geometry(normal, tangent, label):
    status, reason = MODULE.classify_finite_step({
        "relative_normal_velocity_m_per_year": normal,
        "relative_tangential_velocity_m_per_year": tangent,
    })
    assert status == "BLOCKED", label
    assert reason


def test_midpoint_residual_identity_is_only_an_algebraic_diagnostic():
    va = [2.0, -1.0, 0.5]
    vb = [-1.0, 4.0, 2.5]
    vbnd = [(a + b) / 2 for a, b in zip(va, vb)]
    ra = [a - c for a, c in zip(va, vbnd)]
    rb = [b - c for b, c in zip(vb, vbnd)]
    assert [b - a for a, b in zip(ra, rb)] == pytest.approx([b - a for a, b in zip(va, vb)])
    contract = json.loads((ROOT / "R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT.json").read_text(encoding="utf-8"))
    fam_a = next(x for x in contract["model_families"] if x["family"].startswith("A_"))
    assert fam_a["disposition"] == "ALGEBRAIC_DIAGNOSTIC_ONLY_NOT_SELECTED_AS_PHYSICAL_TRANSITION"


def test_every_t0_segment_and_higher_order_junction_fails_closed():
    census = json.loads((ROOT / "R6_SHARED_BOUNDARY_FINITE_STEP_CENSUS.json").read_text(encoding="utf-8"))
    assert census["segment_count"] == 1983
    assert census["finite_step_status_counts"] == {"BLOCKED": 1983}
    assert census["junction_count"] == 20
    assert census["junction_status_counts"] == {"BLOCKED": 20}
    for junction in census["junctions"]:
        assert junction["degree"] >= 3
        assert junction["canonical_velocity"] is None
        assert junction["compatibility_status"] == "BLOCKED"


def test_existing_spherical_t0_partition_is_retained_without_a_future_partition_claim():
    manifest = json.loads((ROOT / "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json").read_text(encoding="utf-8"))
    readiness = json.loads((ROOT / "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V6.json").read_text(encoding="utf-8"))
    assert manifest["topology"]["face_count"] == 64800
    assert manifest["topology"]["partition_proof"]["one_face_per_parent_cell"] is True
    assert readiness["forward_evolution_executed"] is False
    assert readiness["positive_interval"] is False


def test_dateline_and_polar_vertex_keys_remain_canonical():
    prior = ROOT / "scripts" / "r6_bind_shared_boundary_topology_contact.py"
    spec = importlib.util.spec_from_file_location("r6_boundary_ids", prior)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.vertex_key(50, 0) == mod.vertex_key(50, 360)
    assert mod.vertex_key(0, 12) == mod.vertex_key(0, 271) == "SOUTH_POLE"
    assert mod.vertex_key(180, 12) == mod.vertex_key(180, 271) == "NORTH_POLE"
