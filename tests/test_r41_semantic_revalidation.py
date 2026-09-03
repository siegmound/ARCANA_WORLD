from __future__ import annotations
import json,sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines import r41_semantic_revalidation as r


def cfg(): return json.loads((ROOT/r.R41_CONFIG_REL).read_text(encoding='utf-8'))

DOMAINS=[
 'population_persistence','range_occupancy','range_shift_rate','connectivity','gene_flow','additive_variance','trait_response','admixture','ancestry','biomass','trophic_opportunity','extinction_risk','founder_persistence','managed_wild_isolation','producer_divergence'
]
WINDOWS=[
 {'id':'H0_DEEP_TIME_BACKGROUND','age_start_ma':210.0,'age_end_ma':200.0,'engines':['Madingley','RangeShifter','CDMetaPOP'],'earliest_replay_boundary':'H0_210MA'},
 {'id':'H0_PRE_CHA1','age_start_ma':70.0,'age_end_ma':66.0,'engines':['Madingley','RangeShifter','CDMetaPOP'],'earliest_replay_boundary':'R3.9_PRE_CHA1'},
 {'id':'H0_POST_CHA1_RECOVERY','age_start_ma':65.5,'age_end_ma':55.0,'engines':['Madingley','RangeShifter','CDMetaPOP','NEMO'],'earliest_replay_boundary':'R3.11_POST_CHA1'},
 {'id':'H0_LATE_CENOZOIC','age_start_ma':30.0,'age_end_ma':0.2,'engines':['Madingley','RangeShifter','NEMO'],'earliest_replay_boundary':'R3.14_LATE_CENOZOIC'},
 {'id':'SAPIENT_3MA_TO_200KA','age_start_ma':3.0,'age_end_ma':0.2,'engines':['Geonomics','CDMetaPOP','SLiM','NEMO'],'earliest_replay_boundary':'R3.27'},
 {'id':'SAPIENT_200KA_TO_0','age_start_ka':200.0,'age_end_ka':0.0,'engines':['Geonomics','SLiM','CDMetaPOP'],'earliest_replay_boundary':'R3.28'},
 {'id':'PRODUCER_20KA_TO_0','age_start_ka':20.0,'age_end_ka':0.0,'engines':['Geonomics','SLiM','RangeShifter'],'earliest_replay_boundary':'R3.34'}
]

def r40_cfg(): return {'frozen_revalidation_windows':WINDOWS,'comparison_domains':DOMAINS}

def good_rows(c):
    metrics={
      'R41_NEMO_B1_ADMIXTURE_CONVERGENCE':{'initial_mean_frequency_gap':0.45,'final_mean_frequency_gap':0.08,'qfreq_rows':16,'generations':100,'patches':2},
      'R41_GEONOMICS_DEFAULT_SPATIAL_DEMOGRAPHY':{'species_count':1,'terminal_population_total':100,'occupied_cells_total':20,'model_class':'Model'},
      'R41_MADINGLEY_ONE_YEAR_ECOSYSTEM':{'initial_cohort_count':20,'final_cohort_count':21,'initial_stock_count':2,'final_stock_count':2,'years':1},
      'R41_RANGESHIFTR_DEFAULT_RANGE_DYNAMICS':{'initial_abundance':100,'final_abundance':120,'initial_occupied_cells':10,'final_occupied_cells':12,'years':10},
      'R41_CDMETAPOP_BUNDLED_5GEN_EXAMPLE':{'scenario_rows':4,'runtime_generations':5,'new_output_files':10,'csv_output_files':5,'source_commit':'3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118'},
      'R41_SLIM_TWO_POP_TREESEQ_GENE_FLOW':{'tree_nodes':1000,'tree_edges':900,'tree_individuals':400,'tree_mutations':2,'sequence_length':10000.0,'generations':50},
    }
    rows=[]
    for spec in c['microbenchmarks']:
      rows.append({'benchmark_id':spec['id'],'engine':spec['engine'],'confirmed_version':c['required_engines'][spec['engine']],'status':'PASS','returncode':0,'metrics':metrics[spec['id']]})
    return rows

def build_fixture(tmp_path, mutate=None):
    c=cfg(); (tmp_path/'configs').mkdir(parents=True)
    (tmp_path/r.R41_CONFIG_REL).write_text(json.dumps(c),encoding='utf-8')
    (tmp_path/r.R40_CONFIG_REL).write_text(json.dumps(r40_cfg()),encoding='utf-8')
    sp=tmp_path/r.R40_SEAL_REL; sp.parent.mkdir(parents=True)
    sp.write_text(json.dumps({'status':r.R40_SEALED,'verdict':'SEALED','checks_failed':0,'summary':{'all_required_engines_ready':True,'ready_engines':sorted(c['required_engines'])}}),encoding='utf-8')
    rows=good_rows(c)
    if mutate: mutate(rows)
    ep=tmp_path/r.R41_HOST_EVIDENCE_REL; ep.parent.mkdir(parents=True,exist_ok=True)
    ep.write_text(json.dumps({'stage':r.STAGE,'evidence_type':'CONTROLLED_MULTI_ENGINE_MICROBENCHMARK_EVIDENCE','canonical_state_changed':False,'benchmarks':rows}),encoding='utf-8')
    return c


def test_stage_and_parent(): assert cfg()['stage']=='v0.6D1-R4.1' and cfg()['parent_stage']=='v0.6D1-R4.0'
def test_parent_status_exact(): assert cfg()['required_parent_status']==r.R40_SEALED
def test_no_canonical_write(): assert cfg()['canonical_state_changed'] is False and cfg()['external_engine_direct_canonical_write'] is False
def test_deep_off(): assert cfg()['deep_biological_coupling'] is False
def test_no_auto_promotion(): assert cfg()['automatic_external_evidence_promotion'] is False
def test_six_engines_exact(): assert cfg()['required_engines']=={'NEMO':'2.4.2','Geonomics':'1.4.9','Madingley':'MadingleyR-1.0.6__CPP-2.02','RangeShifter':'3.0.1','CDMetaPOP':'3.08','SLiM':'5.2'}
def test_six_microbenchmarks(): assert len(cfg()['microbenchmarks'])==6 and len({x['engine'] for x in cfg()['microbenchmarks']})==6
def test_all_domains_exact(): assert set(cfg()['domain_authority'])==set(DOMAINS)
def test_no_domain_voting(): assert all(x['vote'] is False for x in cfg()['domain_authority'].values())
def test_range_primary_rangeshifter(): assert cfg()['domain_authority']['range_shift_rate']['primary']==['RangeShifter']
def test_biomass_primary_madingley(): assert cfg()['domain_authority']['biomass']['primary']==['Madingley']
def test_ancestry_primary_slim(): assert cfg()['domain_authority']['ancestry']['primary']==['SLiM']
def test_nemo_not_trait_response_primary(): assert 'NEMO' not in cfg()['domain_authority']['trait_response']['primary']
def test_no_literal_population_equivalence(): assert cfg()['semantic_rules']['population_scale']['rule']=='NO_LITERAL_CROSS_ENGINE_N_EQUIVALENCE'
def test_explicit_time_mapping_required(): assert cfg()['semantic_rules']['time_scale']['historical_window_execution_requires_generation_interval'] is True
def test_single_runs_semantic_only(): assert cfg()['semantic_rules']['uncertainty']['single_run_use']=='SEMANTIC_AND_EXECUTABLE_GATE_ONLY'
def test_r41_does_not_execute_windows(): assert cfg()['historical_window_gate']['execute_in_r41'] is False
def test_r42_is_next_stage(): assert cfg()['historical_window_gate']['next_stage']=='v0.6D1-R4.2'
def test_frozen_matrix_hash_matches_snapshot(): assert r.frozen_r40_matrix_hash(r40_cfg())==cfg()['r40_frozen_matrix_sha256']
def test_metric_nemo_good():
 c=cfg(); spec=next(x for x in c['microbenchmarks'] if x['engine']=='NEMO'); ok,_=r._metric_check(spec['id'],good_rows(c)[0]['metrics'],spec); assert ok
def test_metric_nemo_rejects_nonconvergence():
 c=cfg(); spec=next(x for x in c['microbenchmarks'] if x['engine']=='NEMO'); m={'initial_mean_frequency_gap':.45,'final_mean_frequency_gap':.5,'qfreq_rows':16,'generations':100,'patches':2}; assert not r._metric_check(spec['id'],m,spec)[0]
def test_metric_slim_allows_zero_mutations():
 c=cfg(); spec=next(x for x in c['microbenchmarks'] if x['engine']=='SLiM'); m=next(x['metrics'] for x in good_rows(c) if x['engine']=='SLiM'); m=dict(m); m['tree_mutations']=0; assert r._metric_check(spec['id'],m,spec)[0]
def test_good_fixture_ready(tmp_path):
 build_fixture(tmp_path); rep,checks=r.build_report(tmp_path); assert rep['status']==r.R41_READY and not [x for x in checks if not x.passed]
def test_fixture_version_drift_blocks(tmp_path):
 def mut(rows): next(x for x in rows if x['engine']=='RangeShifter')['confirmed_version']='3.0.0'
 build_fixture(tmp_path,mut); rep,checks=r.build_report(tmp_path); assert rep['status']!=r.R41_READY and any(not x.passed and 'version_pin' in x.name for x in checks)
def test_fixture_missing_benchmark_blocks(tmp_path):
 build_fixture(tmp_path,lambda rows: rows.pop()); rep,_=r.build_report(tmp_path); assert rep['checks_failed']>0
def test_fixture_parent_not_sealed_blocks(tmp_path):
 build_fixture(tmp_path); p=tmp_path/r.R40_SEAL_REL; d=json.loads(p.read_text()); d['verdict']='BLOCKED'; p.write_text(json.dumps(d)); rep,_=r.build_report(tmp_path); assert rep['checks_failed']>0
def test_historical_gate_authorized_only_on_pass():
 c=cfg(); g=r.build_historical_gate(c,r40_cfg(),True); assert g['status']=='AUTHORIZED_FOR_R42' and len(g['windows'])==7 and all(x['authorized_for_r42_execution'] for x in g['windows'])
def test_historical_gate_pre_result():
 g=r.build_historical_gate(cfg(),r40_cfg(),True); assert all(x['selection_based_on_r41_results'] is False for x in g['windows'])
def test_authority_matrix_frozen_pre_result():
 a=r.build_authority_matrix(cfg()); assert a['status']=='FROZEN_PRE_RESULT' and a['majority_vote'] is False

def test_nemo_ini_uses_validated_lifecycle_and_symmetric_matrix():
 t=(ROOT/'benchmarks/r41/Nemo2_R41_B1.ini').read_text(); assert 'quanti_init             1' in t and 'breed_disperse          2' in t and 'mating_isWrightFisher' in t and '{{0.95, 0.05}' in t and '{0.05, 0.95}}' in t
def test_nemo_microbenchmark_has_no_selection_or_mutation():
 t=(ROOT/'benchmarks/r41/Nemo2_R41_B1.ini').read_text(); assert 'quanti_mutation_rate    0' in t and 'selection' not in t.lower()
def test_geonomics_benchmark_runs_documented_default_model():
 t=(ROOT/'benchmarks/r41/geonomics_r41.py').read_text(); assert 'gnx.run_default_model()' in t and "getattr(mod,'comm'" in t
def test_madingley_benchmark_init_and_run():
 t=(ROOT/'benchmarks/r41/madingley_r41.R').read_text(); assert 'madingley_init' in t and 'madingley_run' in t and 'years=1' in t
def test_rangeshifter_benchmark_uses_real_run_and_population_dataframe_output():
 t=(ROOT/'benchmarks/r41/rangeshiftr_r41.R').read_text(); assert 'RSsim' in t and 'RunRS' in t and 'ReturnPopDataFrame=TRUE' in t and 'totalAbundance' in t
def test_cdmetapop_benchmark_pinned_commit():
 t=(ROOT/'benchmarks/r41/cdmetapop_r41.py').read_text(); assert '3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118' in t and 'RunVars.csv' in t and 'CDmetaPOP.py' in t
def test_slim_benchmark_records_tree_sequence_and_migration():
 t=(ROOT/'benchmarks/r41/R41_two_pop_gene_flow.slim').read_text(); assert 'initializeTreeSeq()' in t and 'setMigrationRates' in t and 'treeSeqOutput' in t
def test_capture_bridge_uses_bash_stdin_and_fresh_workdirs():
 t=(ROOT/'capture_v0_6D1_R4_1_microbenchmarks.ps1').read_text(); assert 'bash -s' in t and 'Remove-Item -Recurse -Force $WorkDir' in t and 'Passed benchmarks:' in t
def test_capture_bridge_uses_existing_r40_bindings():
 t=(ROOT/'capture_v0_6D1_R4_1_microbenchmarks.ps1').read_text(); assert 'set_r40_engine_env.local.ps1' in t and 'R4_1_RUNTIME_IDENTITY_EVIDENCE.json' in t
def test_runner_recaptures_exact_runtime_identity_before_benchmarks():
 t=(ROOT/'run_v0_6D1_R4_1.ps1').read_text(); assert 'capture_v0_6D1_R4_0_runtime_evidence.ps1' in t and t.index('fresh exact runtime identity evidence') < t.index('controlled scientific microbenchmarks')
def test_runner_does_not_start_historical_window_execution():
 t=(ROOT/'run_v0_6D1_R4_1.ps1').read_text(); assert 'R4.2' not in t and 'historical window execution gate' in t
def test_final_status_distinct(): assert r.R41_SEALED != r.R41_READY and 'SEALED' in r.R41_SEALED

def test_r_collectors_escape_json_error_text_with_base_encode_string():
 for rel in ['benchmarks/r41/madingley_r41.R','benchmarks/r41/rangeshiftr_r41.R']:
  t=(ROOT/rel).read_text()
  assert 'encodeString(as.character(x), quote=' in t
  assert 'json_escape(err)' in t


def test_capture_bridge_drains_stdout_and_stderr_concurrently():
 t=(ROOT/'capture_v0_6D1_R4_1_microbenchmarks.ps1').read_text()
 assert '$p.StandardOutput.ReadToEndAsync()' in t
 assert '$p.StandardError.ReadToEndAsync()' in t
 assert '$p.StandardOutput.ReadToEnd(); $stderr=$p.StandardError.ReadToEnd()' not in t

def test_capture_bridge_has_heartbeat_and_timeout():
 t=(ROOT/'capture_v0_6D1_R4_1_microbenchmarks.ps1').read_text()
 assert 'still running' in t and 'TimeoutSeconds' in t and 'ARCANA_R41_TIMEOUT' in t
 assert 'Invoke-WslScript $geoScript "Geonomics" 3600 30' in t


def test_rangeshifter_benchmark_uses_complete_explicit_parameter_master():
 t=(ROOT/'benchmarks/r41/rangeshiftr_r41.R').read_text()
 for token in ['ArtificialLandscape','Demography(','Dispersal(','Initialise(','validateRSparams','seed=410041']:
  assert token in t

def test_cdmetapop_collector_prefers_exact_pinned_entrypoint_and_preserves_engine_log():
 t=(ROOT/'benchmarks/r41/cdmetapop_r41.py').read_text()
 assert "repo/'src'/'CDmetaPOP.py'" in t
 assert 'engine_log_tail' in t and 'output_root_directories' in t

def test_r41_console_surfaces_failed_benchmark_diagnostics():
 t=(ROOT/'scripts/run_v0_6D1_R4_1.py').read_text()
 assert "'stderr_tail':x.get('stderr_tail')" in t and "x.get('status')!='PASS'" in t


def test_capture_preserves_nested_engine_diagnostics():
 t=(ROOT/'capture_v0_6D1_R4_1_microbenchmarks.ps1').read_text()
 assert '$raw.engine_log_tail' in t and 'result_stderr_tail=$resultStderrTail' in t

def test_cdmetapop_still_requires_real_csv_outputs():
 t=(ROOT/'benchmarks/r41/cdmetapop_r41.py').read_text()
 assert "metrics['csv_output_files']>0" in t and "proc.returncode==0" in t

def test_rangeshifter_single_replicate_population_dataframe_avoids_native_multi_rep_occupancy_path():
 t=(ROOT/'benchmarks/r41/rangeshiftr_r41.R').read_text()
 assert 'Replicates=1' in t
 assert 'OutIntOcc=0' in t and 'ReturnPopDataFrame=TRUE' in t
 assert 'FreeType=1' in t and 'NrCells=' not in t
 assert 'sum(p0$totalAbundance>0' in t and 'sum(p1$totalAbundance>0' in t
 assert "occupancy_semantics='single_replicate_positive_abundance_cells'" in t
 assert 'dedicated_multi_replicate_occupancy_output=FALSE' in t
 assert 'replicates=1L' in t

def test_cdmetapop_uses_generic_pinned_example_with_isolated_schema_shim():
 t=(ROOT/'benchmarks/r41/cdmetapop_r41.py').read_text()
 assert "upstream_runvars=inp/'RunVars.csv'" in t
 assert "generic_popvars=inp/'popvars'/'PopVars.csv'" in t
 assert "pop_fields.append('implement_disease')" in t
 assert "row['implement_disease']='N'" in t
 assert "RunVars_R41.csv" in t and "PopVars_R41.csv" in t
 assert "benchmark_pop_rows=[dict(pop_rows[0])]" in t
 assert "rows[0]['Popvars']='popvars/PopVars_R41.csv'" in t
 assert "rows[0]['runtime']='5'" in t and "rows[0]['mcruns']='1'" in t
 assert "shutil.copytree(examples,inp)" in t
 assert "source_tree_modified':False" in t
 assert "benchmark_popvars_isolated_first_row':popvar_rows==1" in t
 assert "PatchVars.csv" in t and "ClassVars_AS1.csv" in t

def test_cdmetapop_output_root_matches_pinned_entrypoint_semantics():
 t=(ROOT/'benchmarks/r41/cdmetapop_r41.py').read_text()
 assert "inp.glob('R41_smoke*')" in t
 assert "metrics['output_root_directories']>0" in t
 assert "run_output_directories" not in t
