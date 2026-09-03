from __future__ import annotations
import csv, json
from pathlib import Path
import numpy as np
import pytest

from arcana_worldsim.state_query import r53_demography as r53


def test_stress_profiles_and_seeds_are_frozen():
    assert r53.DEMOGRAPHIC_STRESS_PROFILES == {
        'D0_STANDARDIZED_BASELINE': {'source_n0':60,'patch_k':120},
        'D1_STANDARDIZED_MODERATE_BOTTLENECK': {'source_n0':30,'patch_k':90},
        'D2_STANDARDIZED_SEVERE_BOTTLENECK': {'source_n0':12,'patch_k':60},
    }
    assert r53.SEEDS == (530301,530302)
    assert r53.AUTHORIZED_CDMETAPOP_FIELDS == ('Year','N_Initial','Alleles','He','Ho')


def test_r52_seal_embedded_hashes_are_read_from_authority_block():
    seal={
        'authority':{
            'r52_execution_plan_sha256':r53.EXPECTED_R52_PLAN_SHA256,
            'r52_raw_evidence_manifest_sha256':r53.EXPECTED_R52_RAW_MANIFEST_SHA256,
            'r52_candidate_output_manifest_sha256':r53.EXPECTED_R52_OUTPUT_MANIFEST_SHA256,
        },
        # The CLI presentation flattens these fields, but the persisted seal does not.
        'execution_plan_sha256':'WRONG_TOP_LEVEL_SENTINEL',
        'raw_evidence_manifest_sha256':'WRONG_TOP_LEVEL_SENTINEL',
        'candidate_output_manifest_sha256':'WRONG_TOP_LEVEL_SENTINEL',
    }
    authority=seal.get('authority') or {}
    assert authority.get('r52_execution_plan_sha256') == r53.EXPECTED_R52_PLAN_SHA256
    assert authority.get('r52_raw_evidence_manifest_sha256') == r53.EXPECTED_R52_RAW_MANIFEST_SHA256
    assert authority.get('r52_candidate_output_manifest_sha256') == r53.EXPECTED_R52_OUTPUT_MANIFEST_SHA256


def test_toroidal_distance_wraps_longitude():
    # cells (row 10, col 0) and (row 10, col 179) are one cell apart on a 180-col world.
    d,p = r53._distance_and_probability([10*180+0,10*180+179],90,180)
    assert d[0,1] == pytest.approx(r53.ENGINE_COORDINATE_SCALE)
    assert 0 < p[0,1] < 1
    assert p[0,0] == 1


def test_summary_parser_uses_only_authorized_fields_and_preserves_extinction(tmp_path:Path):
    p=tmp_path/'summary_popAllTime.csv'
    p.write_text('Year,N_Initial,Alleles,He,Ho,Ignored\n0,10|5,2|2,0.5|0.4,0.4|0.3,x\n1,3|0,2|1,0.3|0.2,0.2|0.1,x\n2,0|0,1|1,0.1|0.1,0.1|0.0,x\n',encoding='utf-8')
    s=r53.summarize_cdmetapop_summary(p)
    assert s['initial_population_engine_native']==15
    assert s['final_population_engine_native']==0
    assert s['extinction_observed'] is True
    assert s['first_zero_population_engine_generation']==2
    assert s['minimum_to_initial_ratio']==0
    assert s['He_retention_ratio'] == pytest.approx(0.1/0.45)


def test_summary_parser_fails_closed_on_missing_authorized_field(tmp_path:Path):
    p=tmp_path/'x.csv'; p.write_text('Year,N_Initial,Alleles,He\n0,1,2,0.5\n',encoding='utf-8')
    with pytest.raises(r53.R53Error): r53.summarize_cdmetapop_summary(p)


def test_r52_support_is_reporting_stratification_only(tmp_path:Path,monkeypatch):
    out=tmp_path/r53.R52_OUT_REL; out.mkdir(parents=True)
    rows=[
      {'family_id':'F1','candidate_id':'RPT_010_D02','habitat_profile':'A','movement_profile':'D1','both_seeds_final_target_intersection':True,'any_seed_final_target_intersection':True},
      {'family_id':'F1','candidate_id':'RPT_010_D02','habitat_profile':'A','movement_profile':'D2','both_seeds_final_target_intersection':False,'any_seed_final_target_intersection':False},
    ]
    r53.write_json(tmp_path/r53.R52_SENSITIVITY_REL,{'records':rows})
    s=r53._r52_support_by_family(tmp_path)['F1']
    assert s['support_class']=='MIXED_EXECUTABLE_SENSITIVITY_FINAL_INTERSECTION'
    assert s['used_as_cdmetapop_spatial_geometry'] is False
    assert s['used_as_arcana_target_authority'] is False


def test_network_selection_is_deterministic_core_first_and_capped():
    ages=np.array([1.0,.98])
    ids=('RPT_010_D02','RPT_009_D02')
    spatial=np.zeros((96,2,2,8,4),float)
    # Repeated occupancy at cells 11 and 12, then 13.
    for e in range(96):
        spatial[e,0,0,0]=[1,1,1,1]  # cell 11 for nc=10 => row1 col1
        spatial[e,0,1,0]=[1,1,2,1]  # cell 12
    fam={'candidate_id':'RPT_010_D02','family_id':'F','oldest_supported_age_ma':1.0}
    cells=r53._select_network_cells_for_family(fam,{11},ages,ids,spatial,9,10)
    assert cells[0]==11
    assert 12 in cells
    assert len(cells)<=r53.MAX_PATCHES_PER_FAMILY


def _write_template(path:Path, header:list[str], row:dict[str,str]):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=header,lineterminator='\n'); w.writeheader(); w.writerow(row)


def test_input_builder_keeps_engine_counts_standardized_not_arcana_literal(tmp_path:Path,monkeypatch):
    eng=tmp_path/r53.ENGINE_ROOT_REL/'example_files'
    runh=['Popvars','sizecontrol','constMortans','mcruns','runtime','output_years','gridformat','gridsampling','summaryOutput','cdclimgentime','startcomp','implementcomp']
    _write_template(eng/'RunVars.csv',runh,{k:'0' for k in runh})
    poph=['xyfilename','mate_cdmat','matemoveno','matemovethresh','migrateout_cdmat','migrateback_cdmat','stray_cdmat','disperseLocal_cdmat','disperseLocalno','disperseLocalthresh','growth_option','popmodel','startGenes','loci','alleles','muterate','cdevolveans','startSelection','plasticgeneans','startPlasticgene']
    _write_template(eng/'popvars/PopVars.csv',poph,{k:'N' for k in poph})
    patchh=['PatchID','X','Y','SubpatchNO','K','K StDev','N0','Natal Grounds','Migration Out Grounds','Genes Initialize','Class Vars','Migration Out Prob','Migration Back Prob','Straying Prob','Dispersal Prob','HabitatOut','HabitatBack','GrowDaysOut']
    patchrow={k:'0' for k in patchh}; patchrow['GrowDaysOut']='155 | 155 | 155'
    _write_template(eng/'patchvars/PatchVars.csv',patchh,patchrow)
    (eng/'classvars').mkdir(parents=True,exist_ok=True); (eng/'classvars/ClassVars_AS1.csv').write_text('x\n1\n',encoding='utf-8')
    gd=tmp_path/'g'; meta=r53._build_cdmetapop_input_group(tmp_path,gd,[11,12],{11},{'source_n0':30,'patch_k':90},9,10)
    with (gd/'Inputs/patchvars/PatchVars_R53.csv').open(encoding='utf-8') as f: rows=list(csv.DictReader(f))
    assert rows[0]['N0']=='30' and rows[1]['N0']=='0'
    assert rows[0]['K']=='90' and rows[1]['K']=='90'
    assert rows[0]['GrowDaysOut']=='155' and rows[1]['GrowDaysOut']=='155'
    assert all('|' not in v for row in rows for v in row.values() if isinstance(v,str))
    with (gd/'Inputs/popvars/PopVars_R53.csv').open(encoding='utf-8') as f: pop=list(csv.DictReader(f))[0]
    assert pop['loci']==str(r53.NEUTRAL_LOCI) and pop['alleles']==str(r53.NEUTRAL_ALLELES)
    assert pop['implement_disease']=='N'
    assert meta['input_file_count']>=6


def test_temporal_template_scalarization_fails_closed_when_values_differ():
    assert r53._collapse_invariant_template_temporal_values({'GrowDaysOut':'155 | 155 | 155'})['GrowDaysOut']=='155'
    with pytest.raises(r53.R53Error, match='forbids implicit temporal-template selection'):
        r53._collapse_invariant_template_temporal_values({'GrowDaysOut':'150 | 155 | 160'})


def test_plan_semantics_forbid_r52_geometry_and_numeric_verdict(monkeypatch,tmp_path:Path):
    # Exercise plan assembly without real parent files/engine templates.
    monkeypatch.setattr(r53,'validate_parent_authority',lambda *a,**k:{'failed':[]})
    fams=[]; cores={}
    for i in range(12):
        sid='RPT_010_D02' if i<7 else 'RPT_009_D02'; fid=f'{sid}__F{i:04d}'
        fams.append({'candidate_id':sid,'family_id':fid,'oldest_supported_age_ma':1.0,'survives_all_thresholds':True})
        cores[fid]={11}
    monkeypatch.setattr(r53.r52,'reconstruct_robust_family_cores',lambda root:(fams,cores,np.arange(9.),np.arange(10.)))
    ages=np.array([1.0,.98]); ids=('RPT_010_D02','RPT_009_D02'); sp=np.zeros((96,2,2,8,4),float)
    for e in range(96):
        sp[e,0,:,0]=[1,1,1,1]; sp[e,0,:,1]=[1,1,2,1]; sp[e,1,:,0]=[1,1,1,1]; sp[e,1,:,1]=[1,1,2,1]
    monkeypatch.setattr(r53,'_load_j14',lambda root:(ages,ids,sp))
    monkeypatch.setattr(r53,'_r52_support_by_family',lambda root:{f['family_id']:{'support_class':'X','used_as_cdmetapop_spatial_geometry':False} for f in fams})
    monkeypatch.setattr(r53,'_build_cdmetapop_input_group',lambda *a,**k:{'input_file_count':1,'input_manifest_sha256':'x'})
    res=r53.prepare_demographic_challenges(tmp_path,True); p=res['plan']
    assert p['group_count']==36 and p['planned_stream_count']==72
    assert p['standardized_diagnostic_semantics']['r52_range_geometry_used_as_cdmetapop_input'] is False
    assert p['selection_rules']['numeric_output_causes_automatic_scientific_pass_fail'] is False
    assert all(g['r52_numeric_geometry_used_as_input'] is False for g in p['groups'])


def test_extinction_is_descriptive_not_integrity_failure():
    # Contract-level invariant: numeric extinction never appears in execution-integrity predicates.
    src=Path(r53.__file__).read_text(encoding='utf-8')
    assert '"extinction_is_not_runtime_failure": True' in src
    assert 'automatic_scientific_pass_fail_from_values": False' in src

def test_seeded_launcher_seeds_both_python_and_numpy_before_engine_run():
    launcher=(Path(__file__).parents[1]/'benchmarks/r53/cdmetapop_r53_seeded_launcher.py').read_text(encoding='utf-8')
    assert launcher.index('random.seed(a.seed)') < launcher.index('runpy.run_path')
    assert launcher.index('np.random.seed(a.seed)') < launcher.index('runpy.run_path')


def test_runner_pilot_precedes_full_corpus_and_no_micro_seal():
    runner=(Path(__file__).parents[1]/'run_v0_6D1_R5_3.ps1').read_text(encoding='utf-8')
    assert runner.index('CDMetaPOP pilot: first family/stress/seed') < runner.index('CDMetaPOP targeted execution:')
    assert 'seal_v0_6D1_R5_3' not in runner
    assert 'R5.3 remains CANDIDATE by design' in runner


def test_runner_uses_fresh_host_binding_and_does_not_require_legacy_r41_output():
    runner=(Path(__file__).parents[1]/'run_v0_6D1_R5_3.ps1').read_text(encoding='utf-8')
    assert 'R4_1_RUNTIME_IDENTITY_EVIDENCE.json' not in runner
    assert 'Get-Command wsl.exe' in runner
    assert 'R5_3_HOST_RUNTIME_BINDING.json' in runner
    assert 'ARCANA_CONDA_EXE' in runner
    assert 'legacy_r41_runtime_identity_required=$false' in runner


def test_runner_prefers_governed_conda_path_with_single_candidate_wsl_probe():
    runner=(Path(__file__).parents[1]/'run_v0_6D1_R5_3.ps1').read_text(encoding='utf-8')
    assert "'/home/jose/miniforge3/bin/conda'" in runner
    assert 'Test-R53WslCondaCandidate' in runner
    assert '$WslExe -e /usr/bin/test -x' in runner
    assert '$WslExe -e /usr/bin/readlink -f' in runner
    assert 'R5.3 fresh WSL Conda discovery failed.' not in runner
    assert '$discoverCmd' not in runner
    assert '$WslExe -e bash -lc' not in runner


def test_config_explicitly_denies_literal_time_population_and_range_geometry_authority():
    cfg=json.loads((Path(__file__).parents[1]/'configs/world1_r53_corridor_conditioned_demography_v0_6D1_R5_3.json').read_text(encoding='utf-8'))
    g=cfg['governance']
    assert g['r52_range_geometry_used_as_cdmetapop_input'] is False
    assert g['engine_counts_are_literal_arcana_population'] is False
    assert g['engine_generations_are_literal_arcana_time'] is False
    assert g['external_engine_defines_arcana_target'] is False

def test_full_analyzer_accepts_integrity_complete_synthetic_corpus_without_numeric_winner(tmp_path:Path,monkeypatch):
    monkeypatch.setattr(r53,'validate_parent_authority',lambda *a,**k:{'failed':[]})
    out=tmp_path/r53.OUT_REL; out.mkdir(parents=True)
    groups=[]; bridge=[]
    gi=0
    for fi in range(12):
        sid='RPT_010_D02' if fi<7 else 'RPT_009_D02'; fid=f'{sid}__F{fi:04d}'
        for stress in r53.DEMOGRAPHIC_STRESS_PROFILES:
            gi+=1; gid=f'G{gi:03d}'; gdir=out/'cdmetapop_work'/gid; inp=gdir/'Inputs'; ev=gdir/'Evidence'; inp.mkdir(parents=True); ev.mkdir(parents=True)
            r53.write_json(gdir/'GROUP_INPUT_MANIFEST.json',{'x':1}); imsha=r53.sha256_file(gdir/'GROUP_INPUT_MANIFEST.json')
            g={'group_id':gid,'candidate_id':sid,'family_id':fid,'demographic_stress_profile':stress,'seeds':list(r53.SEEDS),'expected_stream_count':2,'input_dir':str(inp.relative_to(tmp_path)).replace('\\','/'),'evidence_dir':str(ev.relative_to(tmp_path)).replace('\\','/'),'input_manifest_sha256':imsha,'r52_numeric_geometry_used_as_input':False,'r52_numeric_output_defines_arcana_target':False,'r52_corridor_support':{'support_class':'X'}}
            groups.append(g)
            for seed in r53.SEEDS:
                sd=ev/f'seed_{seed}'; sd.mkdir(parents=True)
                (sd/'summary_popAllTime.csv').write_text('Year,N_Initial,Alleles,He,Ho\n0,10,2,0.5,0.4\n1,8,2,0.45,0.35\n',encoding='utf-8')
                r53.write_json(sd/'STREAM_RUNTIME.json',{'status':'PASS_R53_CDMETAPOP_STREAM','seed':seed,'cdmetapop_version':r53.EXPECTED_CDMETAPOP_VERSION,'cdmetapop_commit':r53.EXPECTED_CDMETAPOP_COMMIT})
                bridge.append({'group_id':gid,'seed':seed,'exit_code':0,'timed_out':False})
    plan={'status':'PASS_R53_CDMETAPOP_DEMOGRAPHIC_CHALLENGE_PLAN_PREPARED','robust_family_count':12,'group_count':36,'planned_stream_count':72,'stress_profiles':r53.DEMOGRAPHIC_STRESS_PROFILES,'seeds':list(r53.SEEDS),'authorized_output_fields':list(r53.AUTHORIZED_CDMETAPOP_FIELDS),'selection_rules':{'majority_vote':False,'result_selected_tuning':False,'single_demographic_history_winner_selected':False,'external_engine_defines_arcana_target':False,'numeric_output_causes_automatic_scientific_pass_fail':False},'canonical_state_changed':False,'derived_refinement_promoted_to_canon':False,'deep_biological_coupling':False,'groups':groups}
    r53.write_json(out/'R5_3_CDMETAPOP_EXECUTION_PLAN.json',plan)
    r53.write_json(out/'R5_3_CDMETAPOP_RUNTIME_IDENTITY.json',{'status':'PASS_R53_CDMETAPOP_3_08_PINNED_RUNTIME_IDENTITY','cdmetapop_version':r53.EXPECTED_CDMETAPOP_VERSION,'cdmetapop_commit':r53.EXPECTED_CDMETAPOP_COMMIT})
    r53.write_json(out/'R5_3_CDMETAPOP_EXECUTION_BRIDGE.json',{'status':'R53_POWERSHELL_WSL_CDMETAPOP_EXECUTION_BRIDGE','stream_count':72,'records':bridge})
    res=r53.analyze_cdmetapop_evidence(tmp_path,True)
    assert res['audit']['failed']==[]
    assert res['audit']['scientific_candidate_eligible'] is False
    assert len(res['stream_records'])==72 and len(res['sensitivity'])==36
    assert all(x['automatic_scientific_pass_fail_from_values'] is False for x in res['sensitivity'])
