from pathlib import Path
import json
import numpy as np

from arcana_worldsim.scientific_engines.r425_target_protocol_preflight_geonomics_j14_discovery import (
    build_target_preflight, discover_j14_spatial_authority, _npz_spatial_exact3, J14,
)


def test_target_preflight_preserves_44_12_1_2_accounting(tmp_path: Path):
    r420={'record_count':59,'active_repair_count':57,'records':[]}
    r417={'p1_cell_count':59,'records':[]}
    for i in range(44):
        f=tmp_path/'outputs'/f'v0_6D1_R3_{i}'/f'canonical_{i}.json'; f.parent.mkdir(parents=True,exist_ok=True); f.write_text('{"x":1}')
        w=f'E{i}'; d='d'
        r420['records'].append({'window_id':w,'domain':d,'backlog_class':'CANONICAL_TARGET_EXTRACTOR_OR_EXPLICIT_DESCRIPTOR_REQUIRED','repair_disposition':'CANONICAL_DESCRIPTOR_EXTRACTOR_SPEC_FROZEN'})
        r417['records'].append({'window_id':w,'domain':d,'candidate_source_count':1,'candidate_sources_inspected':[{'source':str(f)}]})
    for i in range(12):
        w=f'N{i}'; r420['records'].append({'window_id':w,'domain':'d','backlog_class':'NEW_CANONICAL_TARGET_DESIGN_REQUIRED'}); r417['records'].append({'window_id':w,'domain':'d','candidate_source_count':0,'candidate_sources_inspected':[]})
    r420['records'].append({'window_id':'R','domain':'d','backlog_class':'MATERIALIZED_TARGET_OR_PRIMARY_METRIC_SEMANTIC_REPAIR_REQUIRED','failed_validation_keys':['provenance_integrity_pass']}); r417['records'].append({'window_id':'R','domain':'d'})
    for i in range(2):
        w=f'P{i}'; r420['records'].append({'window_id':w,'domain':'d','backlog_class':'CONTEXT_ONLY_PROXY_PRESERVE'}); r417['records'].append({'window_id':w,'domain':'d'})
    o=build_target_preflight(tmp_path,r420,r417)
    assert o['record_count']==59 and o['active_repair_count']==57 and o['context_only_proxy_count']==2
    assert o['canonical_extractor_ready_count']==44
    assert o['semantic_repair_audit_ready_count']==1
    assert o['new_target_design_authority_required_count']==12
    assert o['implementation_ready_count']==45


def test_external_engine_source_cannot_define_target(tmp_path: Path):
    f=tmp_path/'local_runs'/'v0_6D1_R3_6D'/'nemo'/'x.json'; f.parent.mkdir(parents=True); f.write_text('{"value":1}')
    r420={'records':[{'window_id':'W','domain':'d','backlog_class':'CANONICAL_TARGET_EXTRACTOR_OR_EXPLICIT_DESCRIPTOR_REQUIRED'}]}
    r417={'records':[{'window_id':'W','domain':'d','candidate_sources_inspected':[{'source':str(f)}]}]}
    o=build_target_preflight(tmp_path,r420,r417)
    assert o['canonical_extractor_ready_count']==0
    assert o['source_or_authority_deferred_count']==1


def test_npz_exact_3ma_requires_time_indexed_spatial_support(tmp_path: Path):
    p=tmp_path/'x.npz'
    np.savez(p, age_ma=np.array([3.0,2.0]), lat=np.array([1.,2.]), lon=np.array([3.,4.]), population_state=np.zeros((2,2,2)))
    o=_npz_spatial_exact3(p)
    assert o['spatial_basis_present'] and o['exact_3ma_time_present'] and o['time_indexed_spatial_support']


def test_discovery_accepts_only_sealed_exact_3ma_spatial_authority(tmp_path: Path):
    d=tmp_path/'outputs'/'v0_6D1_R3_99'; d.mkdir(parents=True)
    p=d/'R3_99_SPATIAL_STATE.npz'
    np.savez(p, age_ma=np.array([3.0,2.5]), lat=np.array([0.,1.]), lon=np.array([0.,1.]), population_state=np.zeros((2,2,2)))
    s=tmp_path/'outputs'/'v0_6D1_R3_99_SEAL'; s.mkdir(); (s/'FINAL_SEAL.json').write_text(json.dumps({'status':'PASS_R399_SEALED','verdict':'SEALED'}))
    parent={'records':[{'job_id':J14,'canonical_spatial_sources_audited':[]}]}
    o=discover_j14_spatial_authority(tmp_path,parent)
    assert o['existing_sealed_authority_found'] is True
    assert o['sealed_existing_authority_candidate_count']>=1


def test_discovery_does_not_accept_macro_time_without_spatial(tmp_path: Path):
    d=tmp_path/'outputs'/'v0_6D1_R3_27'; d.mkdir(parents=True)
    p=d/'R3_27_MACRO_REPLAY_STATE.npz'; np.savez(p, age_ma=np.array([3.0,2.0]), state=np.zeros((2,3)))
    s=tmp_path/'outputs'/'v0_6D1_R3_27_SEAL'; s.mkdir(); (s/'FINAL_SEAL.json').write_text(json.dumps({'status':'PASS_R327_SEALED','verdict':'SEALED'}))
    o=discover_j14_spatial_authority(tmp_path,{'records':[{'job_id':J14,'canonical_spatial_sources_audited':[{'path':str(p)}]}]})
    assert o['existing_sealed_authority_found'] is False
