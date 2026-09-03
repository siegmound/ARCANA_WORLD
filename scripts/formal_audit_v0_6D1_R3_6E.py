from pathlib import Path
import hashlib, json, sys
from arcana_worldsim.scientific_engines.r36e_inference import analyze_r36d_results_zip
ROOT=Path(__file__).resolve().parents[1]
zip_path=ROOT/'reference_results'/'v0_6D1_R3_6D_RAW_RESULTS.zip'
r=analyze_r36d_results_zip(zip_path)
checks=[]
def check(name, cond): checks.append((name,bool(cond)))
check('source_zip_present',zip_path.is_file())
check('r36d_40_jobs',r['source_job_count']==40)
check('r36d_40_executed',r['source_executed_count']==40)
check('r36d_40_parsed',r['source_parsed_complete_count']==40)
check('structural_mismatch_verdict',r['verdict'].startswith('STRUCTURAL_ADMIXTURE_OPERATOR_MISMATCH_SUPPORTED'))
vals=r['three_way_causal_comparison']
check('all_8_comparisons',len(vals)==8)
check('arcana_over_analytic_min_gt_100',min(x['arcana_1x125k_over_analytic'] for x in vals)>100)
check('nemo_over_analytic_max_lt_4',max(x['nemo_over_analytic'] for x in vals)<4)
check('nemo_over_analytic_min_gt_0p25',min(x['nemo_over_analytic'] for x in vals)>0.25)
check('b1_near_2L',all(abs(x['arcana_1x125k_over_analytic']-128)<2 for x in vals if x['pair']=='B1_TWO_DEME_ADMIXTURE'))
check('qst_flow_min_gt_0p9',min(x['nemo_stat_Qst_min'] for x in r['nemo_flow_structure'])>0.9)
check('no_canonical_write',not r['canonical_write_allowed'])
check('no_auto_calibration',not r['automatic_calibration_allowed'])
check('no_mu_b_recalibration',not r['mu_b_recalibration_authorized'])
check('no_ceiling_change',not r['ceiling_change_authorized'])
check('no_production_replay',not r['production_r3_5_replay_authorized'])
for i,(n,ok) in enumerate(checks,1): print(f'{i:02d} {"PASS" if ok else "FAIL"} {n}')
passed=sum(ok for _,ok in checks)
print(json.dumps({'stage':'v0.6D1-R3.6E','passed':passed,'total':len(checks),'verdict':r['verdict'],'source_results_sha256':hashlib.sha256(zip_path.read_bytes()).hexdigest()},indent=2))
sys.exit(0 if passed==len(checks) else 2)
