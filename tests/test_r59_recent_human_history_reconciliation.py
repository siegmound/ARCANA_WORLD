from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pytest
from arcana_worldsim.state_query import r59_recent_human_history_reconciliation as r59


def wj(p: Path, o):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(o, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def make_manifest(base: Path, names: list[str], status: str):
    return {
        'stage': 'x', 'status': status,
        'files': {n: {'bytes': (base/n).stat().st_size, 'sha256': r59.sha256_file(base/n)} for n in names},
    }


def bind_r328_expected(root: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(r59, 'EXPECTED_R328_FINAL_SEAL_AUDIT_SHA256', r59.sha256_file(root/r59.R328_SEAL_AUDIT))
    monkeypatch.setattr(r59, 'EXPECTED_R328_FINAL_SEAL_MANIFEST_SHA256', r59.sha256_file(root/r59.R328_SEAL_MANIFEST))
    monkeypatch.setattr(r59, 'EXPECTED_R328_OUTPUT_MANIFEST_SHA256', r59.sha256_file(root/r59.R328_OUTPUT_MANIFEST))
    monkeypatch.setattr(r59, 'EXPECTED_R328_REPLAY_SHA256', r59.sha256_file(root/r59.R328_REPLAY))
    monkeypatch.setattr(r59, 'EXPECTED_R328_CHECKPOINT_SHA256', r59.sha256_file(root/r59.R328_CHECKPOINT))


def refresh_r328_manifest(root: Path, monkeypatch: pytest.MonkeyPatch):
    out = root/r59.R328_OUT
    names = ['R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz','R3_28_HIGH_RESOLUTION_REPLAY_AUTHORITY.json','R3_28_HUMAN_0KA_CHECKPOINT.json','R3_28_CANDIDATE_POPULATION_OUTCOMES.json','R3_28_INTEGRATED_AUDIT.json']
    wj(root/r59.R328_OUTPUT_MANIFEST, make_manifest(out, names, 'CANDIDATE_OUTPUT_MANIFEST'))
    monkeypatch.setattr(r59, 'EXPECTED_R328_OUTPUT_MANIFEST_SHA256', r59.sha256_file(root/r59.R328_OUTPUT_MANIFEST))
    monkeypatch.setattr(r59, 'EXPECTED_R328_REPLAY_SHA256', r59.sha256_file(root/r59.R328_REPLAY))
    monkeypatch.setattr(r59, 'EXPECTED_R328_CHECKPOINT_SHA256', r59.sha256_file(root/r59.R328_CHECKPOINT))


def build_tree(tmp: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp
    cfg = {
        'target_cohort': list(r59.TARGET_COHORT), 'external_engine_execution': False, 'rerun_r328': False,
        'numeric_historical_truth_claimed': False, 'canonical_state_changed': False,
        'derived_refinement_promoted_to_canon': False, 'deep_biological_coupling': False,
        'auto_authorize_downstream_r329': False,
    }
    wj(root/'configs/world1_r59_recent_human_history_reconciliation_v0_6D1_R5_9.json', cfg)

    # R3.27 trajectory used for exact same-pipeline boundary reconstruction.
    ids = np.array(['RPT_010_D02','RPT_009_D02'])
    vars_ = np.array(['effective_population','deme_count','ecological_breadth','cumulative_buffering','dispersal_capacity','developmental_investment','genetic_diversity_proxy','adaptive_integration'])
    ages27 = np.arange(3.0, 0.2-1e-12, -0.02)
    st27 = np.zeros((96,2,len(ages27),8), dtype=float)
    for m in range(96):
        st27[m,0,:,0] = 1000+m; st27[m,1,:,0] = 800+m
        st27[m,:,:,1] = 3
        st27[m,0,:,6] = .30; st27[m,1,:,6] = .20
        st27[m,0,:,7] = .70; st27[m,1,:,7] = .60
    (root/r59.R327_TRAJECTORIES).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(root/r59.R327_TRAJECTORIES, candidate_ids=ids, age_ma=ages27, variable_names=vars_, state=st27)

    # R5.8 candidate outputs.
    o58 = root/r59.R58_OUT; o58.mkdir(parents=True)
    wj(root/r59.R58_AUDIT, {'status':'PASS_R58_3MA_200KA_HOMINID_HISTORY_RECONCILIATION_CANDIDATE','scientific_candidate_eligible':True,'checks_passed':23,'checks_total':23})
    wj(root/r59.R58_HANDOFF, {'age_ka':200.0,'candidate_cohort':list(r59.TARGET_COHORT),'candidate_count':2,'unique_human_identity_materialized':False,'ready_for_high_resolution_200ka_to_0_reconciliation':True,'source_r57_final_seal_sha256':r59.EXPECTED_R57_FINAL_SEAL_SHA256})
    wj(root/r59.R58_BINDING, {'r57_final_seal_sha256':r59.EXPECTED_R57_FINAL_SEAL_SHA256,'r327_trajectories_sha256':r59.sha256_file(root/r59.R327_TRAJECTORIES)})
    wj(root/r59.R58_MANIFEST, make_manifest(o58, ['R5_8_INTEGRATED_RECONCILIATION.json','R5_8_200KA_RECONCILED_HANDOFF.json','R5_8_PARENT_AUTHORITY_BINDING.json'], 'PASS_R58_3MA_200KA_HOMINID_HISTORY_RECONCILIATION_CANDIDATE'))

    # R3.28 replay consistent with the exact selected R3.27 endpoint.
    o28 = root/r59.R328_OUT; o28.mkdir(parents=True)
    ages28 = r59.expected_r328_age_axis(); members = np.arange(0,96,3,dtype=int)
    summary = np.zeros((32,2,len(ages28),8), dtype=np.float32)
    x = st27[members][:,:,-1,:]
    summary[:,:,0,0] = np.maximum(500.0, x[:,:,0])
    summary[:,:,0,3] = np.clip(x[:,:,6],.02,1)
    summary[:,:,0,4] = np.clip(x[:,:,7],0,1)
    summary[:,:,:,0] = np.maximum(summary[:,:,:,0], summary[:,:,0,0][:,:,None])
    summary[:,:,:,3] = summary[:,:,0,3][:,:,None]
    summary[:,:,:,4] = summary[:,:,0,4][:,:,None]
    contact = np.zeros((32,len(ages28)),dtype=np.float32); admix=np.zeros_like(contact)
    cha2 = ages28[(ages28<=14.95)&(ages28>=11.0)]
    np.savez_compressed(root/r59.R328_REPLAY,
        candidate_ids=ids,parent_member_indices=members,age_ka=ages28,
        state_variable_names=np.array(r59.EXPECTED_R328_STATE_NAMES),species_summary_variable_names=np.array(r59.EXPECTED_R328_SUMMARY_NAMES),
        species_summary=summary,contact_index=contact,admixture_opportunity_cumulative=admix,
        cha2_age_ka=cha2, snapshot_age_ka=np.array([200.,0.]), snapshot_deme_state=np.zeros((32,2,2,6,7)), snapshot_active=np.zeros((32,2,2,6)), cha2_deme_state=np.zeros((32,2,len(cha2),6,7)), cha2_active=np.zeros((32,2,len(cha2),6)))
    wj(root/r59.R328_AUTHORITY, {'parent':'PASS_R327_HOMININ_MACRO_EVOLUTION_REPLAY_TO_200KA_ROBUSTNESS_AND_HUMAN_200KA_CHECKPOINT_SEALED','candidate_cohort':list(r59.TARGET_COHORT),'recent_forcing_semantics':'R318_SEALED_PHASE_INTEGRAL_CONSTRAINED_DOWNSCALING_WITH_DIRECT_R320_CHA2_50Y_HAZARD','cha2_semantics':'DIAGNOSTIC_RANKING_NOT_FLOOD_DEPTH','contact_semantics':'SYMMETRIC_ADMIXTURE_OPPORTUNITY_DIAGNOSTIC_NO_FORCED_REPLACEMENT','human_similarity_target':False,'deep_biological_coupling':False})
    wj(root/r59.R328_CHECKPOINT, {'age_ka':0.0,'candidate_cohort':list(r59.TARGET_COHORT),'candidate_count':2,'unique_human_identity':None,'unique_human_identity_materialized':False})
    candidates=[]
    for sid in r59.TARGET_COHORT:
        candidates.append({'species_id':sid,'survival_frequency':1.0,'final_population_median':10000.0,'final_deme_median':4.0,'final_diversity_median':.25,'final_adaptive_integration_median':.7,'cha2_population_retention_median':.95,'sensitivity_qualification_frequency':1.0,'human_0ka_checkpoint_qualified':True})
    wj(root/r59.R328_OUTCOMES, {'candidates':candidates})
    wj(root/r59.R328_AUDIT, {'status':'PASS_R328_HIGH_RESOLUTION_200KA_TO_0_REPLAY_CANDIDATE','checks_passed':28,'checks_total':28,'checks_failed':0})
    refresh_r328_manifest(root, monkeypatch)

    s28 = root/r59.R328_SEAL_OUT; s28.mkdir(parents=True)
    wj(root/r59.R328_SEAL_AUDIT, {'verdict':'SEALED','status':'PASS_R328_HIGH_RESOLUTION_200KA_TO_0_POPULATION_STRUCTURE_MIGRATION_ADMIXTURE_CHA2_EXPOSURE_AND_HUMAN_0KA_CHECKPOINT_SEALED','checks_passed':35,'checks_failed':0})
    # Bind manifest to audit, then bind constants.
    audit_meta={'bytes':(root/r59.R328_SEAL_AUDIT).stat().st_size,'sha256':r59.sha256_file(root/r59.R328_SEAL_AUDIT)}
    wj(root/r59.R328_SEAL_MANIFEST, {'files':{'R3_28_FINAL_SEAL_AUDIT.json':audit_meta}})
    bind_r328_expected(root, monkeypatch)
    return root


def test_r59_passes_and_emits_two_lineage_0ka_handoff(tmp_path, monkeypatch):
    root=build_tree(tmp_path,monkeypatch)
    a=r59.reconcile(root)
    assert a['scientific_candidate_eligible'] is True
    assert a['checks_passed']==a['checks_total']
    h=json.loads((root/r59.OUT_REL/'R5_9_0KA_RECONCILED_HANDOFF.json').read_text())
    assert h['candidate_cohort']==list(r59.TARGET_COHORT)
    assert h['unique_human_identity_materialized'] is False
    assert h['downstream_r329_auto_authorized'] is False


def test_r327_r328_population_boundary_drift_fails_closed(tmp_path, monkeypatch):
    root=build_tree(tmp_path,monkeypatch)
    with np.load(root/r59.R328_REPLAY,allow_pickle=False) as z: data={k:z[k] for k in z.files}
    data['species_summary']=data['species_summary'].copy();data['species_summary'][0,0,0,0]+=7.0
    np.savez_compressed(root/r59.R328_REPLAY,**data)
    refresh_r328_manifest(root,monkeypatch)
    a=r59.reconcile(root)
    assert a['scientific_candidate_eligible'] is False
    assert 'r327_to_r328_population_boundary_exact' in a['failed']


def test_r328_age_axis_drift_fails_closed(tmp_path, monkeypatch):
    root=build_tree(tmp_path,monkeypatch)
    with np.load(root/r59.R328_REPLAY,allow_pickle=False) as z: data={k:z[k] for k in z.files}
    data['age_ka']=data['age_ka'].copy();data['age_ka'][10]-=.001
    np.savez_compressed(root/r59.R328_REPLAY,**data)
    refresh_r328_manifest(root,monkeypatch)
    a=r59.reconcile(root)
    assert a['scientific_candidate_eligible'] is False
    assert 'r328_age_axis_exact' in a['failed']


def test_r58_unique_identity_drift_blocks_parent_authority(tmp_path, monkeypatch):
    root=build_tree(tmp_path,monkeypatch)
    h=json.loads((root/r59.R58_HANDOFF).read_text());h['unique_human_identity_materialized']=True
    wj(root/r59.R58_HANDOFF,h)
    wj(root/r59.R58_MANIFEST, make_manifest(root/r59.R58_OUT, ['R5_8_INTEGRATED_RECONCILIATION.json','R5_8_200KA_RECONCILED_HANDOFF.json','R5_8_PARENT_AUTHORITY_BINDING.json'], 'PASS_R58_3MA_200KA_HOMINID_HISTORY_RECONCILIATION_CANDIDATE'))
    p=r59.validate_parent_authority(root)
    assert 'r58_handoff_exact' in p['failed']
