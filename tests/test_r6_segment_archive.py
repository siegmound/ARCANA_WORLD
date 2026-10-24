from __future__ import annotations

import hashlib
import json
from pathlib import Path
from dataclasses import dataclass, replace

import pytest

from arcana_worldsim.r6.segment_archive import (
    INCOMPLETE_NAME, MANIFEST_NAME, STATE_STREAM, SegmentArchiveError,
    SegmentArchiveWriter, validate_segment_archive,
)


@dataclass(frozen=True)
class _SyntheticState:
    time_s: float
    temperature_k: tuple[float, ...]
    material_coordinate: tuple[float, ...]
    materials: tuple[dict, ...]
    width_m: float = 100_000.0
    initial_width_m: float = 100_000.0
    crust_m: float = 28_000.0
    initial_crust_m: float = 28_000.0
    lithosphere_m: float = 80_000.0
    initial_lithosphere_m: float = 80_000.0
    beta: float = 1.0
    accumulated_strain: float = 0.0
    crust_fraction: float = 0.35
    surface_temperature_k: float = 280.0
    base_temperature_k: float = 1000.0

    def payload(self):
        return {"schema": "SYNTHETIC_TEST_STATE_V1", "time_s": self.time_s,
                "initial_width_m": self.initial_width_m, "width_m": self.width_m,
                "initial_crust_m": self.initial_crust_m, "initial_lithosphere_m": self.initial_lithosphere_m,
                "crust_m": self.crust_m, "lithosphere_m": self.lithosphere_m,
                "beta": self.beta, "accumulated_strain": self.accumulated_strain,
                "crust_fraction": self.crust_fraction,
                "material_coordinate": list(self.material_coordinate),
                "temperature_k": list(self.temperature_k), "materials": list(self.materials),
                "surface_temperature_k": self.surface_temperature_k,
                "base_temperature_k": self.base_temperature_k}


def _state(time_s: float = 0.0, cooling: float = 0.0) -> _SyntheticState:
    n = 73
    material = {"role_id": "SYNTHETIC_TEST_MATERIAL", "k_w_m_k": 3.0,
                "rho_kg_m3": 2800.0, "cp_j_kg_k": 1000.0, "radiogenic_w_m3": 1e-6}
    materials = tuple(dict(material) for _ in range(n))
    coordinate = tuple(i / (n - 1) for i in range(n))
    return _SyntheticState(time_s, tuple(280.0 + i * 10.0 - cooling for i in range(n)),
                           coordinate, materials)


def _provenance() -> dict:
    digest = hashlib.sha256(b"synthetic test fixture").hexdigest()
    return {
        "identity_status": "SYNTHETIC_TEST_ONLY",
        "source_commit": "TEST_ONLY",
        "source_composite_sha256": digest,
        "configuration_sha256": digest,
        "provider_identities": {"synthetic_provider": digest},
        "input_identities": {"synthetic_input": digest},
    }


def _capture(root: Path):
    start = _state()
    states = [start, _state(1.0, 0.1), _state(2.0, 0.2), _state(3.0, 0.3)]
    writer = SegmentArchiveWriter(root, segment_id="synthetic-segment-01",
                                  provenance=_provenance(), expected_trajectory_count=1)
    with writer.trajectory(trajectory_id="direct-test-01", support_id="TEST-C028",
                           trajectory_kind="DIRECT", resolution_factor=0.0005,
                           start_time_s=start.time_s,
                           requested_duration_s=3.0):
        for state in states:
            writer.observe(state)
        final = states[-1]
        writer.complete_trajectory(final, integration_substeps=3)
    manifest = writer.finalize()
    return start, final, states, manifest


def test_stream_archive_roundtrips_every_synthetic_observation_and_measures_size(tmp_path):
    root = tmp_path / "segment"
    start, final, observed, manifest = _capture(root)

    assert observed[0] == start and observed[-1] == final
    assert len(observed) == 4
    verified = validate_segment_archive(root)
    assert verified["status"] == "SEGMENT_ARCHIVE_VALID"
    assert verified["state_count"] == len(observed)
    assert manifest["checkpoint_capability"] == "NOT_QUALIFIED_AS_RESTARTABLE"
    assert not (root / INCOMPLETE_NAME).exists()

    records = [json.loads(line) for line in (root / STATE_STREAM).read_text(encoding="utf-8").splitlines()]
    assert len(records) == len(observed)
    for i, (record, state) in enumerate(zip(records, observed)):
        assert record["sequence"] == i
        assert record["time_s"] == state.time_s
        assert record["time_s_hex"] == state.time_s.hex()
        assert record["state"] == state.payload()
        assert record["record_type"] == ("INITIAL_INTEGRATOR_STATE" if i == 0 else "INTEGRATOR_SUBSTEP_STATE")
        assert record["state_class"] == "DIAGNOSTIC_OBSERVATION"
        assert record["checkpoint_capability"] == "NOT_QUALIFIED_AS_RESTARTABLE"
        assert record["state"] == state.payload()
    assert manifest["state_stream"]["bytes"] == (root / STATE_STREAM).stat().st_size
    assert manifest["state_stream"]["bytes"] > 0


def test_interrupted_or_unfinished_archive_is_never_valid_complete(tmp_path):
    root = tmp_path / "partial"
    writer = SegmentArchiveWriter(root, segment_id="synthetic-partial",
                                  provenance=_provenance(), expected_trajectory_count=1)
    with pytest.raises(SegmentArchiveError, match="TRAJECTORY_NOT_EXPLICITLY_COMPLETED"):
        with writer.trajectory(trajectory_id="t1", support_id="TEST-C028",
                               trajectory_kind="DIRECT", resolution_factor=0.0005,
                               start_time_s=0.0, requested_duration_s=1.0):
            writer.observe(_state())
    writer.close_incomplete("TEST_ABORT")
    assert (root / INCOMPLETE_NAME).is_file()
    assert not (root / MANIFEST_NAME).exists()
    with pytest.raises(SegmentArchiveError, match="ARCHIVE_MISSING_OR_INCOMPLETE"):
        validate_segment_archive(root)


def test_observer_failure_preserves_incomplete_marker_and_prevents_manifest(tmp_path):
    root = tmp_path / "observer-failure"
    writer = SegmentArchiveWriter(root, segment_id="synthetic-io-failure",
                                  provenance=_provenance(), expected_trajectory_count=1)
    states_seen = 0
    with pytest.raises(OSError, match="synthetic telemetry failure"):
        with writer.trajectory(trajectory_id="t1", support_id="TEST-C028",
                               trajectory_kind="DIRECT", resolution_factor=0.0005,
                               start_time_s=0.0, requested_duration_s=3.0):
            def fail_after_initial(state):
                nonlocal states_seen
                writer.observe(state)
                states_seen += 1
                if states_seen == 2:
                    raise OSError("synthetic telemetry failure")
            for state in (_state(), _state(1.0), _state(2.0)):
                fail_after_initial(state)
    writer.close_incomplete("OBSERVER_FAILED")
    assert states_seen == 2
    assert (root / INCOMPLETE_NAME).is_file()
    assert not (root / MANIFEST_NAME).exists()


def test_payload_tampering_fails_stream_integrity(tmp_path):
    root = tmp_path / "tamper"
    _capture(root)
    path = root / STATE_STREAM
    raw = path.read_bytes()
    path.write_bytes(raw.replace(b"TEST-C028", b"TEST-C029", 1))
    with pytest.raises(SegmentArchiveError, match="TRAJECTORY_IDENTITY_CHANGED_IN_STREAM"):
        validate_segment_archive(root)


def test_provenance_missing_identity_and_existing_destination_fail_closed(tmp_path):
    root = tmp_path / "bad-provenance"
    incomplete = _provenance()
    del incomplete["provider_identities"]
    with pytest.raises(SegmentArchiveError, match="PROVENANCE_FIELDS_INCOMPLETE"):
        SegmentArchiveWriter(root, segment_id="bad", provenance=incomplete,
                             expected_trajectory_count=1)
    valid = tmp_path / "existing"
    valid.mkdir()
    with pytest.raises(SegmentArchiveError, match="DESTINATION_ALREADY_EXISTS"):
        SegmentArchiveWriter(valid, segment_id="bad", provenance=_provenance(),
                             expected_trajectory_count=1)
