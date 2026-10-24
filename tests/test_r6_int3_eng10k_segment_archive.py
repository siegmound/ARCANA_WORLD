from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from dataclasses import dataclass
from types import ModuleType

import pytest

from arcana_worldsim.r6.segment_archive import (  # noqa: E402
    INCOMPLETE_NAME, SegmentArchiveError, SegmentArchiveWriter,
    validate_segment_archive,
)

@pytest.fixture
def runner(monkeypatch):
    """Load runner glue with numerical providers stubbed; no kernel can execute."""
    class ContractError(ValueError):
        pass

    functional = ModuleType("arcana_worldsim.r6.functional_development")
    functional.initial_reduced_state = lambda *args, **kwargs: None
    functional.pure_shear_thermal_step = lambda *args, **kwargs: None
    int0a = ModuleType("arcana_worldsim.r6.int0a_pipeline")
    for name in ("advance_pair", "capture_numerical_step_samples", "prepare_pair_5_11",
                 "trajectory_document"):
        setattr(int0a, name, lambda *args, **kwargs: None)
    int0a.MAX_DIAGNOSTIC_SAMPLES_PER_SUPPORT = 1002
    int3 = ModuleType("arcana_worldsim.r6.int3_eng10k")
    int3.MAX_PROJECTED_OUTPUT_BYTES = 10_000_000
    int3.R4_KERNEL_SHA256 = "0" * 64
    int3.R4_SUPPORT_IDS = ("TEST-C028", "TEST-C029")
    int3.R4_MANIFEST_SHA256 = "1" * 64
    int3.RESOLUTION_FACTORS = (0.001, 0.0005, 0.00025)
    int3.SECONDS_PER_YEAR = 31_557_600.0
    int3.Eng10kContractError = ContractError
    int3.advance_with_bounded_samples = lambda *args, **kwargs: None
    int3.canonical_bytes = lambda value: (json.dumps(
        value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    int3.compare_reduced_states = lambda *args, **kwargs: None
    int3.create_evidence_attempt_parent = lambda *args, **kwargs: None
    int3.load_r4_continuation_bundle = lambda *args, **kwargs: None
    int3.provider_component_bindings_match = lambda *args, **kwargs: False
    int3.resolve_evidence_destinations = lambda *args, **kwargs: None
    int3.resolve_incomplete_evidence_output = lambda *args, **kwargs: None
    int3.sha256_bytes = lambda value: hashlib.sha256(value).hexdigest()
    monkeypatch.setitem(sys.modules, functional.__name__, functional)
    monkeypatch.setitem(sys.modules, int0a.__name__, int0a)
    monkeypatch.setitem(sys.modules, int3.__name__, int3)
    monkeypatch.setattr(sys, "path", list(sys.path))
    source = Path(__file__).resolve().parents[1] / "scripts" / "r6_int3_eng10k.py"
    spec = importlib.util.spec_from_file_location("r6_int3_eng10k_synthetic_test", source)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class SyntheticState:
    time_s: float
    temperature_k: tuple[float, ...]

    def payload(self):
        return {"schema": "TEST_STATE_V1", "time_s": self.time_s,
                "temperature_k": list(self.temperature_k),
                "material_coordinate": [0.0, 1.0],
                "materials": [{"role_id": "TEST"}, {"role_id": "TEST"}],
                "width_m": 100.0, "crust_m": 20.0,
                "lithosphere_m": 80.0, "beta": 1.0,
                "accumulated_strain": 0.0}


def _provenance():
    digest = hashlib.sha256(b"synthetic runner provenance").hexdigest()
    return {"identity_status": "SYNTHETIC_TEST_ONLY", "source_commit": "TEST_ONLY",
            "source_composite_sha256": digest, "configuration_sha256": digest,
            "provider_identities": {"fixture": digest},
            "input_identities": {"fixture": digest}}


def _invoke(runner, writer, *, kind: str, support: str, factor: float, start: float):
    initial = SyntheticState(start, (280.0, 400.0))
    duration_s = 2.0 * runner.SECONDS_PER_YEAR
    states = (initial, SyntheticState(start + duration_s / 2.0, (280.1, 400.1)),
              SyntheticState(start + duration_s, (280.2, 400.2)))

    def compute(observer=None):
        if observer is not None:
            for state in states:
                observer(state)
        return states[-1], {"integration_substeps": 2, "synthetic": True}

    markers = runner._TrajectoryMarkerWriter(None, expected_trajectories=8)
    return runner._run_profiled_trajectory(
        markers, trajectory_kind=kind, support_id=support,
        resolution_factor=factor, duration_years=2.0, compute=compute,
        archive_writer=writer, initial_state=initial,
    ), states


def test_runner_archive_binds_all_eight_trajectories_and_preserves_compute_results(tmp_path, runner):
    (tmp_path / "run").mkdir()
    writer = SegmentArchiveWriter(tmp_path / "run" / "SEGMENT_ARCHIVE_V1",
        segment_id="synthetic-int3", provenance=_provenance(), expected_trajectory_count=8)
    expected = []
    for factor in (0.001, 0.0005, 0.00025):
        for support in ("TEST-C028", "TEST-C029"):
            result, states = _invoke(runner, writer, kind="DIRECT", support=support,
                                     factor=factor, start=0.0)
            assert result[0] == states[-1]
            assert result[1] == {"integration_substeps": 2, "synthetic": True}
            expected.append(("DIRECT", support, factor, states))
    for support in ("TEST-C028", "TEST-C029"):
        result, states = _invoke(runner, writer, kind="RESTART", support=support,
                                 factor=0.0005, start=100.0)
        assert result[0] == states[-1]
        assert result[1] == {"integration_substeps": 2, "synthetic": True}
        expected.append(("RESTART", support, 0.0005, states))

    writer.finalize()
    root = tmp_path / "run" / "SEGMENT_ARCHIVE_V1"
    identity = validate_segment_archive(root)
    assert identity["trajectory_count"] == 8
    assert identity["state_count"] == 24
    records = [json.loads(line) for line in (root / "STATES.jsonl").read_text(encoding="utf-8").splitlines()]
    for (kind, support, factor, states), group in zip(expected, (records[i:i + 3] for i in range(0, 24, 3))):
        assert [row["trajectory_kind"] for row in group] == [kind] * 3
        assert [row["support_id"] for row in group] == [support] * 3
        assert [row["resolution_factor"] for row in group] == [factor] * 3
        assert [row["state"] for row in group] == [state.payload() for state in states]
        assert [row["record_type"] for row in group] == [
            "INITIAL_INTEGRATOR_STATE", "INTEGRATOR_SUBSTEP_STATE", "INTEGRATOR_SUBSTEP_STATE"]


def test_runner_archive_does_not_publish_until_every_declared_trajectory_completes(tmp_path, runner):
    (tmp_path / "partial").mkdir()
    root = tmp_path / "partial" / "SEGMENT_ARCHIVE_V1"
    writer = SegmentArchiveWriter(root, segment_id="partial-int3",
        provenance=_provenance(), expected_trajectory_count=8)
    for factor in (0.001, 0.0005, 0.00025):
        for support in ("TEST-C028", "TEST-C029"):
            _invoke(runner, writer, kind="DIRECT", support=support, factor=factor, start=0.0)
    with pytest.raises(SegmentArchiveError, match="EXPECTED_TRAJECTORY_SET_INCOMPLETE"):
        writer.finalize()
    writer.close_incomplete("SYNTHETIC_RUN_STOPPED_BEFORE_RESTARTS")
    assert (root / INCOMPLETE_NAME).is_file()
    assert not (root / "SEGMENT_MANIFEST.json").exists()
    with pytest.raises(SegmentArchiveError, match="ARCHIVE_MISSING_OR_INCOMPLETE"):
        validate_segment_archive(root)


def test_outer_runner_manifest_covers_archive_members_without_replacing_diagnostics(tmp_path, runner):
    output = tmp_path / "candidate"
    output.mkdir()
    (output / "RUN_STARTED.json").write_bytes(b"{}\n")
    archive_root = output / "SEGMENT_ARCHIVE_V1"
    writer = SegmentArchiveWriter(archive_root, segment_id="manifest-fixture",
        provenance=_provenance(), expected_trajectory_count=1)
    _, states = _invoke(runner, writer, kind="DIRECT", support="TEST-C028",
                        factor=0.0005, start=0.0)
    writer.finalize()
    diagnostic = {"samples": [{"time_s": 0.0}, {"time_s": 2.0}],
                  "all_substeps_retained": False}
    runner._write_bundle(output, {"DIAGNOSTIC_SAMPLES.json": diagnostic},
                         b"synthetic-config\n", {"preflight": "fixture"},
                         {"segment_archive": validate_segment_archive(archive_root)})

    manifest = json.loads((output / "ARTIFACT_MANIFEST.json").read_text(encoding="utf-8"))
    files = manifest["files"]
    expected_archive_names = {f"SEGMENT_ARCHIVE_V1/{path.name}"
                              for path in archive_root.iterdir()}
    assert expected_archive_names <= set(files)
    for relative in expected_archive_names:
        path = output / relative
        assert files[relative] == {"bytes": path.stat().st_size,
                                   "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    assert json.loads((output / "DIAGNOSTIC_SAMPLES.json").read_text(encoding="utf-8")) == diagnostic
    assert [state.time_s for state in states] == [0.0, runner.SECONDS_PER_YEAR,
                                                   2.0 * runner.SECONDS_PER_YEAR]


def test_runner_compute_without_archive_keeps_existing_call_shape_and_result(runner):
    markers = runner._TrajectoryMarkerWriter(None, expected_trajectories=1)
    expected = ("unchanged-state", {"integration_substeps": 7})
    final, diagnostics = runner._run_profiled_trajectory(
        markers, trajectory_kind="DIRECT", support_id="TEST-C028",
        resolution_factor=0.0005, duration_years=1.0,
        compute=lambda: expected,
    )
    assert (final, diagnostics) == expected
