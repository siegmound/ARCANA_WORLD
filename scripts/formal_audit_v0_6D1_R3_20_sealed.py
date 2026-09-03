from __future__ import annotations

import argparse
import json
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np

ROOT0 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT0 / "src"))

from arcana_worldsim.late_cenozoic import sealed_120ka_boundary as b1
from arcana_worldsim.late_cenozoic.cha2_nested_50y import CHA2Nested50YRecentProvider
from arcana_worldsim.late_cenozoic import cha2_hydrological_hazard as r320

STAGE = "v0.6D1-R3.20"
CANONICAL_VERDICT = "PASS_R320_CHA2_YOUNGER_DRYAS_CLASS_MAGNITUDE_CONFIRMED__15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_LAYER_READY"
SEALED_VERDICT = "PASS_R320_CHA2_YOUNGER_DRYAS_CLASS_MAGNITUDE_AND_15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_LAYER_SEALED"
EXPECTED_SUMMARY_SHA256 = "ab5abbe28bccab3df2d18384ff9563e71d82af4d6a59a4e5484ab5c2b5116cab"
EXPECTED_NPZ_SHA256 = "4319f6464f96014e372e241a9c4b8d801bc945124153a3c9cef6dd25fcb5fb14"
EXPECTED_C1_SHA256 = "d0b121f0b0fe7214d6c6f4736176d1c64f419c77dd991659291fe12b633ada0f"
EXPECTED_R319_VERDICT = "PASS_R319_CANONICAL_125KA_TO_0_H0_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY__0KA_NATURAL_CONTROL_BIOLOGY_BOUNDARY_SEALED"
EXPECTED_R319_JSON_SHA256 = "658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71"
EXPECTED_R319_NPZ_SHA256 = "f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406"
EXPECTED_METRICS = {
    "baseline_overturning_strength": 0.98922412840008,
    "freshwater_peak_sv": 0.20270779797753885,
    "freshwater_peak_year_before_book": -12900,
    "minimum_overturning_strength": 0.3756271044587676,
    "minimum_overturning_fraction_of_baseline": 0.3797189066407908,
    "minimum_overturning_year_before_book": -12850,
    "strong_suppression_duration_years": 1300.0,
    "strong_suppression_start_year_before_book": -13200,
    "strong_suppression_end_year_before_book": -11950,
    "event_exit_year_before_book": -11900,
    "full_recovery_year_before_book_diagnostic": -10500,
    "maximum_northern_local_cooling_c": 4.918580792825181,
    "maximum_northern_local_cooling_year_before_book": -12850,
    "northern_active_land_fraction_cooling_at_least_2c_at_peak": 1.0,
    "maximum_global_state_cooling_c_diagnostic": 0.09231673360365544,
    "maximum_global_state_cooling_year_before_book_diagnostic": -12750,
}
EXPECTED_PEAK_SEVERE_FRACTION = 0.0005143151037202125
EXPECTED_PEAK_SEVERE_YEAR = -11300
EXPECTED_ACTIVE_BANDS = [0, 5, 12]


def hfile(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def feq(a: Any, b: float, atol: float = 1e-12) -> bool:
    try:
        return abs(float(a) - float(b)) <= atol
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seal-out", type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve(); run = args.run_dir.resolve(); out = args.out.resolve(); seal_out = args.seal_out.resolve()

    sump = run / "R3_20_CHA2_YD_MAGNITUDE_AND_HYDROLOGICAL_HAZARD_SUMMARY.json"
    npzp = run / "R3_20_CHA2_15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_FIELDS.npz"
    checks: list[dict[str, Any]] = []
    def ck(name: str, passed: bool, actual: Any=None, expected: Any=None) -> None:
        checks.append({"name": name, "pass": bool(passed), "actual": actual, "expected": expected})

    ck("summary_exists", sump.is_file(), str(sump), "file")
    ck("npz_exists", npzp.is_file(), str(npzp), "file")
    if not sump.is_file() or not npzp.is_file():
        failed=[x for x in checks if not x["pass"]]
        audit={"schema":"ARCANA_R320_FORMAL_SEALED_AUDIT_V1","stage":STAGE,"verdict":"FAIL_R320_SEALED_AUDIT","checks":f"{len(checks)-len(failed)}/{len(checks)}","failed":failed,"check_rows":checks}
        out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(audit,indent=2),encoding="utf-8")
        print(json.dumps({"verdict":audit["verdict"],"checks":audit["checks"],"audit":str(out)},indent=2)); return 1

    summary=json.loads(sump.read_text(encoding="utf-8"))
    sh=hfile(sump); nh=hfile(npzp)
    ck("summary_sha_exact", sh==EXPECTED_SUMMARY_SHA256, sh, EXPECTED_SUMMARY_SHA256)
    ck("npz_sha_exact", nh==EXPECTED_NPZ_SHA256, nh, EXPECTED_NPZ_SHA256)
    ck("summary_stage", summary.get("stage")==STAGE, summary.get("stage"), STAGE)
    ck("summary_schema", summary.get("schema")==r320.SCHEMA, summary.get("schema"), r320.SCHEMA)
    ck("summary_verdict", summary.get("verdict")==CANONICAL_VERDICT, summary.get("verdict"), CANONICAL_VERDICT)
    ck("cha2_c1_hash_pointer", summary.get("cha2_c1_sha256")==EXPECTED_C1_SHA256, summary.get("cha2_c1_sha256"), EXPECTED_C1_SHA256)

    mag=summary.get("magnitude_audit", {})
    ck("magnitude_schema_v2", mag.get("schema")=="ARCANA_R320_YD_CLASS_MAGNITUDE_AUDIT_V2", mag.get("schema"), "ARCANA_R320_YD_CLASS_MAGNITUDE_AUDIT_V2")
    ck("magnitude_r1_revision", mag.get("audit_revision")=="R1_METRIC_AND_PARENT_SCHEMA_REPAIR", mag.get("audit_revision"), "R1_METRIC_AND_PARENT_SCHEMA_REPAIR")
    ck("magnitude_class_yd", mag.get("classification")=="YOUNGER_DRYAS_CLASS", mag.get("classification"), "YOUNGER_DRYAS_CLASS")
    ck("magnitude_passed", mag.get("passed") is True, mag.get("passed"), True)
    for name,val in mag.get("checks",{}).items(): ck(f"magnitude_gate::{name}", val is True, val, True)
    mm=mag.get("metrics",{})
    for k,v in EXPECTED_METRICS.items():
        if isinstance(v,int): ck(f"metric_exact::{k}", mm.get(k)==v, mm.get(k), v)
        else: ck(f"metric_exact::{k}", feq(mm.get(k),v,1e-12), mm.get(k), v)
    mgov=mag.get("governance",{})
    for k in ("impact_origin_required","human_population_used","settlement_target_used","flood_myth_target_used","religion_target_used","biology_modified","cha2_c1_modified","global_temperature_scalar_magnitude_is_hard_gate","full_90pct_overturning_recovery_is_hard_gate"):
        ck(f"magnitude_governance_false::{k}", mgov.get(k) is False, mgov.get(k), False)
    ck("event_exit_same_80pct_regime", mgov.get("event_exit_uses_same_80pct_threshold_as_strong_suppression") is True, mgov.get("event_exit_uses_same_80pct_threshold_as_strong_suppression"), True)

    hzsum=summary.get("hazard_timeseries",{})
    ck("hazard_start", hzsum.get("start_year_before_book")==-14950, hzsum.get("start_year_before_book"), -14950)
    ck("hazard_end", hzsum.get("end_year_before_book")==-11000, hzsum.get("end_year_before_book"), -11000)
    ck("hazard_step_50", hzsum.get("step_years")==50, hzsum.get("step_years"), 50)
    ck("hazard_state_count_80", hzsum.get("state_count")==80, hzsum.get("state_count"), 80)
    ck("hazard_peak_severe_fraction", feq(hzsum.get("peak_severe_fraction"),EXPECTED_PEAK_SEVERE_FRACTION,1e-15), hzsum.get("peak_severe_fraction"), EXPECTED_PEAK_SEVERE_FRACTION)
    ck("hazard_peak_severe_year", hzsum.get("peak_severe_fraction_year_before_book")==EXPECTED_PEAK_SEVERE_YEAR, hzsum.get("peak_severe_fraction_year_before_book"), EXPECTED_PEAK_SEVERE_YEAR)
    ck("hazard_compound_peak_1", feq(hzsum.get("peak_compound_hazard_max"),1.0,0.0), hzsum.get("peak_compound_hazard_max"), 1.0)
    ck("hazard_active_band_count_3", hzsum.get("active_10deg_latitude_band_count_at_peak")==3, hzsum.get("active_10deg_latitude_band_count_at_peak"), 3)
    ck("hazard_active_bands_exact", hzsum.get("active_10deg_latitude_bands_at_peak")==EXPECTED_ACTIVE_BANDS, hzsum.get("active_10deg_latitude_bands_at_peak"), EXPECTED_ACTIVE_BANDS)
    gov=summary.get("governance",{})
    for k in ("cha2_c1_modified","r319_h0_state_modified","biology_modified","impact_origin_required","human_population_used","settlement_target_used","flood_myth_target_used","religion_target_used"):
        ck(f"summary_governance_false::{k}", gov.get(k) is False, gov.get(k), False)
    ck("hazard_rankings_not_depths", gov.get("hazard_indices_are_diagnostic_rankings_not_flood_depths") is True, gov.get("hazard_indices_are_diagnostic_rankings_not_flood_depths"), True)
    ck("future_human_replay_allowed", gov.get("future_human_replay_may_consume_hazard_fields") is True, gov.get("future_human_replay_may_consume_hazard_fields"), True)

    # Parent H0 must remain exactly SEALED and untouched.
    sealp=root/"R3_19_SEAL_SUMMARY.json"
    r319j=root/"local_runs/v0_6D1_R3_19/WORLD1_H0_0KA_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY_CHECKPOINT_v0_6D1_R3_19.json"
    r319n=r319j.with_suffix(".npz")
    ck("r319_seal_exists", sealp.is_file(), str(sealp), "file")
    if sealp.is_file():
        s=json.loads(sealp.read_text(encoding="utf-8")); sc=s.get("formal_audit_checks",s.get("checks"))
        ck("r319_seal_verdict", s.get("verdict")==EXPECTED_R319_VERDICT, s.get("verdict"), EXPECTED_R319_VERDICT)
        ck("r319_seal_73_73", str(sc)=="73/73", sc, "73/73")
    ck("r319_json_exists", r319j.is_file(), str(r319j), "file")
    ck("r319_npz_exists", r319n.is_file(), str(r319n), "file")
    if r319j.is_file(): ck("r319_json_sha_exact", hfile(r319j)==EXPECTED_R319_JSON_SHA256, hfile(r319j), EXPECTED_R319_JSON_SHA256)
    if r319n.is_file(): ck("r319_npz_sha_exact", hfile(r319n)==EXPECTED_R319_NPZ_SHA256, hfile(r319n), EXPECTED_R319_NPZ_SHA256)

    c1p=root/"src/arcana_worldsim/late_cenozoic/cha2_nested_50y.py"
    ck("c1_exists", c1p.is_file(), str(c1p), "file")
    if c1p.is_file(): ck("c1_sha_frozen", hfile(c1p)==EXPECTED_C1_SHA256, hfile(c1p), EXPECTED_C1_SHA256)

    # Full independent replay from SEALED provider + A1.
    sealed_root=root/"local_bindings/v0_6D1_R3_14/v0_6_1_SEALED_MINIMAL"
    a1p=root/"references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz"
    ck("v061_binding_exists", sealed_root.is_dir(), str(sealed_root), "dir")
    ck("a1_exists", a1p.is_file(), str(a1p), "file")
    replay_mag=None; replay_hz=None
    if sealed_root.is_dir() and a1p.is_file():
        try:
            hashes=b1.verify_v061_sealed_root(sealed_root)
            for key,want in b1.EXPECTED.items(): ck(f"v061_sha::{key}", hashes.get(key)==want, hashes.get(key), want)
            z=np.load(a1p,allow_pickle=False); a1={k:z[k] for k in z.files}
            provider=CHA2Nested50YRecentProvider(a1,sealed_root)
            replay_mag=r320.audit_younger_dryas_class_magnitude(provider,a1)
            ck("replay_mag_pass", replay_mag.get("passed") is True, replay_mag.get("passed"), True)
            ck("replay_mag_class", replay_mag.get("classification")=="YOUNGER_DRYAS_CLASS", replay_mag.get("classification"), "YOUNGER_DRYAS_CLASS")
            ck("replay_mag_exact_summary", replay_mag==mag, replay_mag.get("metrics"), mm)
            replay_hz=r320.build_hazard_timeseries(provider,a1)
            with np.load(npzp,allow_pickle=False) as stored:
                expected_keys=["years_before_book","severe_flood_candidate_fraction"]+list(replay_hz["fields"].keys())
                ck("npz_keys_exact", set(stored.files)==set(expected_keys), stored.files, expected_keys)
                ck("npz_years_bit_exact", np.array_equal(stored["years_before_book"],replay_hz["years_before_book"]), None, "array_equal")
                ck("npz_severe_fraction_bit_exact", np.array_equal(stored["severe_flood_candidate_fraction"],replay_hz["severe_flood_candidate_fraction"]), None, "array_equal")
                for k,v in replay_hz["fields"].items(): ck(f"npz_field_bit_exact::{k}", np.array_equal(stored[k],v), None, "array_equal")
                for k in stored.files:
                    a=np.asarray(stored[k])
                    ck(f"npz_finite::{k}", np.all(np.isfinite(a)), bool(np.all(np.isfinite(a))), True)
            ck("replay_peak_severe_fraction", feq(replay_hz["peak_severe_fraction"],EXPECTED_PEAK_SEVERE_FRACTION,1e-15), replay_hz["peak_severe_fraction"],EXPECTED_PEAK_SEVERE_FRACTION)
            ck("replay_peak_severe_year", replay_hz["peak_severe_fraction_year_before_book"]==EXPECTED_PEAK_SEVERE_YEAR, replay_hz["peak_severe_fraction_year_before_book"],EXPECTED_PEAK_SEVERE_YEAR)
        except Exception as exc:
            ck("independent_replay_exception_free", False, repr(exc), "no exception")

    failed=[x for x in checks if not x["pass"]]
    verdict=SEALED_VERDICT if not failed else "FAIL_R320_SEALED_AUDIT"
    audit={
        "schema":"ARCANA_R320_FORMAL_SEALED_AUDIT_V1","stage":STAGE,"verdict":verdict,
        "checks":f"{len(checks)-len(failed)}/{len(checks)}","failed":failed,
        "decision":"CHA2_YOUNGER_DRYAS_CLASS_MAGNITUDE_CONFIRMED_AND_DERIVED_15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_SEALED_WITHOUT_CULTURAL_TARGETING",
        "canonical_artifacts":{"summary":str(sump),"summary_sha256":sh,"hazard_npz":str(npzp),"hazard_npz_sha256":nh},
        "magnitude":{"classification":mag.get("classification"),"metrics":mm},
        "hazard":{"start_year_before_book":-14950,"end_year_before_book":-11000,"step_years":50,"state_count":80,"peak_severe_fraction":EXPECTED_PEAK_SEVERE_FRACTION,"peak_severe_fraction_year_before_book":EXPECTED_PEAK_SEVERE_YEAR,"active_10deg_latitude_bands_at_peak":EXPECTED_ACTIVE_BANDS},
        "independent_replay":{"enabled":True,"magnitude_exact": bool(replay_mag==mag) if replay_mag is not None else False,"hazard_array_bit_exact": not any((not x["pass"]) and x["name"].startswith("npz_") for x in checks)},
        "governance":{"cha2_c1_modified":False,"r319_h0_state_modified":False,"biology_modified":False,"impact_origin_required":False,"human_population_used":False,"settlement_target_used":False,"flood_myth_target_used":False,"religion_target_used":False,"hazard_indices_are_diagnostic_rankings_not_flood_depths":True},
        "check_rows":checks,
    }
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(audit,indent=2),encoding="utf-8")
    if not failed:
        seal={
            "schema":"ARCANA_R320_SEAL_SUMMARY_V1","stage":STAGE,"verdict":SEALED_VERDICT,
            "formal_audit":str(out),"formal_audit_sha256":hfile(out),"formal_audit_checks":audit["checks"],
            "canonical_artifacts":audit["canonical_artifacts"],"magnitude":audit["magnitude"],"hazard":audit["hazard"],
            "parent_authority":{"r319_seal":str(sealp),"r319_json_sha256":EXPECTED_R319_JSON_SHA256,"r319_npz_sha256":EXPECTED_R319_NPZ_SHA256,"cha2_c1_sha256":EXPECTED_C1_SHA256},
            "governance":audit["governance"],
            "next":"v0.6D1-R3.21 — Late-Pleistocene Human-Readiness Functional Phenotype Layer & High-Resolution Replay Interface",
        }
        seal_out.write_text(json.dumps(seal,indent=2),encoding="utf-8")
    print(json.dumps({"verdict":verdict,"checks":audit["checks"],"audit":str(out),"seal":str(seal_out) if not failed else None},indent=2))
    return 0 if not failed else 1

if __name__ == "__main__":
    raise SystemExit(main())
