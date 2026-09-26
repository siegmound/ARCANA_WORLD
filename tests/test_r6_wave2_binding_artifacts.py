from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from arcana_worldsim.r6.bootstrap import create_bootstrap_manifest
from arcana_worldsim.r6.repository_context import canonical_text_sha256


ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_wave2_authority_and_bootstrap_artifacts_are_consistent():
    anchors = [200, 125, 120, 20, 15, 14, 13, 12, 11, 10, 5, 0]
    clock = load("R6_TEMPORAL_SUPPORT_REGISTRY.json")
    initial = load("R6_CANONICAL_INITIAL_STATE_BINDING.json")
    adjudication = load("R6_WAVE2_ADJUDICATION.json")
    reconciliation = load("R6_WAVE2_TARGETED_AUTHORITY_RECONCILIATION.json")
    bootstrap = load("R6_BOOTSTRAP_MANIFEST.json")
    providers = load("R6_PROVIDER_REGISTRY.json")
    climate = load("R6_CLIMATE_SUPPORT_MATRIX.json")

    assert clock["hard_authority_anchors_ka"] == anchors
    assert clock["hard_anchor_count"] == 12 and clock["interval_count"] == 11
    source = ROOT / clock["source_clock"]["path"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == clock["source_clock"]["source_sha256"]
    with np.load(source, allow_pickle=False) as archive:
        ages = archive["age_ka"]
    assert ages.shape == (280,) and ages.dtype == np.dtype("float64")
    assert np.isfinite(ages).all() and np.all(np.diff(ages) < 0)
    assert len(ages) == len(np.unique(ages))
    assert all(np.any(ages == anchor) for anchor in anchors)
    assert hashlib.sha256(ages.tobytes(order="C")).hexdigest() == clock["source_clock"][
        "coordinate_sha256_little_endian_c_order"]

    assert initial["canonical_initial_world_bound"] is False
    assert adjudication["first_real_scientific_state"]["state_count"] == 0
    assert adjudication["scientific_simulation"] is False
    assert adjudication["provider_acquisition"] is False
    assert adjudication["unknown_preserved"] is True
    assert len(climate["anchor_support"]) == len(anchors)
    assert len(providers["providers"]) == 4
    assert reconciliation["global_authority_register_rebuilt"] is False

    recomputed = create_bootstrap_manifest(bootstrap["identity"]["inputs"])
    for key in ("bootstrap_identity_sha256", "run_id", "history_id", "branch_id",
                "canonical_initial_state_bound", "scientific_execution_authorized"):
        assert recomputed[key] == bootstrap[key]
    portable_text = bootstrap["dependency_checkout_sha256"]
    for relpath, digest in bootstrap["identity"]["inputs"]["dependency_sha256"].items():
        if relpath in portable_text:
            checkout = portable_text[relpath]
            assert checkout["historical_raw_sha256"] == digest
            assert canonical_text_sha256(ROOT / relpath) == checkout["canonical_lf_sha256"]
        else:
            assert hashlib.sha256((ROOT / relpath).read_bytes()).hexdigest() == digest
