from pathlib import Path
import csv, json, math
import pytest

from arcana_worldsim.scientific_engines.r411_cdmetapop_population_metric_repair import (
    parse_summary_population, pipe_total, _configured_n0_audit, prepare, execute_reextraction_and_readjudicate,
    final_seal, retained_runtime_inventory, PREPARED, COMPLETE, SEALED, BLOCKED,
    AFFECTED, J09,
)

def wj(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(obj), encoding='utf-8')

def wt(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding='utf-8')

def summary_csv(p: Path, start=22.0, ratio=0.9):
    # 3 written rows; growth[i] maps N_i -> N_{i+1}; last growth infers final post-run N.
    n0=start; n1=start*0.97; n2=start*0.94; final=start*ratio
    rows=[
      {'Year':'0','K':'100|50|50|','GrowthRate':str(n1/n0),'N_Initial':f'{n0}|10|12|'},
      {'Year':'1','K':'95|48|47|','GrowthRate':str(n2/n1),'N_Initial':f'{n1}|9|11|'},
      {'Year':'2','K':'90|45|45|','GrowthRate':str(final/n2),'N_Initial':f'{n2}|8|10|'},
    ]
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['Year','K','GrowthRate','N_Initial']);w.writeheader();w.writerows(rows)

def patch_csv(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['Patch','K','N0','Natal Grounds']);w.writeheader();w.writerows([
          {'Patch':'1','K':'50|48|45','N0':'10','Natal Grounds':'1'},
          {'Patch':'2','K':'50|47|45','N0':'12','Natal Grounds':'1'},
          # Adapter may write N0 on a non-natal patch; pinned CDMetaPOP zeroes it before initialization.
          {'Patch':'3','K':'80|75|70','N0':'40','Natal Grounds':'0'},
        ])

def make_rep(root: Path, work_rel: str, ri: int, ratio: float):
    d=root/work_rel/f'rep_{ri:03d}'/'example_files'
    patch_csv(d/'patchvars'/'PatchVars.csv')
    summary_csv(d/'outputs'/'batchrun0mcrun0'/'summary_popAllTime.csv',22.0,ratio)

def fixture(tmp_path: Path):
    root=tmp_path
    cfg={
      'stage':'v0.6D1-R4.11','affected_frozen_cdmetapop_jobs':AFFECTED,
      'repair_policy':{'reextract_retained_runtime_before_any_rerun':True,'engine_rerun_in_r411':False,'preserve_r43_r49_historical_outputs':True},
      'canonical_state_changed':False,'canonical_replay_authorized':False,'canonical_parameter_change_authorized':False,'deep_biological_coupling':False,'majority_vote':False
    }
    wj(root/'configs/world1_r411_cdmetapop_population_metric_reextraction_v0_6D1_R4_11.json',cfg)
    wj(root/'outputs/v0_6D1_R4_10_SEAL/R4_10_FINAL_SEAL_AUDIT.json',{'status':'PASS_R410_MATCHED_CONTROL_PRECISION_ALTERNATE_EVIDENCE_AND_POPULATION_METRIC_INTEGRITY_AUDIT_SEALED'})
    wj(root/'outputs/v0_6D1_R4_10/R4_10_CDMETAPOP_POPULATION_METRIC_INTEGRITY_AUDIT.json',{'finding':'R43_R49_CDMETAPOP_POPULATION_METRIC_FILENAME_SELECTOR_COLLISION_CONFIRMED'})
    wj(root/'outputs/v0_6D1_R4_10/R4_10_ALTERNATE_EVIDENCE_CLOSURE_PLAN.json',{'status':'R411_PLAN_FROZEN'})
    wt(root/'.arcana_engines/CDMetaPOP-3.08/src/CDmetaPOP_PostProcess.py',"growthPop = tempPop[1:]/tempPop[0:(len(tempPop)-1)]\noutputfile.write(str(N_Init[i][j])+'|')\n")
    wt(root/'.arcana_engines/CDMetaPOP-3.08/src/CDmetaPOP_mainloop.py',"GetMetrics(SubpopIN_init,K,Track_N_Init_pop\nGetMetrics(SubpopIN,K,Track_N_Init_pop,Track_K,loci,alleles,gen+1\n")
    wt(root/'.arcana_engines/CDMetaPOP-3.08/src/CDmetaPOP_PreProcess.py',"N0.append(N0_temp[isub].split('|')[0])\nelif int(N0[isub]) > 0 and natal_patches[isub] == 0:\n    N0[isub] = '0'\n")
    # Four R47 retained reps for each of the five jobs.
    jobs=[]; maps=[]
    for ji,jid in enumerate(AFFECTED):
        reps=[{'replicate_index':i,'seed':10000+ji*100+i} for i in range(4)]
        contract={'frozen_parent_job':{'job_id':jid},'engine_input':{'replicates':reps},'comparison_target':{}}
        wj(root/f'outputs/v0_6D1_R4_3/jobs/{jid}/JOB_CONTRACT.json',contract)
        raw={'stage':'v0.6D1-R4.7','job_id':jid,'engine':'CDMetaPOP','adapter_status':'PASS','replicates':[],'canonical_write':False}
        for r in reps:
            raw['replicates'].append({'replicate_index':r['replicate_index'],'seed':r['seed'],'status':'PASS','metrics':{'initial_population':2.0,'final_population':2.0}})
            make_rep(root, f'outputs/v0_6D1_R4_7/jobs/{jid}/runtime_work', r['replicate_index'], 0.90+0.005*ji)
        wj(root/f'outputs/v0_6D1_R4_7/jobs/{jid}/RAW_EVIDENCE.json',raw)
        jobs.append({'job_id':jid,'window_id':'W0','engine':'CDMetaPOP','earliest_replay_boundary':'R3.11_POST_CHA1'})
        maps.append({'job_id':jid,'domain_mapping':[{'domain':'population_persistence','authority_role':'PRIMARY','comparability_class':'NORMALIZABLE'}]})
    wj(root/'outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json',{'jobs':jobs})
    wj(root/'outputs/v0_6D1_R4_3/R4_3_PER_JOB_UNIT_MAPPING.json',{'mappings':maps})
    wj(root/'outputs/v0_6D1_R4_3/R4_3_WINDOW_BASELINE_DESCRIPTORS.json',{'windows':{'W0':{}}})
    # R48 neutral first 4, same seed ledger as J09.
    j09_contract=json.loads((root/f'outputs/v0_6D1_R4_3/jobs/{J09}/JOB_CONTRACT.json').read_text())
    nraw={'stage':'v0.6D1-R4.8','job_id':J09,'engine':'CDMetaPOP','adapter_status':'PASS','replicates':[],'canonical_write':False}
    for r in j09_contract['engine_input']['replicates']:
        nraw['replicates'].append({'replicate_index':r['replicate_index'],'seed':r['seed'],'status':'PASS','metrics':{'initial_population':2.0,'final_population':2.0}})
        make_rep(root,f'outputs/v0_6D1_R4_8/jobs/{J09}/runtime_work_neutral',r['replicate_index'],1.0)
    wj(root/f'outputs/v0_6D1_R4_8/jobs/{J09}/RAW_NEUTRAL_CONTROL_EVIDENCE.json',nraw)
    # R49 additional 16 dynamic + neutral.
    draw={'stage':'v0.6D1-R4.9','job_id':J09,'engine':'CDMetaPOP','adapter_status':'PASS','replicates':[],'canonical_write':False}
    nr49={'stage':'v0.6D1-R4.9','job_id':J09,'engine':'CDMetaPOP','adapter_status':'PASS','replicates':[],'canonical_write':False}
    for i in range(4,20):
        seed=20000+i
        draw['replicates'].append({'replicate_index':i,'seed':seed,'status':'PASS','metrics':{'initial_population':2.0,'final_population':2.0}})
        nr49['replicates'].append({'replicate_index':i,'seed':seed,'status':'PASS','metrics':{'initial_population':2.0,'final_population':2.0}})
        make_rep(root,f'outputs/v0_6D1_R4_9/jobs/{J09}/runtime_work_additional_dynamic',i,0.91)
        make_rep(root,f'outputs/v0_6D1_R4_9/jobs/{J09}/runtime_work_additional_neutral',i,1.0)
    wj(root/f'outputs/v0_6D1_R4_9/jobs/{J09}/RAW_ADDITIONAL_DYNAMIC_EVIDENCE.json',draw)
    wj(root/f'outputs/v0_6D1_R4_9/jobs/{J09}/RAW_ADDITIONAL_NEUTRAL_EVIDENCE.json',nr49)
    wj(root/'outputs/v0_6D1_R4_9/R4_9_EXPANDED_PAIRED_CAUSAL_EFFECT.json',{'stage':'v0.6D1-R4.9','neutral_factor':1.05,'arcana_causal_forcing_effect_ratio':0.9353883})
    # Frozen adjudication inputs. Descriptor intentionally has no target: test exercises evidence integrity and 75-cell accounting without inventing semantics.
    domains=['population_persistence']+[f'd{i}' for i in range(1,75)]
    wj(root/'configs/world1_r43_historical_revalidation_v0_6D1_R4_3.json',{'window_domain_scope':{'W0':domains}})
    wj(root/'configs/world1_r44_discordance_adjudication_v0_6D1_R4_4.json',{'domain_metric_candidates':{'CDMetaPOP':{'population_persistence':['population_agent_response_ratio']}},'effect_policy':{'ratio_neutral_factor':1.05,'delta_neutral_abs':.02,'concordant_ratio_factor':1.5,'calibration_ratio_factor':4.0,'structural_disagreement_requires_opposite_direction':True,'proxy_only_can_trigger_structural_disagreement':False},'replay_boundary_order':['R3.11_POST_CHA1']})
    cells=[{'window_id':'W0','domain':d,'discordance_class':'INSUFFICIENT_EVIDENCE'} for d in domains]
    wj(root/'outputs/v0_6D1_R4_4/R4_4_CROSS_ENGINE_DOMAIN_DISCORDANCE_MATRIX.json',{'class_counts':{'INSUFFICIENT_EVIDENCE':75},'cells':cells,'evidence_rows':[{'window_id':'W0','domain':'d74','job_id':'NON_CDM','engine':'Other','authority_role':'SECONDARY','mapping_comparability':'PROXY_ONLY','discordance_class':'INSUFFICIENT_EVIDENCE','majority_vote':False}]})
    return root

def test_pipe_total():
    assert pipe_total('22|10|12|')==22.0

def test_summary_parser_reconstructs_final(tmp_path):
    p=tmp_path/'summary_popAllTime.csv';summary_csv(p,22,.9);d=parse_summary_population(p);assert d['initial_population']==22 and math.isclose(d['final_population'],19.8) and math.isclose(d['population_response_ratio'],.9)

def test_summary_parser_lifecycle_chain_clean(tmp_path):
    p=tmp_path/'summary_popAllTime.csv';summary_csv(p);assert parse_summary_population(p)['lifecycle_chain_error_count']==0

def test_summary_parser_rejects_missing_columns(tmp_path):
    p=tmp_path/'summary_popAllTime.csv';wt(p,'Year,N_Initial\n0,22|\n');
    with pytest.raises(ValueError): parse_summary_population(p)

def test_inventory_exact_56(tmp_path):
    r=fixture(tmp_path);inv=retained_runtime_inventory(r);assert inv['observed_replicate_record_count']==56 and inv['pass_count']==56 and inv['failed_count']==0

def test_configured_n0_audit_applies_nonnatal_zeroing(tmp_path):
    p=tmp_path/'rep/example_files/patchvars/PatchVars.csv';patch_csv(p);a=_configured_n0_audit(tmp_path/'rep');assert a['raw_configured_n0_sum']==62.0 and a['engine_effective_n0_sum']==22.0 and a['nonnatal_zeroed_n0_sum']==40.0 and a['rows_zeroed_by_engine_rule']==1

def test_inventory_initial_matches_engine_effective_patch_n0(tmp_path):
    r=fixture(tmp_path);inv=retained_runtime_inventory(r);assert inv['all_initial_populations_match_engine_effective_configured_n0_sum'] is True and inv['all_raw_effective_n0_accounting_consistent'] is True

def test_prepare_passes_complete_retained_runtime(tmp_path):
    r=fixture(tmp_path);out,_=prepare(r);assert out['status']==PREPARED and out['checks_failed']==0 and out['retained_summary_count']==56

def test_prepare_blocks_missing_summary(tmp_path):
    r=fixture(tmp_path);p=next((r/f'outputs/v0_6D1_R4_7/jobs/{AFFECTED[0]}/runtime_work/rep_000').rglob('summary_popAllTime.csv'));p.unlink();out,_=prepare(r);assert out['status']==BLOCKED

def test_execute_reextracts_correct_population_not_two(tmp_path):
    r=fixture(tmp_path);prepare(r);out,_=execute_reextraction_and_readjudicate(r);d=json.loads((r/f'outputs/v0_6D1_R4_11/jobs/{AFFECTED[0]}/CORRECTED_RAW_EVIDENCE.json').read_text());assert out['status']==COMPLETE and d['replicates'][0]['metrics']['initial_population']==22.0 and d['replicates'][0]['metrics']['legacy_buggy_initial_population']==2.0

def test_corrected_normalization_present(tmp_path):
    r=fixture(tmp_path);prepare(r);execute_reextraction_and_readjudicate(r);d=json.loads((r/f'outputs/v0_6D1_R4_11/jobs/{AFFECTED[0]}/CORRECTED_NORMALIZED_EVIDENCE.json').read_text());assert 'population_agent_response_ratio' in d['normalized_metrics']

def test_corrected_matched_control_has_20_pairs(tmp_path):
    r=fixture(tmp_path);prepare(r);execute_reextraction_and_readjudicate(r);d=json.loads((r/'outputs/v0_6D1_R4_11/R4_11_CORRECTED_MATCHED_CONTROL_CAUSAL_EFFECT.json').read_text());assert d['pair_count']==20 and all(x['initial_population_match'] for x in d['paired_replicates'])

def test_corrected_matched_control_same_direction_fixture(tmp_path):
    r=fixture(tmp_path);prepare(r);execute_reextraction_and_readjudicate(r);d=json.loads((r/'outputs/v0_6D1_R4_11/R4_11_CORRECTED_MATCHED_CONTROL_CAUSAL_EFFECT.json').read_text());assert d['diagnosis_class']=='R411_CORRECTED_MATCHED_CONTROL_SAME_DIRECTION_ROBUST'

def test_matrix_has_75_cells(tmp_path):
    r=fixture(tmp_path);prepare(r);execute_reextraction_and_readjudicate(r);d=json.loads((r/'outputs/v0_6D1_R4_11/R4_11_CDMETAPOP_METRIC_REPAIRED_READJUDICATED_MATRIX.json').read_text());assert d['cell_count']==75 and sum(d['class_counts'].values())==75

def test_no_engine_rerun(tmp_path):
    r=fixture(tmp_path);prepare(r);execute_reextraction_and_readjudicate(r);d=json.loads((r/'outputs/v0_6D1_R4_11/R4_11_EXECUTION_SUMMARY.json').read_text());assert d['engine_rerun_performed'] is False

def test_final_seal(tmp_path):
    r=fixture(tmp_path);prepare(r);execute_reextraction_and_readjudicate(r);out,checks=final_seal(r);assert out['status']==SEALED and out['verdict']=='SEALED' and all(c.passed for c in checks)

def test_final_seal_blocks_without_execution(tmp_path):
    r=fixture(tmp_path);prepare(r);out,_=final_seal(r);assert out['status']==BLOCKED
