from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

pytest.importorskip("numpy", reason="NumPy unavailable; reduced-kernel continuity tests require NumPy")

from arcana_worldsim.r6.functional_development import (  # noqa: E402
    NodeMaterial, ReducedState, _diffusion_stability_limit, pure_shear_thermal_step,
)
from arcana_worldsim.r6.segment_archive import SegmentArchiveError, SegmentArchiveWriter  # noqa: E402
from arcana_worldsim.r6.segment_continuation import (  # noqa: E402
    bind_completed_segment, build_continuation_manifest,
    create_qualified_checkpoint, load_qualified_checkpoint,
    validate_continuation_manifest, write_continuation_manifest,
    write_qualified_checkpoint,
)


def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                  ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _state(time_s=0.0):
    count = 73
    crust = NodeMaterial("TEST_CRUST", 3.0, 2800.0, 1000.0, 1e-6)
    mantle = NodeMaterial("TEST_MANTLE", 4.0, 3300.0, 1100.0, 0.0)
    materials = tuple(crust if i < 26 else mantle for i in range(count))
    return ReducedState(
        time_s=time_s, initial_width_m=100_000.0, width_m=100_000.0,
        initial_crust_m=28_000.0, initial_lithosphere_m=80_000.0,
        crust_m=28_000.0, lithosphere_m=80_000.0, beta=1.0,
        accumulated_strain=0.0, crust_fraction=0.35,
        material_coordinate=tuple(i / (count - 1) for i in range(count)),
        temperature_k=tuple(280.0 + i * 10.0 for i in range(count)),
        materials=materials, surface_temperature_k=280.0, base_temperature_k=1000.0,
    )


def _identities():
    config = {"kernel": "pure_shear_thermal_step", "fixture": "TEST_ONLY", "v": 1}
    d = _sha(config)
    other = hashlib.sha256(b"test identity").hexdigest()
    provenance = {"identity_status": "SYNTHETIC_TEST_ONLY", "source_commit": "TEST_ONLY",
                  "source_composite_sha256": other, "configuration_sha256": d,
                  "provider_identities": {"fixture_provider": other},
                  "input_identities": {"fixture_input": other}}
    return config, provenance, other


def _run_segment(root, *, segment_id, trajectory_id, start, duration, config, provenance):
    writer = SegmentArchiveWriter(root, segment_id=segment_id, provenance=provenance,
                                  expected_trajectory_count=1)
    observed = []
    with writer.trajectory(trajectory_id=trajectory_id, support_id="SYNTHETIC_SUPPORT",
                           trajectory_kind="DIRECT", resolution_factor=0.0005,
                           start_time_s=start.time_s, requested_duration_s=duration):
        final, diagnostics = pure_shear_thermal_step(
            start, duration_s=duration, extension_velocity_m_s=1.0e-12,
            maximum_kinematic_fraction_per_substep=0.01,
            state_observer=observed.append,
        )
        writer.observe(start)
        for state in observed[1:]:
            writer.observe(state)
        writer.complete_trajectory(final, integration_substeps=diagnostics.substeps)
    writer.finalize()
    kwargs = {"model_identity_sha256": _sha({"model": "synthetic"}),
              "model_configuration_sha256": _sha(config),
              "forcing_identity_sha256": _sha({"forcing": "constant-test-only"}),
              "numerical_configuration": config}
    binding = bind_completed_segment(root, trajectory_id=trajectory_id, **kwargs)
    return final, observed, binding


def test_qualified_checkpoint_and_two_segments_match_continuous_kernel(tmp_path):
    config, provenance, _ = _identities()
    initial = _state()
    continuous_observations = []
    z = tuple(value * initial.lithosphere_m for value in initial.material_coordinate)
    total_duration = _diffusion_stability_limit(z, initial.materials) * 0.8 * 1.5
    continuous_final, _ = pure_shear_thermal_step(
        initial, duration_s=total_duration, extension_velocity_m_s=1.0e-12,
        maximum_kinematic_fraction_per_substep=0.01,
        state_observer=continuous_observations.append,
    )
    assert len(continuous_observations) >= 3
    split_state = continuous_observations[1]
    first_duration = split_state.time_s - initial.time_s
    second_duration = total_duration - first_duration

    first_root = tmp_path / "segment-1"
    first_final, _, first_binding = _run_segment(
        first_root, segment_id="segment-one", trajectory_id="trajectory-one",
        start=initial, duration=first_duration, config=config, provenance=provenance)
    assert first_final.payload() == split_state.payload()
    checkpoint = create_qualified_checkpoint(first_root, first_binding, first_final)
    checkpoint_path = tmp_path / "checkpoint.json"
    write_qualified_checkpoint(checkpoint_path, checkpoint)
    reopened_checkpoint, restored = load_qualified_checkpoint(checkpoint_path)
    assert restored.payload() == first_final.payload()
    assert reopened_checkpoint.checkpoint_id == checkpoint.checkpoint_id

    second_root = tmp_path / "segment-2"
    second_final, _, second_binding = _run_segment(
        second_root, segment_id="segment-two", trajectory_id="trajectory-two",
        start=restored, duration=second_duration, config=config, provenance=provenance)
    assert second_final.payload() == continuous_final.payload()

    chain = build_continuation_manifest([first_binding, second_binding], [reopened_checkpoint])
    assert chain["status"] == "CHAIN_VALIDATED_HASH_BOUND_NOT_EXECUTED"
    assert validate_continuation_manifest(chain) == chain
    chain_path = tmp_path / "continuation.json"
    chain_file_sha = write_continuation_manifest(chain_path, chain)
    assert chain_file_sha == hashlib.sha256(chain_path.read_bytes()).hexdigest()
    assert validate_continuation_manifest(json.loads(chain_path.read_text(encoding="utf-8"))) == chain
    tampered = dict(chain)
    tampered["segments"] = list(chain["segments"])
    tampered["segments"][1] = dict(tampered["segments"][1], start_time_s=-1.0)
    with pytest.raises(SegmentArchiveError, match="DIGEST_OR_STATUS_INVALID"):
        validate_continuation_manifest(tampered)


def test_checkpoint_digest_and_endpoint_are_fail_closed(tmp_path):
    config, provenance, _ = _identities()
    initial = _state()
    root = tmp_path / "one"
    final, _, binding = _run_segment(root, segment_id="one", trajectory_id="t-one",
                                     start=initial, duration=100.0, config=config,
                                     provenance=provenance)
    checkpoint = create_qualified_checkpoint(root, binding, final)
    damaged = checkpoint.to_dict()
    damaged["state_payload"]["width_m"] += 1.0
    path = tmp_path / "damaged.json"
    path.write_text(json.dumps(damaged), encoding="utf-8")
    with pytest.raises(SegmentArchiveError, match="IDENTITY_MISMATCH|STATE_DIGEST_MISMATCH"):
        load_qualified_checkpoint(path)
    with pytest.raises(SegmentArchiveError, match="NOT_ARCHIVED_SEGMENT_ENDPOINT"):
        create_qualified_checkpoint(root, binding, initial)


def test_chain_rejects_time_state_and_model_mismatch(tmp_path):
    config, provenance, _ = _identities()
    initial = _state()
    first_root = tmp_path / "first"
    first_final, _, first_binding = _run_segment(first_root, segment_id="first",
        trajectory_id="t-first", start=initial, duration=100.0,
        config=config, provenance=provenance)
    checkpoint = create_qualified_checkpoint(first_root, first_binding, first_final)
    second_root = tmp_path / "second"
    _, _, second_binding = _run_segment(second_root, segment_id="second",
        trajectory_id="t-second", start=replace(first_final, time_s=first_final.time_s + 1.0),
        duration=100.0, config=config, provenance=provenance)
    with pytest.raises(SegmentArchiveError, match="IDENTITY_MISMATCH|BOUNDARY_STATE_OR_TIME_MISMATCH"):
        build_continuation_manifest([first_binding, second_binding], [checkpoint])

    compatible_root = tmp_path / "compatible-time"
    _, _, compatible = _run_segment(compatible_root, segment_id="compatible",
        trajectory_id="t-compatible", start=first_final, duration=100.0,
        config=config, provenance=provenance)
    with pytest.raises(SegmentArchiveError, match="IDENTITY_MISMATCH:forcing_identity_sha256"):
        build_continuation_manifest(
            [first_binding, replace(compatible, forcing_identity_sha256=_sha({"other": "forcing"}))],
            [checkpoint],
        )
    with pytest.raises(SegmentArchiveError, match="IDENTITY_MISMATCH:provider_identities"):
        build_continuation_manifest(
            [first_binding, replace(compatible, provider_identities={"other": _sha("provider")})],
            [checkpoint],
        )


def test_provider_and_configuration_digests_are_not_silently_substituted(tmp_path):
    config, provenance, _ = _identities()
    initial = _state()
    root = tmp_path / "valid"
    _run_segment(root, segment_id="valid", trajectory_id="t", start=initial,
                 duration=100.0, config=config, provenance=provenance)
    with pytest.raises(SegmentArchiveError, match="MODEL_CONFIGURATION_DIGEST_MISMATCH"):
        bind_completed_segment(root, trajectory_id="t",
            model_identity_sha256=_sha({"model": "synthetic"}),
            model_configuration_sha256=_sha({"other": True}),
            forcing_identity_sha256=_sha({"forcing": "constant-test-only"}),
            numerical_configuration=config)
