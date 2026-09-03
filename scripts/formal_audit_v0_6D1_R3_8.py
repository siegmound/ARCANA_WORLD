from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def sha(p:Path):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
 return h.hexdigest()
checks=[]
def ck(name,cond,detail=''):
 checks.append({'name':name,'pass':bool(cond),'detail':str(detail)})

parent=json.loads((ROOT/'PACKAGE_MANIFEST_v0_6D1_R3_7I.json').read_text())
mis=[]
for r in parent['files']:
 p=ROOT/r['path']
 if not p.exists() or sha(p)!=r['sha256']: mis.append(r['path'])
ck('parent_r37i_manifest_all_files_unchanged',not mis,f'{len(parent["files"])-len(mis)}/{len(parent["files"])}; mismatches={mis[:5]}')
ck('parent_r37i_release_state_sealed',parent.get('release_state')=='SEALED')
sealp=ROOT/'outputs/v0_6D1_R3_7I/PRODUCTION_PROMOTION_SEAL_v0_6D1_R3_7I.json'; seal=json.loads(sealp.read_text())
ck('promotion_seal_pass',seal.get('status')=='PASS_PRODUCTION_PROMOTION_SEAL')
ck('canonical_binding_authorized',seal['authority'].get('canonical_runtime_binding_authorized') is True)
ck('scalar_k_not_physical_constant',seal['authority'].get('scalar_k_physical_constant_authorized') is False)
ck('mu_b_ceiling_unchanged',seal['authority'].get('mu_b_or_ceiling_change_authorized') is False)
refp=ROOT/'references/v0_6D1_R3_8/R37H_210_150_K_CENTER_SEALED_REFERENCE.json'
ck('r37h_center_reference_present',refp.exists())
ck('r37h_center_reference_hash_bound_to_seal',sha(refp)==seal['r37h_full_closed_loop_evidence']['json_sha256']['K_CENTER'],sha(refp))
mod=ROOT/'src/arcana_worldsim/scientific_engines/r38_restartable_checkpoint.py'; text=mod.read_text()
ck('r38_module_present',mod.exists())
for token in ['CHECKPOINT_AGE_MA = 150.0','NOMINAL_K = BRANCH_K["K_CENTER"]','reduced_va_within','reduced_ancestry_covariance','reduced_neutral_segregation_potential','reduced_adaptive_coordinate','ri_state','clock_state','founder_state','vicariance_state','reconnection_state','child_counters','baselines','generation_time']:
 ck('source_contains_'+token.replace(' ','_').replace('"','').replace('=','eq').replace('.','p'),token in text)
ck('canonical_checkpoint_schema_present','ARCANA_R38_CANONICAL_150MA_CHECKPOINT_V1' in text)
ck('restart_state_comparison_present','compare_runtime_states' in text)
ck('r37h_reference_comparison_present','compare_to_r37h_center_reference' in text)
runner=ROOT/'scripts/run_v0_6D1_R3_8_checkpoint_validation.py'; rtext=runner.read_text()
ck('full_runner_present',runner.exists())
ck('full_runner_validates_promotion_seal','validate_promotion_seal' in rtext)
ck('full_runner_uses_480_gate',"len(records_to_150)==480" in rtext)
ck('full_runner_uses_8_step_restart_gate',"len(records_direct)==8" in rtext and "len(records_restart)==8" in rtext)
ck('full_runner_compares_serialization','checkpoint_serialization_identity' in rtext)
ck('full_runner_compares_restart','restart_150_to_149_identity' in rtext)
ck('powershell_runner_present',(ROOT/'run_v0_6D1_R3_8_checkpoint_validation.ps1').exists())
for f in ['CANONICAL_150MA_CONTINUATION_CHECKPOINT_CONTRACT_v0_6D1_R3_8.md','R3_8_DIAGNOSTIC_SMOKE_AUDIT.md','V0_6D1_R3_8_STATUS.md','README_R3_8.md','NEXT_STAGE_HANDOFF_v0_6D1_R3_8.md']:
 ck('doc_'+f,(ROOT/f).exists())
smoke_p=ROOT/'outputs/v0_6D1_R3_8/R3_8_DIAGNOSTIC_SMOKE_AUDIT.json'; smoke=json.loads(smoke_p.read_text())
ck('diagnostic_smoke_pass',smoke['verdict'].startswith('PASS_'))
ck('diagnostic_r37i_population_parity',smoke['r37i_210_209_equivalence']['population_abs_error']<=2e-12)
ck('diagnostic_r37i_q_parity',smoke['r37i_210_209_equivalence']['q_max_abs_error']<=2e-12)
ck('diagnostic_serialization_identity',smoke['checkpoint_serialization_identity']['equivalent'] is True)
ck('diagnostic_restart_identity',smoke['restart_209_to_208_identity']['equivalent'] is True)
ck('diagnostic_does_not_authorize_150_checkpoint',smoke['governance']['canonical_150ma_checkpoint_authorized'] is False)
cpdir=ROOT/'local_runs/v0_6D1_R3_8'
canon_cp=list(cpdir.glob('WORLD1_150Ma_CANONICAL_CONTINUATION_CHECKPOINT_v0_6D1_R3_8.*')) if cpdir.exists() else []
ck('candidate_contains_no_unvalidated_150ma_checkpoint',len(canon_cp)==0,canon_cp)
ck('deep_biological_coupling_not_enabled','Deep_biological_coupling' not in text or 'True' not in text)
passed=sum(x['pass'] for x in checks); out={'stage':'v0.6D1-R3.8','verdict':'PASS_R38_IMPLEMENTATION_AND_DIAGNOSTIC_AUDIT__FULL_150MA_CHECKPOINT_PENDING_LOCAL_EXECUTION' if passed==len(checks) else 'FAIL_R38_FORMAL_AUDIT','checks_passed':passed,'check_count':len(checks),'checks':checks}
op=ROOT/'outputs/v0_6D1_R3_8/FORMAL_AUDIT_v0_6D1_R3_8.json'; op.parent.mkdir(parents=True,exist_ok=True); op.write_text(json.dumps(out,indent=2))
print(json.dumps({'stage':out['stage'],'verdict':out['verdict'],'checks_passed':passed,'check_count':len(checks),'output':str(op)},indent=2))
if passed!=len(checks):
 for x in checks:
  if not x['pass']: print('FAIL',x['name'],x['detail'])
 raise SystemExit(2)
