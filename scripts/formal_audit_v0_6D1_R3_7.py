from pathlib import Path
import hashlib, json, sys
from arcana_worldsim.scientific_engines.r37_validation import analyze_r37_reference_closure
from arcana_worldsim.scientific_engines.segregation_aware_admixture import SegregationAwareAdmixtureConfig

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'reference_results'/'v0_6D1_R3_6D_RAW_RESULTS.zip'
R36E=ROOT/'reference_results'/'R3_6E_CAUSAL_INFERENCE.json'
r=analyze_r37_reference_closure(RAW,R36E)
checks=[]
def check(name,cond): checks.append((name,bool(cond)))

check('raw_r36d_results_present',RAW.is_file())
check('r36e_inference_present',R36E.is_file())
check('r36e_structural_mismatch_parent',r['source_r36e_verdict'].startswith('STRUCTURAL_ADMIXTURE_OPERATOR_MISMATCH_SUPPORTED'))
check('reference_closure_verdict',r['verdict'].startswith('PASS_SEGREGATION_AWARE_OPERATOR_REFERENCE_CLOSURE'))
check('four_reference_rows',len(r['operator_reference_rows'])==4)
check('analytic_relative_error_lt_1e8',r['max_relative_error_vs_analytic']<1e-8)
check('legacy_over_repaired_gt_100',r['minimum_legacy_over_repaired_factor']>100)
check('free_recomb_transient_retention_lt_1e3',r['maximum_ancestry_post_over_pre']<1e-3)
check('first_moment_closure',max(x['first_moment_conservation_max_abs'] for x in r['operator_reference_rows'])<1e-9)
check('pre_recomb_total_variance_closure',max(x['pre_recombination_total_variance_closure_max_abs'] for x in r['operator_reference_rows'])<1e-10)
check('current_species_exchange_cap_locked',SegregationAwareAdmixtureConfig().maximum_total_exchange_fraction_per_deme==0.45)
check('reference_recombination_is_explicit',SegregationAwareAdmixtureConfig().recombination_fraction_per_generation==0.5)
check('no_canonical_write',not r['canonical_write_allowed'])
check('no_production_binding',not r['production_runtime_binding_allowed'])
check('no_mu_b_change',not r['mu_b_change_authorized'])
check('no_ceiling_change',not r['ceiling_change_authorized'])
check('no_state_initialization_authority',not r['state_initialization_authorized'])
check('no_state_evolution_authority',not r['state_evolution_authorized'])
# Sealed/parent scientific authorities must remain byte-identical.
expected={
 'src/d3_additive_variance_v0_6_3D3_3A.py':'3b235b186e234f66a77443bec3a46c80ef699ecd715737be7d36103db01b4c21',
 'src/d3_paleogeographic_history_v0_6_3D3_2C.py':'5831f41ba9cd7bc05be0cd25f8cd84e895c6c9fa453bde7634d7b27c82394730',
 'src/rebased_natural_control_runtime_v0_6D1_R3_4.py':'087d05f532d84f53f8c99d08ae0099657792526eb3aa97bab7cb9e64cb342e45',
 'src/rebased_natural_control_runtime_v0_6D1_R3_5.py':'634237eb15383000e88180b890ead9b6facc281c0a77eb5ce00efe32f3d0bc95',
}
for path,sha in expected.items():
    p=ROOT/path
    check('parent_hash_'+Path(path).name,p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==sha)
for i,(n,ok) in enumerate(checks,1): print(f'{i:02d} {"PASS" if ok else "FAIL"} {n}')
passed=sum(ok for _,ok in checks)
print(json.dumps({'stage':'v0.6D1-R3.7','passed':passed,'total':len(checks),'verdict':r['verdict']},indent=2))
sys.exit(0 if passed==len(checks) else 2)
