from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pytest

from arcana_worldsim.state_query import r55_contact_history as r55


def _blank_spatial(ensembles=2, ages=1):
    x=np.zeros((ensembles,2,ages,8,4),dtype=float)
    return x


def _put(x,e,c,t,slot,row,col):
    x[e,c,t,slot]=[1.0,float(row),float(col),1.0]


def test_exact_contact_is_also_one_cell_contact():
    x=_blank_spatial(2,1)
    _put(x,0,0,0,0,2,3); _put(x,0,1,0,0,2,3)
    _put(x,1,0,0,0,4,4); _put(x,1,1,0,0,4,5)
    ex,near,zone=r55.contact_fractions_at_age(x,0,1,0,{23,44},{23,45},10,10)
    assert ex == pytest.approx(0.5)
    assert near == pytest.approx(1.0)
    assert 23 in zone


def test_separated_cells_are_not_contact():
    x=_blank_spatial(1,1)
    _put(x,0,0,0,0,1,1); _put(x,0,1,0,0,5,5)
    ex,near,zone=r55.contact_fractions_at_age(x,0,1,0,{11},{55},10,10)
    assert ex == 0.0 and near == 0.0 and zone == set()


def test_network_restriction_prevents_outside_contact():
    x=_blank_spatial(1,1)
    _put(x,0,0,0,0,1,1); _put(x,0,1,0,0,1,1)
    ex,near,_=r55.contact_fractions_at_age(x,0,1,0,{12},{11},10,10)
    assert ex == 0.0 and near == 0.0


def test_contact_fraction_uses_matched_ensemble_members():
    x=_blank_spatial(2,1)
    _put(x,0,0,0,0,1,1); _put(x,1,1,0,0,1,1)
    ex,near,_=r55.contact_fractions_at_age(x,0,1,0,{11},{11},10,10)
    assert ex == 0.0 and near == 0.0


def test_threshold_zero_means_positive_support_not_all_states():
    vals=np.asarray([0.0,0.01,0.25])
    assert r55._threshold_mask(vals,0.0).tolist() == [False,True,True]
    assert r55._threshold_mask(vals,0.25).tolist() == [False,False,True]


def test_contiguous_windows_preserve_age_direction_and_span():
    ages=np.asarray([1.0,0.8,0.6,0.4,0.2])
    w=r55.contiguous_windows(ages,np.asarray([False,True,True,False,True]))
    assert len(w)==2
    assert w[0]["oldest_age_ma"] == pytest.approx(0.8)
    assert w[0]["youngest_age_ma"] == pytest.approx(0.6)
    assert w[0]["sample_span_kyr"] == pytest.approx(200.0)
    assert w[1]["state_count"] == 1


def test_support_threshold_family_is_fixed_and_nested_reporting_only():
    assert r55.CONTACT_SUPPORT_THRESHOLDS == (0.0,0.25,0.50,0.75,1.0)
    vals=np.asarray([0.1,0.3,0.6,0.8,1.0])
    masks=[r55._threshold_mask(vals,q) for q in r55.CONTACT_SUPPORT_THRESHOLDS]
    for a,b in zip(masks,masks[1:]):
        assert np.all(~b | a)


def test_r53_compaction_contains_no_verdict_or_score():
    d=r55._compact_r53({"extinction_seed_count":1,"minimum_to_initial_ratio_minmax":[.1,.2],"He_retention_ratio_minmax":[.5,.8],"alleles_retention_ratio_minmax":[.7,.9]})
    assert d["automatic_scientific_pass_fail_from_values"] is False
    assert not any("score" in k.lower() or "winner" in k.lower() for k in d)


def test_r54_compaction_preserves_heterogeneous_semantics():
    d=r55._compact_r54({
      "nemo_delta_He_retention_flow_minus_control_minmax":[.1,.2],
      "nemo_delta_fixed_fraction_flow_minus_control_minmax":[-.1,0],
      "nemo_delta_patch_frequency_variance_flow_minus_control_minmax":[-.2,-.1],
      "nemo_delta_global_frequency_shift_flow_minus_control_minmax":[-.1,.1],
    })
    assert d["cross_engine_equality_required"] is False
    assert d["automatic_scientific_pass_fail_from_values"] is False


def test_pair_count_contract_matches_seven_by_five():
    assert 7*5 == r55.EXPECTED_PAIR_COUNT == 35


def test_stage_does_not_execute_external_engine_or_create_seal():
    root=Path(__file__).resolve().parents[1]
    runner=(root/'run_v0_6D1_R5_5.ps1').read_text(encoding='utf-8')
    contract=(root/'R5_5_CONTACT_ZONE_AND_GENE_FLOW_HISTORY_CONSOLIDATION_CONTRACT.md').read_text(encoding='utf-8')
    assert 'wsl.exe' not in runner.lower()
    assert 'conda' not in runner.lower()
    assert 'seal_v0_6D1_R5_5' not in runner
    assert 'No new external engine is useful' in contract
    assert 'SLiM is deferred to R5.6' in contract


def test_contact_semantics_explicitly_forbid_realized_admixture_claim():
    cfg=json.loads((Path(__file__).resolve().parents[1]/'configs/world1_r55_contact_history_v0_6D1_R5_5.json').read_text(encoding='utf-8'))
    assert 'NOT_REALIZED_ADMIXTURE' in cfg['contact_semantics']
    assert cfg['selection_rules']['majority_vote'] is False
    assert cfg['selection_rules']['agreement_score'] is False


def test_source_contract_uses_r53_r54_as_context_not_geometry():
    root=Path(__file__).resolve().parents[1]
    text=(root/'src/arcana_worldsim/state_query/r55_contact_history.py').read_text(encoding='utf-8')
    assert 'cross_engine_values_used_to_move_or_create_contact_window' in text
    assert 'r53_cdmetapop_used_as_contact_geometry' in text
    assert 'r54_nemo_used_as_contact_geometry' in text


def test_full_builder_emits_35_pair_atlas_and_105_context_records(tmp_path, monkeypatch):
    # Minimal synthetic parent files used only for hash binding after parent validation is mocked.
    for rel in [r55.R54_PLAN_REL,r55.R54_AUDIT_REL,r55.R54_SENSITIVITY_REL,r55.R54_OUTPUT_MANIFEST_REL,r55.R53_SENSITIVITY_REL,r55.R53_OUTPUT_MANIFEST_REL,r55.r53.J14_REL]:
        p=tmp_path/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text('{}',encoding='utf-8')
    monkeypatch.setattr(r55,'validate_parent_authority',lambda *a,**k:{'failed':[]})
    fams=[]; cores={}
    for i in range(7):
        fid=f'RPT_010_D02__F{i+1:04d}'; fams.append({'family_id':fid,'candidate_id':'RPT_010_D02','oldest_supported_age_ma':3.0}); cores[fid]={11}
    for i in range(5):
        fid=f'RPT_009_D02__F{i+1:04d}'; fams.append({'family_id':fid,'candidate_id':'RPT_009_D02','oldest_supported_age_ma':3.0}); cores[fid]={11}
    monkeypatch.setattr(r55.r52,'reconstruct_robust_family_cores',lambda root:(fams,cores,np.arange(10),np.arange(10)))
    ages=np.asarray([3.0,2.0,1.0])
    spatial=np.zeros((2,2,3,8,4),dtype=float)
    for e in range(2):
        for t in range(3):
            spatial[e,0,t,0]=[1,1,1,1]
            spatial[e,1,t,0]=[1,1,2,1]
    monkeypatch.setattr(r55.r53,'_load_j14',lambda root:(ages,tuple(r55.r52.CANDIDATES),spatial))
    monkeypatch.setattr(r55.r53,'_select_network_cells_for_family',lambda fam,core,ages,ids,spatial,nr,nc:[11,12])
    a={}; b={}
    for fam in fams:
        for stress in r55.r53.DEMOGRAPHIC_STRESS_PROFILES:
            key=(fam['family_id'],stress)
            a[key]={'extinction_seed_count':0,'minimum_to_initial_ratio_minmax':[.5,.8],'He_retention_ratio_minmax':[.7,.9],'alleles_retention_ratio_minmax':[.8,1.0]}
            b[key]={'nemo_delta_He_retention_flow_minus_control_minmax':[0,.1],'nemo_delta_fixed_fraction_flow_minus_control_minmax':[-.1,0],'nemo_delta_patch_frequency_variance_flow_minus_control_minmax':[-.1,0],'nemo_delta_global_frequency_shift_flow_minus_control_minmax':[-.1,.1]}
    monkeypatch.setattr(r55,'_sensitivity_lookup',lambda root:(a,b))
    out=r55.build_contact_history(tmp_path,allow_non_scientific_dev_parent=True)
    assert len(out['history']['pair_records'])==35
    assert len(out['context_records'])==105
    assert out['audit']['failed']==[]
    assert out['audit']['summary']['pair_with_one_cell_contact_opportunity_count']==35
    with np.load(tmp_path/r55.OUT_REL/'R5_5_CONTACT_OPPORTUNITY_ATLAS.npz',allow_pickle=False) as z:
        assert z['one_cell_contact_ensemble_fraction'].shape==(35,3)


def test_one_cell_contact_respects_longitude_wrap():
    # col 0 and col 9 are neighbors on a 10-column global grid.
    exact,near,zone=r55._cells_within_one({20},{29},10)
    assert exact is False
    assert near is True
    assert zone == {20,29}
