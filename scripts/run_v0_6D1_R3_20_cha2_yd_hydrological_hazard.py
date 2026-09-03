from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arcana_worldsim.late_cenozoic.cha2_nested_50y import CHA2Nested50YRecentProvider
from arcana_worldsim.late_cenozoic import sealed_120ka_boundary as b1
from arcana_worldsim.late_cenozoic import cha2_hydrological_hazard as r320

EXPECTED_C1_SHA = "d0b121f0b0fe7214d6c6f4736176d1c64f419c77dd991659291fe12b633ada0f"
EXPECTED_R319_JSON = "658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71"
EXPECTED_R319_NPZ = "f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406"
EXPECTED_R319_VERDICT = "PASS_R319_CANONICAL_125KA_TO_0_H0_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY__0KA_NATURAL_CONTROL_BIOLOGY_BOUNDARY_SEALED"


def hfile(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def validate_parent() -> dict:
    sealp = ROOT / "R3_19_SEAL_SUMMARY.json"
    jp = ROOT / "local_runs/v0_6D1_R3_19/WORLD1_H0_0KA_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY_CHECKPOINT_v0_6D1_R3_19.json"
    npzp = jp.with_suffix(".npz")
    for p in (sealp, jp, npzp):
        if not p.is_file():
            raise RuntimeError(f"R3.20 requires R3.19 SEALED evidence: missing {p}")
    seal = json.loads(sealp.read_text(encoding="utf-8"))
    if seal.get("verdict") != EXPECTED_R319_VERDICT:
        raise RuntimeError(f"R3.19 seal verdict mismatch: {seal.get('verdict')}")
    seal_checks = seal.get("formal_audit_checks", seal.get("checks"))
    if str(seal_checks) != "73/73":
        raise RuntimeError(f"R3.19 seal must be 73/73; got {seal_checks!r}")
    gotj, gotn = hfile(jp), hfile(npzp)
    if gotj != EXPECTED_R319_JSON or gotn != EXPECTED_R319_NPZ:
        raise RuntimeError("R3.19 canonical checkpoint SHA mismatch")
    return {"seal": str(sealp), "checkpoint_json_sha256": gotj, "checkpoint_npz_sha256": gotn}


def load_a1() -> dict[str, np.ndarray]:
    p = ROOT / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz"
    z = np.load(p, allow_pickle=False)
    return {k: z[k] for k in z.files}


def build_provider(a1):
    sealed_root = ROOT / "local_bindings/v0_6D1_R3_14/v0_6_1_SEALED_MINIMAL"
    b1.verify_v061_sealed_root(sealed_root)
    c1_path = ROOT / "src/arcana_worldsim/late_cenozoic/cha2_nested_50y.py"
    if hfile(c1_path) != EXPECTED_C1_SHA:
        raise RuntimeError("R3.20 refuses modified CHA2 C1 authority")
    return CHA2Nested50YRecentProvider(a1, sealed_root), sealed_root


def main() -> int:
    t0 = time.perf_counter()
    parent = validate_parent()
    a1 = load_a1()
    provider, sealed_root = build_provider(a1)
    mag = r320.audit_younger_dryas_class_magnitude(provider, a1)
    outdir = ROOT / "local_runs/v0_6D1_R3_20"
    outdir.mkdir(parents=True, exist_ok=True)
    if not mag["passed"]:
        blocker = {
            "stage": r320.STAGE,
            "verdict": "FAIL_CLOSED_R320_CHA2_OUTSIDE_YOUNGER_DRYAS_CLASS_ENVELOPE",
            "parent_r319": parent,
            "magnitude_audit": mag,
            "cha2_c1_modified": False,
            "biology_modified": False,
            "human_or_cultural_target_used": False,
        }
        p = outdir / "R3_20_CHA2_MAGNITUDE_BLOCKER.json"
        p.write_text(json.dumps(blocker, indent=2), encoding="utf-8")
        print(json.dumps(blocker, indent=2))
        return 2

    hz = r320.build_hazard_timeseries(provider, a1)
    npz_path = outdir / "R3_20_CHA2_15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_FIELDS.npz"
    payload = {
        "years_before_book": hz["years_before_book"],
        "severe_flood_candidate_fraction": hz["severe_flood_candidate_fraction"],
    }
    for k, v in hz["fields"].items():
        payload[k] = v
    np.savez_compressed(npz_path, **payload)

    peak_i = int(np.argmax(hz["severe_flood_candidate_fraction"]))
    peak_year = int(hz["years_before_book"][peak_i])
    peak_compound = np.asarray(hz["fields"]["compound_flood_hazard_index"][peak_i], dtype=float)
    peak_active = peak_compound >= r320.HydrologicalHazardConfig().severe_candidate_threshold
    lat = np.asarray(a1["lat"], dtype=float)
    bands = np.floor((lat + 90.0) / 10.0).astype(int)
    active_bands = sorted({int(bands[i]) for i in range(len(lat)) if np.any(peak_active[i])})

    summary = {
        "stage": r320.STAGE,
        "schema": r320.SCHEMA,
        "verdict": "PASS_R320_CHA2_YOUNGER_DRYAS_CLASS_MAGNITUDE_CONFIRMED__15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_LAYER_READY",
        "wall_seconds": time.perf_counter() - t0,
        "parent_r319": parent,
        "sealed_v061_hashes": b1.verify_v061_sealed_root(sealed_root),
        "cha2_c1_sha256": EXPECTED_C1_SHA,
        "magnitude_audit": mag,
        "hazard_timeseries": {
            "start_year_before_book": int(hz["years_before_book"][0]),
            "end_year_before_book": int(hz["years_before_book"][-1]),
            "step_years": 50,
            "state_count": int(len(hz["years_before_book"])),
            "peak_severe_fraction": float(hz["peak_severe_fraction"]),
            "peak_severe_fraction_year_before_book": peak_year,
            "peak_compound_hazard_max": float(np.max(peak_compound)),
            "active_10deg_latitude_band_count_at_peak": int(len(active_bands)),
            "active_10deg_latitude_bands_at_peak": active_bands,
            "npz": str(npz_path),
            "npz_sha256": hfile(npz_path),
        },
        "governance": {
            "cha2_c1_modified": False,
            "r319_h0_state_modified": False,
            "biology_modified": False,
            "impact_origin_required": False,
            "human_population_used": False,
            "settlement_target_used": False,
            "flood_myth_target_used": False,
            "religion_target_used": False,
            "hazard_indices_are_diagnostic_rankings_not_flood_depths": True,
            "future_human_replay_may_consume_hazard_fields": True,
        },
    }
    sp = outdir / "R3_20_CHA2_YD_MAGNITUDE_AND_HYDROLOGICAL_HAZARD_SUMMARY.json"
    sp.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({
        "stage": summary["stage"], "verdict": summary["verdict"],
        "wall_seconds": summary["wall_seconds"],
        "classification": mag["classification"], "magnitude_metrics": mag["metrics"],
        "hazard": summary["hazard_timeseries"], "summary": str(sp),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
