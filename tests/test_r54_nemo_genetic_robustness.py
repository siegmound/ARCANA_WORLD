from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pytest

from arcana_worldsim.state_query import r54_nemo_genetics as r54


def test_contract_counts_and_no_microseal():
    assert len(r54.STRESS_PROFILES) == 3
    assert r54.SEEDS == (540401, 540402)
    assert r54.VARIANTS == ("FLOW", "MATCHED_NO_FLOW")
    assert r54.EXPECTED_FAMILY_COUNT * len(r54.STRESS_PROFILES) * len(r54.VARIANTS) * len(r54.SEEDS) == 144


def test_initial_marker_frequencies_are_standardized_and_non_extreme():
    p=r54.standardized_initial_frequencies(4)
    assert p.shape == (4,16)
    assert np.all((p>0)&(p<1))
    assert np.allclose(p[0,::2],0.25)
    assert np.allclose(p[0,1::2],0.75)
    assert np.allclose(p,p[0][None,:])


def test_flow_matrix_is_symmetric_doubly_stochastic_and_fixed_mass():
    cells=[0,1,8,9,16]
    P=r54._sinkhorn_symmetric_affinity(cells,4,8)
    assert np.allclose(P,P.T,atol=1e-12,rtol=0)
    assert np.allclose(P.sum(axis=1),1,atol=2e-10,rtol=0)
    assert np.allclose(P.sum(axis=0),1,atol=2e-10,rtol=0)
    assert np.allclose(np.diag(P),1-r54.TOTAL_FLOW_MASS,atol=1e-12,rtol=0)


def test_flow_matrix_log_domain_balancing_handles_extreme_geometry_without_symmetry_drift():
    # Very uneven separations stress the old alternating row/column normalization.
    # The R5.4 challenge must remain symmetric and exactly balanced without
    # selecting or dropping distant ARCANA network cells.
    cells=[0, 1, 50_000, 99_999]
    P=r54._sinkhorn_symmetric_affinity(cells,10_000,10)
    assert np.all(np.isfinite(P))
    assert np.all(P>=0)
    assert np.allclose(P,P.T,atol=1e-12,rtol=0)
    assert np.allclose(P.sum(axis=1),1,atol=2e-10,rtol=0)
    assert np.allclose(P.sum(axis=0),1,atol=2e-10,rtol=0)
    assert np.allclose(np.diag(P),1-r54.TOTAL_FLOW_MASS,atol=1e-12,rtol=0)


def test_log_domain_balancer_is_used_without_edge_floor_or_result_selected_repair():
    src=Path(r54.__file__).read_text(encoding='utf-8')
    assert 'log-domain' in src
    assert '_row_logsumexp' in src
    assert 'edge_floor' not in src
    assert 'result-selected' not in src[src.index('def _sinkhorn_symmetric_affinity'):src.index('def standardized_initial_frequencies')]


def test_log_affinity_regularization_is_fixed_predeclared_and_not_result_selected():
    assert r54.MIN_RELATIVE_LOG_AFFINITY == -60.0
    cells=[0, 1, 500_000, 999_999]
    P=r54._sinkhorn_symmetric_affinity(cells,100_000,10)
    assert np.allclose(P,P.T,atol=1e-12,rtol=0)
    assert np.allclose(P.sum(axis=1),1,atol=2e-10,rtol=0)
    assert np.allclose(np.diag(P),1-r54.TOTAL_FLOW_MASS,atol=1e-12,rtol=0)


def test_ini_builder_has_matched_control_and_final_qfreq_callback(tmp_path:Path):
    group={'group_numeric_id':1,'demographic_stress_profile':'D2_STANDARDIZED_SEVERE_BOTTLENECK'}
    cells=[0,1,8]
    flow=tmp_path/'flow'/'Nemo2_ARCANA_R54.ini'; ctrl=tmp_path/'ctrl'/'Nemo2_ARCANA_R54.ini'
    mf=r54.build_nemo_ini(path=flow,group=group,variant='FLOW',seed=540401,cells=cells,nr=4,nc=8)
    mc=r54.build_nemo_ini(path=ctrl,group=group,variant='MATCHED_NO_FLOW',seed=540401,cells=cells,nr=4,nc=8)
    tf=flow.read_text(); tc=ctrl.read_text()
    assert 'generations             41' in tf
    assert 'quanti_freq_logtime     41' in tf
    assert 'quanti_mutation_rate    0' in tf
    assert 'patch_nbfem             {{12, 12, 12}}' in tf
    cm=np.loadtxt(ctrl.parent/'nemo_dispersal_matrix.tsv',delimiter='\t')
    fm=np.loadtxt(flow.parent/'nemo_dispersal_matrix.tsv',delimiter='\t')
    assert np.allclose(cm,np.eye(3))
    assert not np.allclose(fm,np.eye(3))
    assert mf['matrix_symmetric'] and mc['matrix_symmetric']


def _write_qfreq(path:Path, freq:np.ndarray, gen:int=41):
    lines=[f'pop trait locus allele g{gen}']
    for p in range(freq.shape[0]):
        for l in range(freq.shape[1]):
            lines.append(f'{p+1} 1 {l+1} 0.05 {freq[p,l]:.12g}')
    path.write_text('\n'.join(lines)+'\n')


def test_qfreq_parser_and_summary_use_frequency_only(tmp_path:Path):
    p=r54.standardized_initial_frequencies(3)
    q=tmp_path/'x.qfreq'; _write_qfreq(q,p)
    parsed=r54.parse_qfreq(q)
    assert parsed['generations']==[41]
    assert parsed['frequencies'].shape==(1,3,16)
    s=r54.summarize_qfreq(q,3)
    assert s['He_retention_ratio']==pytest.approx(1.0)
    assert s['final_fixed_patch_locus_fraction']==0.0
    assert s['final_among_patch_frequency_variance_mean']==pytest.approx(0.0)


def test_qfreq_fails_closed_on_wrong_locus_contract(tmp_path:Path):
    p=np.full((2,15),0.5); q=tmp_path/'bad.qfreq'; _write_qfreq(q,p)
    with pytest.raises(r54.R54Error): r54.parse_qfreq(q)


def test_r53_reporting_is_side_by_side_only(tmp_path:Path):
    p=tmp_path/r54.R53_SENSITIVITY_REL; p.parent.mkdir(parents=True)
    doc={'status':'R53_FIXED_DEMOGRAPHIC_STRESS_SENSITIVITY_SUMMARY','records':[{'candidate_id':'A','family_id':'F','demographic_stress_profile':'D0_STANDARDIZED_BASELINE','extinction_seed_count':1,'He_retention_ratio_minmax':[0.5,0.7],'alleles_retention_ratio_minmax':[0.8,0.9]}]}
    p.write_text(json.dumps(doc))
    r=r54._r53_reporting_by_key(tmp_path)[('A','F','D0_STANDARDIZED_BASELINE')]
    assert r['used_to_set_nemo_numeric_parameters'] is False
    assert r['used_as_arcana_target_authority'] is False


def test_r54_source_forbids_forced_cross_engine_equality():
    src=Path(r54.__file__).read_text(encoding='utf-8')
    assert 'cross_engine_equality_required": False' in src
    assert 'cross_engine_agreement_score_computed": False' in src
    assert 'r53_cdmetapop_values_used_to_fit_nemo": False' in src


def test_runner_has_project_local_pytest_and_resume_support():
    root=Path(__file__).resolve().parents[1]
    txt=(root/'run_v0_6D1_R5_4.ps1').read_text(encoding='utf-8')
    assert '--basetemp $PytestBase' in txt
    assert '[switch]$Resume' in txt
    assert 'nemo2.4.2' in txt
    assert 'list -n $CondaEnv --json nemo' in txt
    assert "conda_package_version=[string]$NemoPkg[0].version" in txt
    assert 'R5.4 remains CANDIDATE by design' in txt


def test_config_declares_no_numeric_truth_or_canonical_write():
    root=Path(__file__).resolve().parents[1]
    doc=json.loads((root/'configs/world1_r54_nemo_genetic_robustness_v0_6D1_R5_4.json').read_text())
    assert doc['challenge']['planned_stream_count']==144
    assert doc['authority']['r53_cdmetapop_values_used_to_fit_nemo'] is False
    assert doc['governance']['forced_cross_engine_metric_equality'] is False
    assert doc['governance']['automatic_numeric_scientific_pass_fail'] is False
    assert doc['governance']['canonical_write'] is False
    assert doc['governance']['micro_seal'] is False


def test_full_analyzer_accepts_integrity_complete_synthetic_corpus_without_numeric_winner(tmp_path:Path, monkeypatch):
    monkeypatch.setattr(r54,'validate_parent_authority',lambda *a,**k:{'failed':[]})
    out=tmp_path/r54.OUT_REL; out.mkdir(parents=True)
    # R5.3 reporting table: 12 families x 3 stress profiles.
    r53sens=tmp_path/r54.R53_SENSITIVITY_REL; r53sens.parent.mkdir(parents=True,exist_ok=True)
    sens_rows=[]
    families=[]
    for i in range(12):
        cand='RPT_010_D02' if i<7 else 'RPT_009_D02'; fid=f'F{i:04d}'; families.append((cand,fid))
        for stress in r54.STRESS_PROFILES:
            sens_rows.append({'candidate_id':cand,'family_id':fid,'demographic_stress_profile':stress,'extinction_seed_count':0,'He_retention_ratio_minmax':[0.8,0.9],'alleles_retention_ratio_minmax':[0.9,1.0]})
    r53sens.write_text(json.dumps({'records':sens_rows}))
    streams=[]; bridge=[]; gnum=0
    for cand,fid in families:
        for stress in r54.STRESS_PROFILES:
            gnum+=1; gid=f'R54_G{gnum:03d}_{fid}_{stress.split("_")[0]}'
            for variant in r54.VARIANTS:
                for seed in r54.SEEDS:
                    wd=out/'nemo_work'/gid/variant/f'seed_{seed}'; wd.mkdir(parents=True)
                    q=wd/'synthetic_1.qfreq'; _write_qfreq(q,r54.standardized_initial_frequencies(2))
                    (wd/'engine.returncode.txt').write_text('0\n')
                    (wd/'STREAM_RUNTIME.json').write_text(json.dumps({'status':'PASS_R54_NEMO_STREAM'}))
                    streams.append({'group_id':gid,'group_numeric_id':gnum,'candidate_id':cand,'family_id':fid,'demographic_stress_profile':stress,'variant':variant,'seed':seed,'work_dir':wd.relative_to(tmp_path).as_posix(),'patch_count':2})
                    bridge.append({'exit_code':0})
    plan={'status':'PASS_R54_NEMO_GENETIC_ROBUSTNESS_CHALLENGE_PLAN_PREPARED','family_count':12,'group_count':36,'planned_stream_count':144,'streams':streams,'semantics':{'r53_cdmetapop_values_used_to_fit_nemo':False,'r53_used_only_for_side_by_side_reporting':True,'matched_no_flow_control_is_required':True,'heterogeneous_engine_metrics_forced_to_equality':False},'selection_rules':{'majority_vote':False,'result_selected_tuning':False,'single_family_winner_selected':False,'external_engine_defines_arcana_target':False,'numeric_output_causes_automatic_scientific_pass_fail':False},'canonical_state_changed':False,'derived_refinement_promoted_to_canon':False,'deep_biological_coupling':False}
    (out/'R5_4_NEMO_EXECUTION_PLAN.json').write_text(json.dumps(plan))
    (out/'R5_4_NEMO_RUNTIME_IDENTITY.json').write_text(json.dumps({'status':'PASS_R54_NEMO_2_4_2_PINNED_RUNTIME_IDENTITY','nemo_version':'2.4.2','conda_package_name':'nemo','conda_package_version':'2.4.2','nemo_executable_name':'nemo2.4.2'}))
    (out/'R5_4_NEMO_EXECUTION_BRIDGE.json').write_text(json.dumps({'records':bridge}))
    result=r54.analyze_nemo_evidence(tmp_path)
    assert result['audit']['failed']==[]
    assert result['audit']['scientific_candidate_eligible'] is True
    assert len(result['stream_records'])==144
    assert len(result['paired'])==72
    assert len(result['sensitivity'])==36
    assert result['audit']['summary']['cross_engine_numeric_truth_claimed'] is False


def test_analyzer_runtime_contract_requires_exact_conda_package_and_executable():
    src=Path(r54.__file__).read_text(encoding='utf-8')
    assert 'runtime_conda_package_exact' in src
    assert 'runtime_executable_exact' in src
    assert 'runtime.get("conda_package_name") == "nemo"' in src
    assert 'runtime.get("conda_package_version") == EXPECTED_NEMO_VERSION' in src


def test_stream_runner_does_not_require_python_inside_nemo_conda_env():
    root=Path(__file__).resolve().parents[1]
    txt=(root/'benchmarks/r54/run_nemo_r54_stream.sh').read_text(encoding='utf-8')
    assert 'run -n "$CONDA_ENV" nemo2.4.2 "$INI"' in txt
    assert 'run -n "$CONDA_ENV" python' not in txt
