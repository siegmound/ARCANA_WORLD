from __future__ import annotations

from dataclasses import replace
import ast
import hashlib
import json
from pathlib import Path
import pytest

from arcana_worldsim.r6.functional_development import NodeMaterial, ReducedState
from arcana_worldsim.r6.geological_surface_microdomain import SUPPORTS
from arcana_worldsim.r6.int10k_short_reference import (
    ShortReferenceConfig, ShortReferenceError, _validate_regional_coverage,
    compare_reference, run_short_reference, verify_source_bundle,
)
from arcana_worldsim.r6.regional_geological_evolution import RegionalConfig


def _states():
    materials = tuple(NodeMaterial(
        role_id="CONTINENTAL_CRUST_REFERENCE" if i < 25 else "LITHOSPHERIC_MANTLE_REFERENCE",
        k_w_m_k=3.0 if i < 25 else 4.0,
        rho_kg_m3=2800.0 if i < 25 else 3300.0,
        cp_j_kg_k=1000.0,
        radiogenic_w_m3=1e-6 if i < 25 else 2e-8)
        for i in range(73))
    z = tuple(i / 72 for i in range(73))
    temperatures = tuple(280.0 + 1200.0 * x for x in z)
    base = ReducedState(0.0, 100_000.0, 100_000.0, 35_000.0,
                        100_000.0, 35_000.0, 100_000.0, 1.0, 0.0, 0.35,
                        z, temperatures, materials, 280.0, 1480.0)
    return {SUPPORTS[0]: base,
            SUPPORTS[1]: replace(base, width_m=101_000.0,
                                 initial_width_m=101_000.0)}


def _identity():
    return {
        "source_result_sha256": "a" * 64,
        "t0_boundary_id": "SYNTHETIC_T0_EDGE",
        "t0_boundary_length_m": 111_194.92664455874,
        "support_cells": [
            {"support_id": SUPPORTS[0], "grid_cell": [91, 28], "plate_id": 11},
            {"support_id": SUPPORTS[1], "grid_cell": [91, 29], "plate_id": 5},
        ],
    }


def _source_bundle(tmp_path):
    result = b'{"sample":"E0 fixture"}\n'
    result_hash = hashlib.sha256(result).hexdigest()
    sidecar = f"{result_hash}  RESULT.json\n".encode("ascii")
    sidecar_hash = hashlib.sha256(sidecar).hexdigest()
    manifest = {
        "schema": "ARCANA_CONSTITUTIVE_MECHANICS_MANIFEST_V1",
        "manifest_self_hash": None,
        "result": {"path": "RESULT.json", "sha256": result_hash,
                   "size_bytes": len(result)},
        "sidecar": {"path": "RESULT.json.sha256", "sha256": sidecar_hash,
                    "size_bytes": len(sidecar)},
    }
    manifest_bytes = json.dumps(manifest, sort_keys=True).encode("utf-8")
    members = {"RESULT.json": result, "MANIFEST.json": manifest_bytes,
               "RESULT.json.sha256": sidecar}
    for name, payload in members.items():
        (tmp_path / name).write_bytes(payload)
    expected = {name: hashlib.sha256(payload).hexdigest()
                for name, payload in members.items()}
    return members, expected


def test_source_bundle_hashes_and_manifest_sidecar_closure(tmp_path):
    members, expected = _source_bundle(tmp_path)
    assert verify_source_bundle(tmp_path, expected) == expected
    assert all((tmp_path / name).read_bytes() == data
               for name, data in members.items())


@pytest.mark.parametrize("bad_digest", ["a" * 52, "a" * 63, "A" * 64, "g" * 64])
def test_source_bundle_rejects_malformed_sha256_pins(tmp_path, bad_digest):
    _, expected = _source_bundle(tmp_path)
    expected["MANIFEST.json"] = bad_digest
    with pytest.raises(ShortReferenceError, match="SOURCE_HASH_MALFORMED"):
        verify_source_bundle(tmp_path, expected)


@pytest.mark.parametrize("member", ["RESULT.json", "MANIFEST.json", "RESULT.json.sha256"])
def test_source_bundle_rejects_member_identity_mismatch(tmp_path, member):
    _, expected = _source_bundle(tmp_path)
    expected[member] = "0" * 64
    with pytest.raises(ShortReferenceError, match="SOURCE_MEMBER_HASH_MISMATCH"):
        verify_source_bundle(tmp_path, expected)


def test_source_bundle_rejects_manifest_sidecar_disagreement(tmp_path):
    _, expected = _source_bundle(tmp_path)
    manifest_path = tmp_path / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["result"]["sha256"] = "f" * 64
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    expected["MANIFEST.json"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    with pytest.raises(ShortReferenceError, match="SOURCE_MANIFEST_CLOSURE_INVALID"):
        verify_source_bundle(tmp_path, expected)


def test_e1_cli_manifest_pin_is_full_sha256():
    cli = Path(__file__).parents[1] / "scripts" / "r6_int10k_short_reference.py"
    tree = ast.parse(cli.read_text(encoding="utf-8"))
    assignment = next(node for node in tree.body
                      if isinstance(node, ast.Assign) and
                      any(isinstance(target, ast.Name) and target.id == "SOURCE_HASHES"
                          for target in node.targets))
    hashes = ast.literal_eval(assignment.value)
    assert hashes["MANIFEST.json"] == (
        "a1e72a3f541d1c75809cc724c9723332303e90aa775a2c92bc0acc11a240bc21")
    assert all(len(digest) == 64 and all(char in "0123456789abcdef" for char in digest)
               for digest in hashes.values())


@pytest.mark.parametrize("years,split", [(3, 1), (10, 5)])
def test_reference_direct_equals_checkpoint_split(years, split):
    out = run_short_reference(_states(), _identity(),
                              config=ShortReferenceConfig(years, split))
    assert out["status"] == "PASS_SHORT_REFERENCE_IN_MEMORY_PARITY"
    assert out["direct"]["regional_state"]["time_years"] == years
    for trajectory in (out["direct"], out["split"]):
        state = trajectory["regional_state"]
        assert [row["time_year"] for row in state["records"]] == list(range(1, years + 1))
        assert [row["time_year"] for row in state["snapshots"]] == list(range(0, years + 1))


def test_regional_coverage_accepts_records_and_snapshots_with_initial_state():
    state = {
        "time_years": 3,
        "records": [{"time_year": year} for year in (1, 2, 3)],
        "snapshots": [{"time_year": year} for year in (0, 1, 2, 3)],
    }
    _validate_regional_coverage(state, 3)


@pytest.mark.parametrize("field,years", [
    ("records", [1, 3]),                  # missing annual record
    ("records", [1, 2, 2, 3]),            # duplicate annual record
    ("records", [2, 1, 3]),               # out-of-order annual record
    ("snapshots", [1, 2, 3]),             # missing year-zero initial snapshot
    ("snapshots", [0, 1, 1, 2, 3]),       # duplicate snapshot
    ("snapshots", [0, 2, 1, 3]),           # out-of-order snapshot
])
def test_regional_coverage_rejects_missing_duplicate_or_out_of_order_years(field, years):
    state = {
        "time_years": 3,
        "records": [{"time_year": year} for year in (1, 2, 3)],
        "snapshots": [{"time_year": year} for year in (0, 1, 2, 3)],
    }
    state[field] = [{"time_year": year} for year in years]
    with pytest.raises(ShortReferenceError, match="SHORT_REFERENCE_COVERAGE_INVALID"):
        _validate_regional_coverage(state, 3)


@pytest.mark.parametrize("time_years", [2, 4])
def test_regional_coverage_rejects_wrong_terminal_year(time_years):
    state = {
        "time_years": time_years,
        "records": [{"time_year": year} for year in (1, 2, 3)],
        "snapshots": [{"time_year": year} for year in (0, 1, 2, 3)],
    }
    with pytest.raises(ShortReferenceError, match="SHORT_REFERENCE_COVERAGE_INVALID"):
        _validate_regional_coverage(state, 3)


@pytest.mark.parametrize("years,split", [(2, 1), (11, 1), (3, 0), (3, 3)])
def test_invalid_plan_fails_closed(years, split):
    with pytest.raises(ShortReferenceError):
        ShortReferenceConfig(years, split).validate()


def test_plan_drift_fails_closed():
    with pytest.raises(ShortReferenceError, match="PLANNED_DURATION_MISMATCH"):
        run_short_reference(_states(), _identity(),
                            config=ShortReferenceConfig(3, 1),
                            regional_config=RegionalConfig(duration_years=10))


def test_numeric_event_schema_and_finite_fail_closed():
    with pytest.raises(ShortReferenceError, match="NONFINITE"):
        compare_reference([float("nan")], [float("nan")])
    with pytest.raises(ShortReferenceError, match="REFERENCE_MISMATCH"):
        compare_reference({"events": ["a"]}, {"events": ["b"]})
    with pytest.raises(ShortReferenceError, match="REFERENCE_KEY_MISMATCH"):
        compare_reference({"a": 1}, {"b": 1})
    with pytest.raises(ShortReferenceError, match="REFERENCE_NUMERIC_MISMATCH"):
        compare_reference({"temperature_k": 400.0}, {"temperature_k": 401.0})
