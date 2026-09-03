from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json
import numpy as np

STAGE = "v0.6D1-R5.11"
OUT_REL = Path("outputs/v0_6D1_R5_11")
TARGET_COHORT = ("RPT_010_D02", "RPT_009_D02")
EXPECTED_MEMBER_INDICES = tuple(range(0, 96, 3))
FINAL_STATUS = "PASS_R511_R510_TO_R330_CENSUS_GROUP_ABM_RECONCILIATION_CANDIDATE"

# Exact post-R5.10 source authority.
EXPECTED_R510_SOURCE_MANIFEST_SHA256 = "921d875ff400006e24537f65f87b33026b74a494a39a55c940ea24ab07f88702"
EXPECTED_R510_SOURCE_MODULE_SHA256 = "d88d87469f5902813a02d7010032831efd433e18366791df29d2db832de15178"
EXPECTED_R510_CONFIG_SHA256 = "c17b40c5927931435b877e4007728f9579d0f480bb47a1456e9264b16dd6be94"
EXPECTED_R510_CONTRACT_SHA256 = "a714ad503bde3fd2e990d644c093bf9d9af4b355abc2f56b51cb609c1315316a"

# Immutable sealed R3.30 authority.
EXPECTED_R330_FINAL_SEAL_AUDIT_SHA256 = "f6c2240b518e26d63fb93caf4a6c607649029f1362c0c2ee1211f777a10bf6a2"
EXPECTED_R330_FINAL_SEAL_MANIFEST_SHA256 = "ee3b7dc945bf78a6d9c0805cf15835895d12ab93501d90abcdc60f0cfa3095af"
EXPECTED_R330_OUTPUT_MANIFEST_SHA256 = "b98e8c8f9882c5672492d0467c74b817996e2f4238ac337e2d09dd5ffbd236f6"
EXPECTED_R330_CENSUS_NPZ_SHA256 = "f890169abce22641dddf95d82ff34d641c9bbde1362cd15e13cb0a8f34e6a919"
EXPECTED_R330_ABM_NPZ_SHA256 = "ede3b7ad301ce3e6b51cd3c8f4e70ff2392a43e50695b676b56912191d51cd57"
EXPECTED_R330_AUTHORITY_SHA256 = "a61598fd4c7864138cae3e414cd717b71f267de23bad7e36f68e022519f6edf9"
EXPECTED_R330_CHECKPOINT_SHA256 = "eb1fb23af98a6eda36bc1bf8fe4982e4c4c95fec7b03063b93abd56a5bfc0122"
EXPECTED_R330_OUTCOMES_SHA256 = "28a29f624911eb4c526734d8defd45ff3db40e0532b3093b7baa13d04609fc01"
EXPECTED_R330_SENSITIVITY_SHA256 = "12e0cf74e1e6e94a0d14b0d1251286e16c5df783d5588baae17eb06fc92e1179"
EXPECTED_R330_HISTORY_SHA256 = "578b1aeed3ad845d28f407c961d8901c043384dfce98d9c3adfb8ad12a042110"
EXPECTED_R330_AUDIT_SHA256 = "c06272d1bb467216d0cd22c2c21943c98e56a053208ba9590d0d770054969e8a"
EXPECTED_R330_SOURCE_MANIFEST_SHA256 = "6c8e6205370e2b661a2f9dac600120ad07ac0cb3248d2f38fcd9ba19aa4ce83d"
EXPECTED_R330_SOURCE_MODULE_SHA256 = "7ff8479e8c1c78c92dc8b1bd200337cd52e0a6573628ceb7814d4141f857316b"
EXPECTED_R330_CONFIG_SHA256 = "f6f7302c507102ff50dd830e4c1b2cd93185d88073e858b370e6d5727d9b1d37"
EXPECTED_R330_CONTRACT_SHA256 = "32ea47c3a997bc021512ad7812ca20107e87b3aad09c73fc1e4ddee13f900406"
EXPECTED_R329_REPLAY_SHA256 = "bbdde55933575153a88e570e3dc5709b38a09f696ffc2777c28299fc3cd3112a"
EXPECTED_R328_REPLAY_SHA256 = "16a48a3ec8736b4b6297186222d7274a5ce376085f27bfa9108d7ba5cd0ec99a"

R510_OUT = Path("outputs/v0_6D1_R5_10")
R510_MANIFEST = R510_OUT / "R5_10_OUTPUT_MANIFEST.json"
R510_AUDIT = R510_OUT / "R5_10_INTEGRATED_RECONCILIATION.json"
R510_HANDOFF = R510_OUT / "R5_10_0KA_COMMUNITY_PRECONDITION_HANDOFF.json"
R510_BINDING = R510_OUT / "R5_10_PARENT_AUTHORITY_BINDING.json"
R510_SOURCE_MANIFEST = Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_10.json")
R510_SOURCE_MODULE = Path("src/arcana_worldsim/state_query/r510_r329_settlement_cultural_reconciliation.py")
R510_CONFIG = Path("configs/world1_r510_r329_settlement_cultural_reconciliation_v0_6D1_R5_10.json")
R510_CONTRACT = Path("R5_10_R59_R329_POPULATION_SETTLEMENT_CULTURAL_PRECONDITION_RECONCILIATION_CONTRACT.md")

R328_REPLAY = Path("outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz")
R329_REPLAY = Path("outputs/v0_6D1_R3_29/R3_29_COMMUNITY_NETWORK_REPLAY.npz")
R330_OUT = Path("outputs/v0_6D1_R3_30")
R330_SEAL_OUT = Path("outputs/v0_6D1_R3_30_SEAL")
R330_CENSUS_NPZ = R330_OUT / "R3_30_CENSUS_AND_GROUP_TIMESERIES.npz"
R330_ABM_NPZ = R330_OUT / "R3_30_WEIGHTED_GROUP_ABM.npz"
R330_AUTHORITY = R330_OUT / "R3_30_CENSUS_CALIBRATION_AUTHORITY.json"
R330_CHECKPOINT = R330_OUT / "R3_30_COMMUNITY_HISTORY_CHECKPOINT.json"
R330_OUTCOMES = R330_OUT / "R3_30_LINEAGE_CENSUS_AND_GROUP_OUTCOMES.json"
R330_SENSITIVITY = R330_OUT / "R3_30_SENSITIVITY_AND_ROBUSTNESS.json"
R330_HISTORY = R330_OUT / "R3_30_LATE_PLEISTOCENE_COMMUNITY_HISTORY.json"
R330_AUDIT = R330_OUT / "R3_30_INTEGRATED_AUDIT.json"
R330_OUTPUT_MANIFEST = R330_OUT / "R3_30_OUTPUT_MANIFEST.json"
R330_SEAL_AUDIT = R330_SEAL_OUT / "R3_30_FINAL_SEAL_AUDIT.json"
R330_SEAL_MANIFEST = R330_SEAL_OUT / "R3_30_FINAL_SEAL_MANIFEST.json"
R330_SOURCE_MANIFEST = Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_30.json")
R330_SOURCE_MODULE = Path("src/arcana_worldsim/scientific_engines/r330_census_group_abm.py")
R330_CONFIG = Path("configs/world1_r330_census_group_abm_v0_6D1_R3_30.json")
R330_CONTRACT = Path("R3_30_CENSUS_GROUP_ABM_CONTRACT.md")

EXPECTED_CENSUS_NAMES = (
    "census_equivalent_total", "residential_group_mean_size", "residential_group_count_equivalent",
    "active_network_count_equivalent", "regional_network_count_equivalent", "cha2_group_disruption_equivalent",
)
EXPECTED_AGENT_NAMES = (
    "represented_people", "represented_camps", "mean_camp_size", "deme_index", "grid_row", "grid_col",
    "mode_code", "network_access", "culture_stock", "resource_stress", "interlineage_exchange", "cha2_disruption",
)
EXPECTED_HISTORY_NAMES = (
    "census_equivalent_total", "residential_group_count_equivalent", "mobile_group_fraction",
    "seasonal_aggregation_fraction", "persistent_group_fraction", "fission_event_equivalent",
    "fusion_event_equivalent", "network_reach_equivalent", "culture_stock", "cha2_disruption_equivalent",
)

class R511Error(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _manifest_integrity(base: Path, manifest_path: Path) -> tuple[bool, dict[str, Any]]:
    if not manifest_path.is_file():
        return False, {"error": "missing_manifest"}
    try:
        m = load_json(manifest_path)
        files = dict(m.get("files") or {})
        mismatches: list[str] = []
        ok = bool(files)
        for name, meta in files.items():
            p = base / name
            same = p.is_file() and p.stat().st_size == int(meta.get("bytes", -1)) and sha256_file(p) == meta.get("sha256")
            if not same:
                mismatches.append(name); ok = False
        return bool(ok), {"file_count": len(files), "mismatches": mismatches}
    except Exception as exc:
        return False, {"error": repr(exc)}


def validate_parent_authority(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    checks: dict[str, bool] = {}
    required = [
        R510_MANIFEST, R510_AUDIT, R510_HANDOFF, R510_BINDING, R510_SOURCE_MANIFEST, R510_SOURCE_MODULE, R510_CONFIG, R510_CONTRACT,
        R328_REPLAY, R329_REPLAY, R330_CENSUS_NPZ, R330_ABM_NPZ, R330_AUTHORITY, R330_CHECKPOINT, R330_OUTCOMES,
        R330_SENSITIVITY, R330_HISTORY, R330_AUDIT, R330_OUTPUT_MANIFEST, R330_SEAL_AUDIT, R330_SEAL_MANIFEST,
        R330_SOURCE_MANIFEST, R330_SOURCE_MODULE, R330_CONFIG, R330_CONTRACT,
    ]
    for rel in required:
        checks[f"present::{rel.as_posix()}"] = (root / rel).is_file()

    try:
        mi510, _ = _manifest_integrity(root / R510_OUT, root / R510_MANIFEST)
        a510 = load_json(root / R510_AUDIT); h510 = load_json(root / R510_HANDOFF)
        checks["r510_output_manifest_integrity"] = mi510
        checks["r510_candidate_semantics"] = (
            a510.get("status") == "PASS_R510_R59_TO_R329_POPULATION_SETTLEMENT_CULTURAL_PRECONDITION_RECONCILIATION_CANDIDATE"
            and a510.get("scientific_candidate_eligible") is True
            and int(a510.get("checks_passed", -1)) == 33 and int(a510.get("checks_total", -1)) == 33
            and not (a510.get("failed") or [])
        )
        checks["r510_handoff_exact"] = (
            h510.get("status") == "R510_RECONCILED_COMMUNITY_PRECONDITION_HANDOFF_0KA"
            and float(h510.get("age_ka", -1)) == 0.0
            and tuple(h510.get("candidate_cohort") or []) == TARGET_COHORT
            and tuple(h510.get("community_precondition_cohort") or []) == TARGET_COHORT
            and int(h510.get("candidate_count", -1)) == 2
            and h510.get("unique_human_identity") is None and h510.get("unique_human_identity_materialized") is False
            and h510.get("absolute_census_materialized") is False
            and h510.get("ready_for_r330_reconciliation") is True
            and h510.get("downstream_r330_auto_authorized") is False
        )
        checks["r510_source_manifest_exact_hash"] = sha256_file(root / R510_SOURCE_MANIFEST) == EXPECTED_R510_SOURCE_MANIFEST_SHA256
        checks["r510_source_module_exact_hash"] = sha256_file(root / R510_SOURCE_MODULE) == EXPECTED_R510_SOURCE_MODULE_SHA256
        checks["r510_config_exact_hash"] = sha256_file(root / R510_CONFIG) == EXPECTED_R510_CONFIG_SHA256
        checks["r510_contract_exact_hash"] = sha256_file(root / R510_CONTRACT) == EXPECTED_R510_CONTRACT_SHA256
    except Exception:
        for k in ["r510_output_manifest_integrity", "r510_candidate_semantics", "r510_handoff_exact", "r510_source_manifest_exact_hash", "r510_source_module_exact_hash", "r510_config_exact_hash", "r510_contract_exact_hash"]:
            checks[k] = False

    try:
        seal = load_json(root / R330_SEAL_AUDIT); sm = load_json(root / R330_SEAL_MANIFEST); ia = load_json(root / R330_AUDIT)
        checks["r330_final_seal_audit_exact_hash"] = sha256_file(root / R330_SEAL_AUDIT) == EXPECTED_R330_FINAL_SEAL_AUDIT_SHA256
        checks["r330_final_seal_manifest_exact_hash"] = sha256_file(root / R330_SEAL_MANIFEST) == EXPECTED_R330_FINAL_SEAL_MANIFEST_SHA256
        checks["r330_final_seal_manifest_binds_audit"] = (((sm.get("files") or {}).get("R3_30_FINAL_SEAL_AUDIT.json") or {}).get("sha256") == EXPECTED_R330_FINAL_SEAL_AUDIT_SHA256)
        checks["r330_final_seal_semantics"] = (
            seal.get("verdict") == "SEALED"
            and seal.get("status") == "PASS_R330_CENSUS_EQUIVALENT_CALIBRATION_WEIGHTED_GROUP_ABM_LATE_PLEISTOCENE_COMMUNITY_HISTORY_AND_CHA2_GROUP_EXPOSURE_SEALED"
            and int(seal.get("checks_passed", -1)) == 27 and int(seal.get("checks_failed", -1)) == 0
        )
        checks["r330_integrated_audit_semantics"] = (
            ia.get("status") == "PASS_R330_CENSUS_GROUP_ABM_AND_COMMUNITY_HISTORY_CANDIDATE"
            and int(ia.get("checks_passed", -1)) == 27 and int(ia.get("checks_total", -1)) == 27 and int(ia.get("checks_failed", -1)) == 0
        )
        checks["r330_output_manifest_exact_hash"] = sha256_file(root / R330_OUTPUT_MANIFEST) == EXPECTED_R330_OUTPUT_MANIFEST_SHA256
        mi330, _ = _manifest_integrity(root / R330_OUT, root / R330_OUTPUT_MANIFEST)
        checks["r330_output_manifest_integrity"] = mi330
        exact = {
            R330_CENSUS_NPZ: EXPECTED_R330_CENSUS_NPZ_SHA256, R330_ABM_NPZ: EXPECTED_R330_ABM_NPZ_SHA256,
            R330_AUTHORITY: EXPECTED_R330_AUTHORITY_SHA256, R330_CHECKPOINT: EXPECTED_R330_CHECKPOINT_SHA256,
            R330_OUTCOMES: EXPECTED_R330_OUTCOMES_SHA256, R330_SENSITIVITY: EXPECTED_R330_SENSITIVITY_SHA256,
            R330_HISTORY: EXPECTED_R330_HISTORY_SHA256, R330_AUDIT: EXPECTED_R330_AUDIT_SHA256,
            R330_SOURCE_MANIFEST: EXPECTED_R330_SOURCE_MANIFEST_SHA256, R330_SOURCE_MODULE: EXPECTED_R330_SOURCE_MODULE_SHA256,
            R330_CONFIG: EXPECTED_R330_CONFIG_SHA256, R330_CONTRACT: EXPECTED_R330_CONTRACT_SHA256,
            R329_REPLAY: EXPECTED_R329_REPLAY_SHA256, R328_REPLAY: EXPECTED_R328_REPLAY_SHA256,
        }
        for rel, expected in exact.items():
            checks[f"exact_hash::{rel.as_posix()}"] = sha256_file(root / rel) == expected
    except Exception:
        for k in ["r330_final_seal_audit_exact_hash", "r330_final_seal_manifest_exact_hash", "r330_final_seal_manifest_binds_audit", "r330_final_seal_semantics", "r330_integrated_audit_semantics", "r330_output_manifest_exact_hash", "r330_output_manifest_integrity"]:
            checks[k] = False

    failed = [k for k, v in checks.items() if not v]
    return {
        "stage": STAGE,
        "status": "PASS_R511_IMMUTABLE_R510_R330_PARENT_AUTHORITY" if not failed else "BLOCKED_R511_PARENT_AUTHORITY",
        "scientific_parent_mode": True,
        "checks_passed": len(checks) - len(failed), "checks_total": len(checks), "failed": failed, "checks": checks,
    }


def _ratio_draws(cfg330: dict[str, Any], n: int = 32) -> np.ndarray:
    p = cfg330["ne_to_total_census_ratio_prior"]
    rng = np.random.default_rng(int(p["seed"]))
    r = rng.triangular(float(p["low"]), float(p["mode"]), float(p["high"]), size=(n, 2))
    return np.clip(r, float(p["low"]), float(p["high"]))


def reconcile(root: Path) -> dict[str, Any]:
    root = Path(root).resolve(); out = root / OUT_REL
    cfg = load_json(root / "configs/world1_r511_r330_census_group_reconciliation_v0_6D1_R5_11.json")
    cfg330 = load_json(root / R330_CONFIG); auth330 = load_json(root / R330_AUTHORITY); cp330 = load_json(root / R330_CHECKPOINT)
    outcomes = load_json(root / R330_OUTCOMES); sens = load_json(root / R330_SENSITIVITY); history = load_json(root / R330_HISTORY)
    h510 = load_json(root / R510_HANDOFF); parent = validate_parent_authority(root)

    with np.load(root / R330_CENSUS_NPZ, allow_pickle=False) as z30, np.load(root / R330_ABM_NPZ, allow_pickle=False) as zabm, np.load(root / R329_REPLAY, allow_pickle=False) as z29, np.load(root / R328_REPLAY, allow_pickle=False) as z28:
        ids30 = tuple(map(str, z30["candidate_ids"].tolist())); ids29 = tuple(map(str, z29["candidate_ids"].tolist())); ids28 = tuple(map(str, z28["candidate_ids"].tolist()))
        p30 = tuple(map(int, z30["parent_member_indices"].tolist())); p29 = tuple(map(int, z29["parent_member_indices"].tolist())); p28 = tuple(map(int, z28["parent_member_indices"].tolist()))
        ages30 = np.asarray(z30["age_ka"], float); ages29 = np.asarray(z29["age_ka"], float); ages28 = np.asarray(z28["age_ka"], float)
        c_names = tuple(map(str, z30["census_variable_names"].tolist())); S = np.asarray(z30["census_group_series"], float)
        ratio_obs = np.asarray(z30["ne_to_total_census_ratio"], float); census200_obs = np.asarray(z30["census_200ka_anchor"], float)
        ratio_rec = _ratio_draws(cfg330)
        ix28 = np.array([int(np.where(np.isclose(ages28, a, atol=1e-10))[0][0]) for a in ages30], dtype=int)
        pop28 = np.asarray(z28["species_summary"][:, :, ix28, 0], float); p200 = np.asarray(z28["species_summary"][:, :, 0, 0], float)
        census200_rec = p200 / ratio_rec
        census_rec = census200_rec[:, :, None] * (pop28 / np.maximum(p200[:, :, None], 1.0))
        C = np.asarray(z29["community_summary"], float); n29 = tuple(map(str, z29["community_variable_names"].tolist())); anchor29 = np.asarray(z29["anchor_age_ka"], float); ix = {n:i for i,n in enumerate(n29)}
        agg=C[...,ix["aggregation_potential"]]; mob=C[...,ix["residential_mobility_index"]]; sett=C[...,ix["settlement_persistence_potential"]]; net=C[...,ix["network_connectivity"]]; dis=C[...,ix["cha2_community_disruption"]]
        gs=cfg330["residential_group_size"]
        mean_group=np.clip(float(gs["dispersed_reference"])+30.0*agg+7.0*sett-10.0*mob,float(gs["minimum"]),float(gs["maximum"]))
        group_count=census_rec/np.maximum(mean_group,1.0)
        active_size=np.clip(float(cfg330["active_network_reference"])*(0.75+0.5*net),80.0,260.0)
        regional_size=np.clip(float(cfg330["regional_network_reference"])*(0.65+0.7*net),250.0,1100.0)
        series_rec=np.stack([census_rec,mean_group,group_count,census_rec/active_size,census_rec/regional_size,group_count*dis],axis=-1)

        anchor_age=np.asarray(zabm["anchor_age_ka"],float); a_names=tuple(map(str,zabm["agent_variable_names"].tolist())); A=np.asarray(zabm["agent_state"],float); AA=np.asarray(zabm["agent_active"],np.uint8)
        h_names=tuple(map(str,zabm["history_variable_names"].tolist())); H=np.asarray(zabm["history_summary"],float)
        ia={n:i for i,n in enumerate(a_names)}; ih={n:i for i,n in enumerate(h_names)}
        people_err=camp_err=size_err=hist_census_err=hist_group_err=0.0
        for ai,a in enumerate(anchor_age):
            ti=int(np.where(np.isclose(ages30,a,atol=1e-10))[0][0]); active=AA[:,:,ai,:].astype(bool)
            people=np.sum(A[:,:,ai,:,ia["represented_people"]]*active,axis=-1); camps=np.sum(A[:,:,ai,:,ia["represented_camps"]]*active,axis=-1)
            people_err=max(people_err,float(np.max(np.abs(people-S[:,:,ti,0])))); camp_err=max(camp_err,float(np.max(np.abs(camps-S[:,:,ti,2]))))
            if np.any(active):
                m=A[:,:,ai,:,ia["mean_camp_size"]][active]; pp=A[:,:,ai,:,ia["represented_people"]][active]; cc=A[:,:,ai,:,ia["represented_camps"]][active]
                size_err=max(size_err,float(np.max(np.abs(m-pp/np.maximum(cc,1e-9)))))
            hist_census_err=max(hist_census_err,float(np.max(np.abs(H[:,:,ai,ih["census_equivalent_total"]]-S[:,:,ti,0]))))
            hist_group_err=max(hist_group_err,float(np.max(np.abs(H[:,:,ai,ih["residential_group_count_equivalent"]]-S[:,:,ti,2]))))

    checks: dict[str,bool] = {}
    checks["parent_authority_pass"] = not parent.get("failed")
    checks["config_target_cohort_exact"] = tuple(cfg.get("target_cohort") or []) == TARGET_COHORT
    checks["r510_handoff_two_lineage_exact"] = tuple(h510.get("candidate_cohort") or []) == TARGET_COHORT and int(h510.get("candidate_count",-1)) == 2
    checks["r330_candidate_order_exact"] = ids30 == ids29 == ids28 == TARGET_COHORT
    checks["r330_parent_member_indices_exact"] = p30 == p29 == p28 == EXPECTED_MEMBER_INDICES
    checks["r330_age_axis_exact_r329"] = np.array_equal(ages30,ages29) and len(ages30)==175 and float(ages30[0])==50.0 and float(ages30[-1])==0.0
    checks["r330_census_variable_names_exact"] = c_names == EXPECTED_CENSUS_NAMES and S.shape == (32,2,175,6)
    checks["r330_ne_to_total_ratio_draws_exact"] = ratio_obs.shape==(32,2) and float(np.max(np.abs(ratio_obs-ratio_rec))) <= 1e-15
    checks["r330_ne_to_total_ratio_prior_bounds"] = float(np.min(ratio_obs)) >= float(cfg330["ne_to_total_census_ratio_prior"]["low"]) and float(np.max(ratio_obs)) <= float(cfg330["ne_to_total_census_ratio_prior"]["high"])
    checks["r330_census_200ka_anchor_exact"] = float(np.max(np.abs(census200_obs-census200_rec))) <= 1e-12
    checks["r330_full_census_group_series_recomputed_exact"] = float(np.max(np.abs(S-series_rec))) <= 1e-8
    checks["r330_r328_relative_population_trajectory_preserved"] = np.allclose(S[...,0]/np.maximum(census200_obs[:,:,None],1e-30), pop28/np.maximum(p200[:,:,None],1e-30), rtol=0, atol=1e-10)
    checks["r330_agent_variable_names_exact"] = a_names == EXPECTED_AGENT_NAMES and A.shape==(32,2,11,48,12) and AA.shape==(32,2,11,48)
    checks["r330_history_variable_names_exact"] = h_names == EXPECTED_HISTORY_NAMES and H.shape==(32,2,11,10)
    checks["r330_anchor_axis_exact_r329"] = np.array_equal(anchor_age,anchor29) and len(anchor_age)==11
    checks["r330_weighted_agents_conserve_census"] = people_err <= 1e-8
    checks["r330_weighted_agents_conserve_group_equivalents"] = camp_err <= 1e-8
    checks["r330_agent_mean_group_size_identity"] = size_err <= 1e-10
    checks["r330_history_census_matches_timeseries"] = hist_census_err <= 1e-8
    checks["r330_history_group_count_matches_timeseries"] = hist_group_err <= 1e-8
    checks["r330_sensitivity_25_and_no_selection_gate"] = int(sens.get("variant_count",-1))==25 and len(sens.get("variants") or [])==25 and sens.get("selection_gate") is False and tuple(sens.get("candidate_retention") or [])==TARGET_COHORT
    checks["r330_checkpoint_two_lineages_no_unique_identity"] = tuple(cp330.get("candidate_cohort") or [])==TARGET_COHORT and int(cp330.get("candidate_count",-1))==2 and cp330.get("unique_human_identity") is None and cp330.get("unique_human_identity_materialized") is False
    checks["r330_census_equivalent_materialized_but_not_archaeological_observation"] = cp330.get("absolute_census_equivalent_materialized") is True and cp330.get("archaeological_census_observation_claimed") is False and auth330.get("census_semantics")=="UNCERTAINTY_AWARE_CENSUS_EQUIVALENT_POSTERIOR_NOT_ARCHAEOLOGICAL_OBSERVATION"
    checks["r330_weighted_abm_not_person_level"] = auth330.get("group_abm_semantics")=="WEIGHTED_RESIDENTIAL_GROUP_AGENTS_NOT_PERSON_LEVEL"
    checks["r330_fission_fusion_remain_diagnostic_equivalents"] = cfg.get("r330_fission_fusion_equivalents_literal_events") is False and "fission_event_equivalent" in h_names and "fusion_event_equivalent" in h_names
    checks["r330_exchange_remains_opportunity_not_realized_gene_flow"] = "interlineage_exchange" in a_names and h510.get("gene_flow_semantics")=="R329_INTERLINEAGE_EXCHANGE_OPPORTUNITY_IS_DIAGNOSTIC_ONLY_NOT_REALIZED_GENE_FLOW_OR_ADMIXTURE"
    checks["r330_legacy_calibration_not_historical_truth"] = cfg.get("r330_census_equivalent_historical_truth") is False and cfg.get("r330_residential_group_equivalents_historical_truth") is False and cfg.get("r330_legacy_calibration_values_canonical") is False
    checks["r330_evidence_basis_not_revalidated_here"] = cfg.get("r330_evidence_basis_revalidated_in_r511") is False and len(auth330.get("evidence_basis") or {}) == 8
    checks["r330_no_culture_identity_materialized"] = all(cp330.get(k) is False for k in ("language_materialized","religion_materialized","agriculture_materialized","city_state_materialized")) and outcomes.get("unique_human_identity_materialized") is False
    checks["no_new_external_engine_execution"] = cfg.get("external_engine_execution") is False
    checks["r330_not_rerun_or_mutated"] = cfg.get("rerun_r330") is False and sha256_file(root/R330_CENSUS_NPZ)==EXPECTED_R330_CENSUS_NPZ_SHA256 and sha256_file(root/R330_ABM_NPZ)==EXPECTED_R330_ABM_NPZ_SHA256
    checks["numeric_historical_truth_not_claimed"] = cfg.get("numeric_historical_truth_claimed") is False
    checks["canonical_state_unchanged"] = cfg.get("canonical_state_changed") is False
    checks["derived_refinement_not_promoted"] = cfg.get("derived_refinement_promoted_to_canon") is False
    checks["deep_biological_coupling_off"] = cfg.get("deep_biological_coupling") is False and auth330.get("deep_biological_coupling") is False
    checks["downstream_r331_not_auto_authorized"] = cfg.get("auto_authorize_downstream_r331") is False

    checks={k:bool(v) for k,v in checks.items()}; failed=[k for k,v in checks.items() if not v]
    out.mkdir(parents=True,exist_ok=True)

    utility={"stage":STAGE,"status":"PASS_R511_RUNTIME_UTILITY_REVIEW_NO_NEW_ENGINE_REQUIRED","new_external_engine_execution_performed":False,"decision":"NO_NEW_ENGINE_OR_R330_RERUN_REQUIRED","reason":"R3.30 is already SEALED and its census-equivalent and weighted-group outputs are deterministically revalidated against the immutable R3.28/R3.29 parent states.","considered":{"SLiM_5_2":"NOT_RERUN_NO_NEW_ANCESTRY_QUESTION","NEMO_2_4_2":"NOT_RERUN_NO_NEW_GENE_FLOW_QUESTION","CDMetaPOP_3_08":"NOT_RERUN_NO_NEW_PERSISTENCE_QUESTION","RangeShiftR_3_0_1":"NOT_RERUN_NO_NEW_CORRIDOR_QUESTION","new_ABM_runtime":"NOT_REQUIRED_R330_WEIGHTED_GROUP_ABM_IS_RECONCILED_NOT_REEXECUTED"}}
    write_json(out/"R5_11_RUNTIME_UTILITY_REVIEW.json",utility)
    binding={"stage":STAGE,"status":"R511_PARENT_AUTHORITY_BINDING","r510_output_manifest_sha256":sha256_file(root/R510_MANIFEST),"r510_handoff_sha256":sha256_file(root/R510_HANDOFF),"r330_final_seal_audit_sha256":sha256_file(root/R330_SEAL_AUDIT),"r330_output_manifest_sha256":sha256_file(root/R330_OUTPUT_MANIFEST),"r330_census_npz_sha256":sha256_file(root/R330_CENSUS_NPZ),"r330_abm_npz_sha256":sha256_file(root/R330_ABM_NPZ),"r329_replay_sha256":sha256_file(root/R329_REPLAY),"r328_replay_sha256":sha256_file(root/R328_REPLAY),"binding_semantics":"R510_RECONCILED_TWO_LINEAGE_0KA_HANDOFF_PLUS_IMMUTABLE_SEALED_R330_CENSUS_EQUIVALENT_AND_WEIGHTED_GROUP_LAYER"}
    write_json(out/"R5_11_PARENT_AUTHORITY_BINDING.json",binding)
    alignment={"stage":STAGE,"status":"PASS_R511_R330_DETERMINISTIC_PIPELINE_ALIGNMENT" if not failed else "BLOCKED_R511_R330_PIPELINE_ALIGNMENT","candidate_cohort":list(TARGET_COHORT),"ensemble_members":32,"time_states":175,"anchor_states":11,"ratio_draw_max_abs_error":float(np.max(np.abs(ratio_obs-ratio_rec))),"census_200ka_max_abs_error":float(np.max(np.abs(census200_obs-census200_rec))),"full_series_max_abs_error":float(np.max(np.abs(S-series_rec))),"weighted_people_conservation_max_abs_error":people_err,"weighted_camp_conservation_max_abs_error":camp_err,"agent_mean_group_size_max_abs_error":size_err,"history_census_max_abs_error":hist_census_err,"history_group_count_max_abs_error":hist_group_err,"semantics":"EXACT_DETERMINISTIC_REVALIDATION_OF_R330_TRANSFORMATION_FROM_SEALED_R328_R329_WITHOUT_RERUNNING_R330"}
    write_json(out/"R5_11_R330_PIPELINE_ALIGNMENT.json",alignment)
    classification={"stage":STAGE,"status":"R511_R330_DIAGNOSTIC_CALIBRATION_CLASSIFICATION","ne_to_total_census_ratio_prior":cfg330["ne_to_total_census_ratio_prior"],"residential_group_size_calibration":cfg330["residential_group_size"],"active_network_reference":cfg330["active_network_reference"],"regional_network_reference":cfg330["regional_network_reference"],"sensitivity_ratio_multipliers":cfg330["sensitivity_ratio_multipliers"],"sensitivity_group_size_multipliers":cfg330["sensitivity_group_size_multipliers"],"classification":"SEALED_LEGACY_EVIDENCE_CALIBRATED_DIAGNOSTIC_HYPERPARAMETERS_NOT_OBSERVED_HISTORICAL_VALUES_AND_NOT_CANONICAL_NUMERIC_TRUTH","census_equivalent_semantics":"ABSOLUTE_CENSUS_EQUIVALENT_LAYER_AVAILABLE_BUT_NOT_LITERAL_ARCHAEOLOGICAL_OR_HISTORICAL_CENSUS","weighted_group_semantics":"REPRESENTED_PEOPLE_AND_CAMPS_ARE_EQUIVALENT_WEIGHTS_NOT_PERSONS_OR_OBSERVED_CAMPS","fission_fusion_semantics":"GROUP_REORGANIZATION_EQUIVALENTS_NOT_OBSERVED_EVENTS","cha2_semantics":"GROUP_DISRUPTION_EQUIVALENT_PRESSURE_NOT_DESTROYED_CAMPS","evidence_basis_status":"INHERITED_FROM_SEALED_R330_NOT_REVALIDATED_BY_R511"}
    write_json(out/"R5_11_R330_DIAGNOSTIC_CLASSIFICATION.json",classification)
    handoff={"stage":STAGE,"status":"R511_RECONCILED_CENSUS_EQUIVALENT_WEIGHTED_GROUP_HANDOFF_0KA","age_ka":0.0,"candidate_cohort":list(TARGET_COHORT),"candidate_count":2,"unique_human_identity":None,"unique_human_identity_materialized":False,"census_equivalent_layer_available":True,"absolute_census_equivalent_materialized":True,"literal_absolute_census_materialized":False,"archaeological_census_observation_claimed":False,"weighted_group_abm_layer_available":True,"person_level_abm_materialized":False,"literal_residential_group_history_materialized":False,"literal_fission_fusion_event_history_materialized":False,"language_materialized":False,"religion_materialized":False,"agriculture_materialized":False,"city_state_materialized":False,"named_culture_materialized":False,"gene_flow_semantics":"R330_INTERLINEAGE_EXCHANGE_IS_DIAGNOSTIC_OPPORTUNITY_ONLY_NOT_REALIZED_GENE_FLOW_OR_ANCESTRY","source_r510_handoff_sha256":sha256_file(root/R510_HANDOFF),"source_r330_final_seal_audit_sha256":sha256_file(root/R330_SEAL_AUDIT),"source_r330_census_npz_sha256":sha256_file(root/R330_CENSUS_NPZ),"source_r330_abm_npz_sha256":sha256_file(root/R330_ABM_NPZ),"ready_for_r331_reconciliation":not failed,"downstream_r331_auto_authorized":False}
    write_json(out/"R5_11_0KA_CENSUS_GROUP_RECONCILED_HANDOFF.json",handoff)
    audit={"stage":STAGE,"status":FINAL_STATUS if not failed else "BLOCKED_R511_R510_TO_R330_RECONCILIATION","scientific_candidate_eligible":not failed,"checks_passed":len(checks)-len(failed),"checks_total":len(checks),"failed":failed,"checks":checks,"summary":{"target_cohort":list(TARGET_COHORT),"r330_time_states":175,"r330_anchor_states":11,"r330_ensemble_members":32,"census_equivalent_layer_available":True,"literal_archaeological_census_claimed":False,"weighted_group_abm_available":True,"person_level_abm_materialized":False,"literal_group_event_history_claimed":False,"final_human_species_identity_materialized":False,"new_external_engine_execution_performed":False,"r330_rerun_performed":False,"numeric_historical_truth_claimed":False,"canonical_state_changed":False,"derived_refinement_promoted_to_canon":False,"deep_biological_coupling":False},"recommended_next_action":"RECONCILE_SEALED_R331_ABSTRACT_CULTURAL_TECHNOLOGICAL_ECOLOGY_AGAINST_R511_HANDOFF_BEFORE_ACCEPTING_DOWNSTREAM_TECHNOLOGICAL_HISTORY"}
    write_json(out/"R5_11_INTEGRATED_RECONCILIATION.json",audit)
    names=["R5_11_RUNTIME_UTILITY_REVIEW.json","R5_11_PARENT_AUTHORITY_BINDING.json","R5_11_R330_PIPELINE_ALIGNMENT.json","R5_11_R330_DIAGNOSTIC_CLASSIFICATION.json","R5_11_0KA_CENSUS_GROUP_RECONCILED_HANDOFF.json","R5_11_INTEGRATED_RECONCILIATION.json"]
    write_json(out/"R5_11_OUTPUT_MANIFEST.json",{"stage":STAGE,"status":audit["status"],"files":{n:{"bytes":(out/n).stat().st_size,"sha256":sha256_file(out/n)} for n in names}})
    return audit
