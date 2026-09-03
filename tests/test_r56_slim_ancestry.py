from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pytest

from arcana_worldsim.state_query import r56_slim_ancestry as r56


def _pair_ids():
    return [f"CZ{i:03d}_A__B" for i in range(1, r56.EXPECTED_PAIR_COUNT + 1)]


def _make_parent_files(root: Path, near: np.ndarray | None = None):
    out = root / r56.R55_OUT_REL
    out.mkdir(parents=True, exist_ok=True)
    pair_ids = _pair_ids()
    ages = np.linspace(3.0, 0.2, r56.EXPECTED_AGE_STATE_COUNT)
    if near is None:
        near = np.zeros((r56.EXPECTED_PAIR_COUNT, r56.EXPECTED_AGE_STATE_COUNT), dtype=np.float32)
        near[:, 20:40] = 0.01
    exact = np.minimum(near, 0.5)
    np.savez_compressed(out / 'R5_5_CONTACT_OPPORTUNITY_ATLAS.npz', age_ma=ages, pair_ids=np.asarray(pair_ids), one_cell_contact_ensemble_fraction=near, exact_contact_ensemble_fraction=exact, contact_support_thresholds=np.asarray([0,.25,.5,.75,1.0]))
    records=[]
    for i,pid in enumerate(pair_ids):
        records.append({
            'pair_id':pid,'family_a':f'A{i:03d}','family_b':f'B{i:03d}',
            'exact_overlap_state_count':int(np.sum(exact[i]>0)),
            'one_cell_contact_opportunity_state_count':int(np.sum(near[i]>0)),
            'contact_opportunity_windows_by_support_threshold':{'gt0':{'windows':[]}},
            'any_one_cell_contact_opportunity_state':True,
        })
    (out/'R5_5_CONTACT_ZONE_HISTORY.json').write_text(json.dumps({'pair_records':records}),encoding='utf-8')
    for p in [r56.R55_AUDIT_REL,r56.R55_CONTEXT_REL,r56.R55_OUTPUT_MANIFEST_REL,r56.R55_BINDING_REL]:
        fp=root/p; fp.parent.mkdir(parents=True,exist_ok=True); fp.write_text('{}',encoding='utf-8')
    src=root/r56.R55_SOURCE_REL; src.parent.mkdir(parents=True,exist_ok=True); src.write_text('# synthetic r55\n',encoding='utf-8')
    return pair_ids


def test_fixed_variant_family_is_predeclared_and_contains_control():
    assert r56.VARIANTS == {'NO_FLOW':0.0,'LOW_BIDIRECTIONAL':0.005,'HIGH_BIDIRECTIONAL':0.020}
    assert r56.SEEDS == (560601,560602)


def test_schedule_builder_uses_positive_support_only_not_magnitude():
    pair_ids=['P1','P2']
    x=np.asarray([[0,.01,.9,0],[0,.8,.01,0]],dtype=float)
    schedules,pmap=r56.build_schedule_classes(pair_ids,x)
    assert len(schedules)==1
    assert pmap['P1']==pmap['P2']
    assert schedules[0]['active_state_count']==2


def test_schedule_builder_deduplicates_only_identical_binary_histories():
    pair_ids=['P1','P2','P3']
    x=np.asarray([[0,1,0,1],[0,.1,0,.2],[1,0,1,0]],dtype=float)
    schedules,pmap=r56.build_schedule_classes(pair_ids,x)
    assert len(schedules)==2
    assert pmap['P1']==pmap['P2']
    assert pmap['P1']!=pmap['P3']
    assert sorted(sum((s['pair_ids'] for s in schedules),[]))==sorted(pair_ids)


def test_schedule_builder_fails_closed_if_parent_pair_has_no_contact():
    with pytest.raises(r56.R56Error):
        r56.build_schedule_classes(['P1'],np.zeros((1,4)))


def test_slim_renderer_remembers_founders_and_uses_binary_contact_schedule():
    mask=np.zeros(r56.EXPECTED_AGE_STATE_COUNT,dtype=np.uint8); mask[[1,4,9]]=1
    s=r56.render_slim_script(mask,0.005)
    assert 'initializeTreeSeq();' in s
    assert 'sim.treeSeqRememberIndividuals(p1.individuals);' in s
    assert 'sim.treeSeqRememberIndividuals(p2.individuals);' in s
    assert 'p1.setMigrationRates(p2, MIGRATION_RATE);' in s
    assert 'p2.setMigrationRates(p1, MIGRATION_RATE);' in s
    assert 'R56_ACTIVE_STATES=' in s
    assert 'defineConstant("CONTACT", c(' in s
    assert '0.005' in s


def test_slim_renderer_has_standardized_model_not_r53_fitted_demography():
    s=r56.render_slim_script(np.ones(r56.EXPECTED_AGE_STATE_COUNT,dtype=np.uint8),0.02)
    assert f'sim.addSubpop("p1", {r56.FOUNDER_SIZE_PER_POP});' in s
    assert f'sim.addSubpop("p2", {r56.FOUNDER_SIZE_PER_POP});' in s
    assert 'CDMetaPOP' not in s and 'R5.3' not in s and 'NEMO' not in s


def test_ancestry_segment_summary_merges_adjacent_donor_trees_into_one_tract():
    segs=[[(0,10,0),(10,20,1),(20,40,1),(40,100,0)],[(0,100,0)]]
    d=r56.summarize_ancestry_segments(segs,100.0)
    assert d['recipient_haplotype_count']==2
    assert d['donor_ancestry_fraction_mean']==pytest.approx(0.15)
    assert d['donor_tract_count_total']==1
    assert d['donor_tract_length_mean_bp']==pytest.approx(30.0)
    assert d['donor_tract_length_max_bp']==pytest.approx(30.0)
    assert d['recipient_haplotype_with_any_donor_ancestry_fraction']==pytest.approx(0.5)


def test_ancestry_segment_summary_fails_on_incomplete_coverage():
    with pytest.raises(r56.R56Error):
        r56.summarize_ancestry_segments([[(0,50,0)]],100.0)


def test_prepare_deduplicates_35_identical_pair_schedules_to_six_streams(tmp_path,monkeypatch):
    _make_parent_files(tmp_path)
    monkeypatch.setattr(r56,'validate_parent_authority',lambda *a,**k:{'failed':[]})
    plan=r56.prepare_ancestry_challenges(tmp_path,allow_non_scientific_dev_parent=True)
    assert plan['pair_count']==35
    assert plan['schedule_class_count']==1
    assert plan['planned_stream_count']==6
    assert len(plan['pair_to_schedule'])==35
    assert plan['selection_rules']['single_pair_winner'] is False
    assert plan['semantics']['r55_contact_support_fraction_used_as_migration_magnitude'] is False


def _ancestry_result(seed,variant,val):
    block={
      'recipient_haplotype_count':400,
      'donor_ancestry_fraction_mean':val,
      'donor_ancestry_fraction_haplotype_minmax':[0.0,min(1.0,val*2)],
      'recipient_haplotype_with_any_donor_ancestry_fraction':min(1.0,val*4),
      'donor_tract_count_total':0 if val==0 else 10,
      'donor_tract_length_mean_bp':0.0 if val==0 else 1000.0,
      'donor_tract_length_max_bp':0.0 if val==0 else 5000.0,
    }
    return {'stage':r56.STAGE,'status':'PASS_R56_ANCESTRY_RESULT','seed':seed,'variant':variant,'p1_from_p2':dict(block),'p2_from_p1':dict(block)}


def test_full_analyzer_accepts_integrity_complete_synthetic_corpus_without_history_winner(tmp_path,monkeypatch):
    _make_parent_files(tmp_path)
    monkeypatch.setattr(r56,'validate_parent_authority',lambda *a,**k:{'failed':[]})
    plan=r56.prepare_ancestry_challenges(tmp_path,allow_non_scientific_dev_parent=True)
    out=tmp_path/r56.OUT_REL
    r56.write_json(out/'R5_6_SLIM_RUNTIME_IDENTITY.json',{'status':'PASS_R56_SLIM_5_2_PINNED_RUNTIME_IDENTITY','slim_version':'5.2','tskit_version':'1.0.3'})
    r56.write_json(out/'R5_6_EXECUTION_BRIDGE.json',{'status':'R56_POWERSHELL_WSL_SLIM_EXECUTION_BRIDGE','stream_count':6,'exit_zero_count':6})
    for s in plan['streams']:
        wd=tmp_path/Path(s['work_dir'])
        (wd/'r56.trees').write_bytes(b'fake-tree-'+str(s['stream_numeric_id']).encode())
        val={'NO_FLOW':0.0,'LOW_BIDIRECTIONAL':0.1,'HIGH_BIDIRECTIONAL':0.2}[s['variant']]
        res=_ancestry_result(int(s['seed']),str(s['variant']),val)
        r56.write_json(wd/'ANCESTRY_RESULT.json',res)
        runtime={'status':'PASS_R56_SLIM_STREAM','returncode':0,'collector_returncode':0,'tree_sha256':r56.sha256_file(wd/'r56.trees'),'ancestry_result_sha256':r56.sha256_file(wd/'ANCESTRY_RESULT.json')}
        r56.write_json(wd/'STREAM_RUNTIME.json',runtime)
    audit=r56.analyze_ancestry_challenges(tmp_path,allow_non_scientific_dev_parent=True)
    assert audit['failed']==[]
    assert audit['summary']['scientific_stream_count']==6
    assert audit['summary']['pair_count']==35
    assert audit['summary']['numeric_admixture_truth_claimed'] is False
    sens=r56.load_json(out/'R5_6_ANCESTRY_ADMIXTURE_SENSITIVITY.json')
    assert len(sens['records'])==35
    assert sens['selection_semantics'].startswith('NO_WEIGHTED_SCORE')


def test_runner_requires_only_slim_and_tskit_not_unused_msprime_pyslim():
    root=Path(__file__).resolve().parents[1]
    text=(root/'run_v0_6D1_R5_6.ps1').read_text(encoding='utf-8')
    assert "Require-ExactPackage 'slim' '5.2'" in text
    assert "Require-ExactPackage 'tskit' '1.0.3'" in text
    assert "Require-ExactPackage 'msprime'" not in text
    assert "Require-ExactPackage 'pyslim'" not in text


def test_runner_has_pilot_resume_and_no_microseal():
    root=Path(__file__).resolve().parents[1]
    text=(root/'run_v0_6D1_R5_6.ps1').read_text(encoding='utf-8')
    assert '[switch]$Resume' in text
    assert 'check_v0_6D1_R5_6_pilot.py' in text
    assert 'seal_v0_6D1_R5_6' not in text
    assert 'not a micro-seal' in text.lower()


def test_collector_uses_root_ancestry_without_simplification():
    root=Path(__file__).resolve().parents[1]
    text=(root/'benchmarks/r56/slim_collect_r56.py').read_text(encoding='utf-8')
    assert 'tree.parent(v)' in text
    assert 'slim_id' in text
    assert '.simplify(' not in text
    assert 'tskit.load' in text


def test_config_explicitly_forbids_support_fraction_as_migration_rate():
    root=Path(__file__).resolve().parents[1]
    cfg=json.loads((root/'configs/world1_r56_slim_ancestry_v0_6D1_R5_6.json').read_text(encoding='utf-8'))
    assert cfg['contact_support_fraction_used_as_migration_magnitude'] is False
    assert cfg['selection_rules']['result_selected_tuning'] is False
    assert cfg['selection_rules']['single_admixture_history_winner'] is False
    assert cfg['closure_policy']=='CANDIDATE_THEN_SINGLE_LARGE_R53_R56_BLOCK_SEAL'


def test_contract_defers_other_engines_and_explains_slim_utility():
    root=Path(__file__).resolve().parents[1]
    text=(root/'R5_6_TARGETED_ANCESTRY_AND_ADMIXTURE_CHALLENGES_CONTRACT.md').read_text(encoding='utf-8')
    assert 'SLiM 5.2 is useful' in text
    assert 'No additional RangeShiftR, CDMetaPOP, NEMO, Geonomics, or Madingley execution' in text
    assert 'msprime' in text and 'not required' in text


def test_parent_reference_hash_constants_match_frozen_r41_files():
    root=Path(__file__).resolve().parents[1]
    assert r56.sha256_file(root/r56.R41_SLIM_REL)==r56.EXPECTED_R41_SLIM_SHA256
