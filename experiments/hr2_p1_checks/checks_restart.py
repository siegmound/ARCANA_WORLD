"""CREATED_NOT_RUN: complete native restart and bounded B0 pair tests."""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import pytest

WORK = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(WORK / "experiments"), str(WORK / "src")]
from hr2_p1.checkpoint import PairStore, load_native, save_native
from hr2_p1.manufactured import advance_annual, new_case
from hr2_p1.model import canonical, digest, restore_native


def child(mode, source, target, output):
    checked = source if mode == "native" else source / "CONTEXT.json"
    args = [sys.executable, "-B", str(WORK / "scripts/r6_hr2_p1_resume_probe.py"),
            "--mode", mode, "--input", str(source), "--output", str(output),
            "--expected-input-sha256", hashlib.sha256(checked.read_bytes()).hexdigest(),
            "--target-year", str(target)]
    run = subprocess.run(args, cwd=WORK, capture_output=True, text=True,
                         env={**os.environ, "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    assert run.returncode == 0, (run.stdout, run.stderr)
    return json.loads(run.stdout.splitlines()[-1])


@pytest.mark.parametrize("target,split", [(3, 1), (10, 5)])
def test_full_native_direct_split_and_separate_process(tmp_path, target, split):
    direct = new_case(16, 8, target)
    advance_annual(direct, target)
    segment = new_case(16, 8, target)
    advance_annual(segment, split)
    saved = tmp_path / "NATIVE.json"
    save_native(saved, segment)
    resumed = load_native(saved, expected_parameters=direct.parameters,
                          expected_mesh_sha256=direct.mesh.sha256)
    advance_annual(resumed, target)
    assert resumed.checkpoint() == direct.checkpoint()
    output = tmp_path / "CHILD_NATIVE.json"
    result = child("native", saved, target, output)
    assert result["year"] == target
    assert load_native(output).checkpoint() == direct.checkpoint()
    with pytest.raises(FileExistsError):
        save_native(saved, direct)


def test_midwindow_native_checkpoint_owns_complete_schedule():
    case = new_case(16, 8, 3.)
    case.start_window(1.)
    case.step()
    cp = case.checkpoint()
    encoded = canonical(cp)
    resumed = restore_native(json.loads(encoded), case.parameters, case.mesh.sha256)
    case.finish_window()
    assert canonical(cp) == encoded  # No alias to live histogram or schedule.
    resumed.finish_window()
    advance_annual(case, 3)
    advance_annual(resumed, 3)
    assert resumed.checkpoint() == case.checkpoint()


@pytest.mark.parametrize("kind", ["raw", "source", "negative", "clock", "histogram", "authority"])
def test_native_corruption_and_semantic_negatives(kind):
    case = new_case(16, 8, 3.)
    advance_annual(case, 1)
    cp = case.checkpoint()
    if kind in ("raw", "negative"):
        cp["body"]["volumes_m3"][0] = -1.
    elif kind == "source":
        cp["body"]["source_identity"]["numpy"] = "FORGED"
    elif kind == "clock":
        cp["body"]["year"] = 1000.
    elif kind == "histogram":
        cp["body"]["accepted_steps"] += 1
    else:
        cp["body"]["scientific_authority"] = True
    if kind != "raw":
        cp["sha256"] = digest(cp["body"])
    with pytest.raises(ValueError):
        restore_native(cp, case.parameters, case.mesh.sha256)
    with pytest.raises(ValueError, match="CONFIG"):
        restore_native(case.checkpoint(), replace(case.parameters, kappa_m2_year=1.))
    with pytest.raises(ValueError, match="MESH"):
        restore_native(case.checkpoint(), expected_mesh_sha256="0" * 64)


@pytest.mark.parametrize("target,split", [(3, 1), (10, 5)])
def test_b0_contains_full_native_state_and_prefix_then_child_resume(tmp_path, target, split):
    case = new_case(16, 8, target)
    folder = tmp_path / "PAIRED"
    store = PairStore(folder, case.parameters, case.mesh.sha256, f"P1_{target}",
                      initial_identity_sha256=digest(case.initial_identity))
    store.commit(case, [{"ordinal": 0, "time_year": 0., "kind": "INITIAL_NATIVE_STATE"}])
    advance_annual(case, split)
    store.commit(case, [{"ordinal": 1, "time_year": float(split), "kind": "WINDOW_NATIVE_STATE"}])
    reopened = PairStore(folder, case.parameters, case.mesh.sha256, f"P1_{target}",
                         initial_identity_sha256=digest(case.initial_identity), reopen=True)
    assert reopened.read_latest().checkpoint() == case.checkpoint()
    output = tmp_path / "CHILD_FROM_B0.json"
    child("pair", folder, target, output)
    direct = new_case(16, 8, target)
    advance_annual(direct, target)
    assert load_native(output).checkpoint() == direct.checkpoint()
    # Unconfirmed bytes are not restart authority and are not deleted on read.
    orphan = folder / "journal" / ("f" * 64 + ".json")
    orphan.write_text("unconfirmed forensic tail")
    assert reopened.read_latest().year == split
    assert orphan.read_text() == "unconfirmed forensic tail"


def test_b0_wrong_context_corrupt_prefix_and_stale_view(tmp_path):
    case = new_case(16, 8, 3.)
    root = tmp_path / "STORE"
    a = PairStore(root, case.parameters, case.mesh.sha256, "CAS_TEST",
                  initial_identity_sha256=digest(case.initial_identity))
    a.commit(case, [{"ordinal": 0, "time_year": 0.}])
    stale = PairStore(root, case.parameters, case.mesh.sha256, "CAS_TEST",
                      initial_identity_sha256=digest(case.initial_identity), reopen=True)
    advance_annual(case, 1)
    a.commit(case, [{"ordinal": 1, "time_year": 1.}])
    # Distinct staged prefix reaches the B0 expected-parent CAS rather than a
    # content-file collision. It remains unconfirmed after rejection.
    with pytest.raises(Exception):
        stale.commit(case, [{"ordinal": 1, "time_year": 1., "attempt": "STALE"}])
    assert a.read_latest().checkpoint() == case.checkpoint()
    with pytest.raises(ValueError, match="CONTEXT"):
        PairStore(root, replace(case.parameters, kappa_m2_year=1.), case.mesh.sha256,
                  "CAS_TEST", initial_identity_sha256=digest(case.initial_identity), reopen=True)
    committed = root / "journal" / (a.prefix_head + ".json")
    committed.write_bytes(committed.read_bytes() + b"x")
    with pytest.raises((ValueError, json.JSONDecodeError)):
        a.read_latest()


def test_pair_rejects_different_initial_field_even_on_same_mesh(tmp_path):
    case = new_case(16, 8, 3., "latitude")
    other = new_case(16, 8, 3., "longitude")
    store = PairStore(tmp_path / "IC_BOUND", case.parameters, case.mesh.sha256, "IC_TEST",
                      initial_identity_sha256=digest(case.initial_identity))
    with pytest.raises(ValueError, match="INITIAL_CONDITION"):
        store.commit(other, [{"ordinal": 0, "time_year": 0.}])


def test_no_history_resolution_or_display_claim_from_native_checkpoint():
    case = new_case(16, 8, 3.)
    body = case.checkpoint()["body"]
    assert body["mesh"]["metadata"]["width"] == 16
    assert "separate contract" in body["history_resolution"]
    assert body["scientific_authority"] is False and body["production_authority"] is False
    assert body["initial_identity"]["R6_T0_inputs_used"] is False


def test_profile_prepared_native_checkpoint_query_and_b0_services(tmp_path):
    from hr2_p1.checkpoint import save_exclusive
    case = new_case(16, 8, 3.)
    tick = time.perf_counter()
    diagnostics = advance_annual(case, 3)
    numeric_s = time.perf_counter() - tick
    tick = time.perf_counter()
    native = case.checkpoint()
    seal_s = time.perf_counter() - tick
    path = tmp_path / "FULL_NATIVE.json"
    tick = time.perf_counter()
    save_exclusive(path, native)
    persist_s = time.perf_counter() - tick
    tick = time.perf_counter()
    restored = load_native(path, expected_parameters=case.parameters,
                           expected_mesh_sha256=case.mesh.sha256)
    restore_s = time.perf_counter() - tick
    tick = time.perf_counter()
    query = restored.heights().copy()
    query_s = time.perf_counter() - tick
    assert np.array_equal(query, case.heights())
    tick = time.perf_counter()
    pair = PairStore(tmp_path / "PROFILE_PAIR", case.parameters, case.mesh.sha256, "PROFILE",
                     initial_identity_sha256=digest(case.initial_identity))
    pair.commit(case, [{"ordinal": i, "time_year": row["end_year"],
                       "accepted_step": row["accepted_step"], "transfer_sha256": row["transfer_sha256"]}
                      for i, row in enumerate(diagnostics)])
    paired_s = time.perf_counter() - tick
    tick = time.perf_counter()
    assert pair.read_latest().checkpoint() == case.checkpoint()
    verify_s = time.perf_counter() - tick
    paths = [p for p in tmp_path.rglob("*") if p.is_file()]
    metrics = {"scope": "BOUNDED_MANUFACTURED16x8_3Y_SINGLE_SERVICE_SAMPLE",
               "kernel_service_s_including_checks": numeric_s, "accepted_steps": case.accepted_steps,
               "face_count": len(case.mesh.first), "dt_histogram_hex_years": case.dt_histogram,
               "native_seal_for_observation_s": seal_s,
               "native_encode_write_fsync_s": persist_s, "native_restore_verify_s": restore_s,
               "full_native_state_query_s": query_s, "b0_pair_service_s_including_native_and_prefix": paired_s,
               "b0_read_validate_s": verify_s, "native_file_bytes": path.stat().st_size,
               "logical_bytes": sum(p.stat().st_size for p in paths),
               "allocated_bytes": sum(p.stat().st_blocks * 512 for p in paths), "files": len(paths),
               "note": "Nested service measurements are not additive; OS cache uncontrolled; no historical-query engine claim"}
    output = os.environ.get("HR2_P1_QUAL_OUTPUT")
    if output:
        with (Path(output) / "NATIVE_B0_SERVICE_PROFILE.json").open("x") as f:
            json.dump(metrics, f, indent=2)
            f.write("\n")
