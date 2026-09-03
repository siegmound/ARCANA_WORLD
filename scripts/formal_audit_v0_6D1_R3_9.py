from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256();
 with Path(p).open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
 return h.hexdigest()
checks=[]
def ck(n,c,d=''): checks.append({'name':n,'pass':bool(c),'detail':str(d)})
parent=json.loads((ROOT/'PACKAGE_MANIFEST_v0_6D1_R3_8.json').read_text()); mis=[]
for r in parent['files']:
 p=ROOT/r['path']
 if not p.exists() or sha(p)!=r['sha256']: mis.append(r['path'])
ck('parent_r38_all_files_unchanged',not mis,f'{len(parent["files"])-len(mis)}/{len(parent["files"])}; mismatches={mis[:5]}')
ck('parent_r38_sealed',parent.get('release_state')=='SEALED_CANONICAL_150MA_RESTART_BOUNDARY')
auth=json.loads((ROOT/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_8.json').read_text())
ck('r38_checkpoint_authorized',auth.get('governance',{}).get('canonical_150ma_checkpoint_authorized') is True)
for kind in ['json','npz']:
 e=auth['canonical_checkpoint'][kind]; ck('r38_'+kind+'_hash_valid',sha(ROOT/e['path'])==e['sha256'],sha(ROOT/e['path']))
cha=json.loads((ROOT/'outputs/CHA1_PULSE_REFERENCE_AUDIT_v0_6D.json').read_text())
ck('cha1_exact_event_audit_pass',cha.get('status')=='PASS_CHA1_EXACT_EVENT_TIME_PULSE_REFERENCE_AUDIT')
ck('cha1_exact_event_preferred',cha.get('exact_event_time_preferred') is True)
ck('cha1_preimpact_pulse_zero',cha.get('pulse_before_impact_j')==[0.0]*5)
ck('cha1_impact_pulse_positive',float(cha.get('pulse_at_impact_total_j',0))>0)
mod=ROOT/'src/arcana_worldsim/scientific_engines/r39_precha1_continuation.py'; text=mod.read_text()
for tok in ["PRE_CHA1_AGE_MA=66.0","EXPECTED_STEPS_150_TO_66=672","PRE_IMPACT_66P0_MINUS","'cha1_applied':False","'deep_biological_coupling':False","ordinary_125kyr_continuation_ends_here","next_operator_must_be_dedicated_cha1_high_resolution_event"]:
 ck('source_'+tok.replace(' ','_').replace("'",'').replace('=','eq').replace('.','p'),tok in text)
runner=ROOT/'scripts/run_v0_6D1_R3_9_precha1_continuation.py'; rt=runner.read_text()
ck('runner_present',runner.exists())
ck('runner_loads_r38_authority','validate_r38_checkpoint_authority' in rt)
ck('runner_validates_cha1_event_authority','validate_cha1_exact_event_authority' in rt)
ck('runner_uses_672_gate','EXPECTED_STEPS_150_TO_66' in rt)
ck('runner_forbids_cha1_events','forbidden_cha1_events_found' in rt)
ck('runner_serialization_gate','serialization_identity' in rt)
sm=json.loads((ROOT/'outputs/v0_6D1_R3_9/R3_9_DIAGNOSTIC_SMOKE.json').read_text())
ck('diagnostic_smoke_pass',sm['verdict'].startswith('PASS_'))
ck('diagnostic_uses_sealed_checkpoint',sm['r38_checkpoint_hashes_valid'] is True)
ck('diagnostic_cha1_authority_valid',sm['cha1_exact_event_authority_valid'] is True)
ck('diagnostic_cha1_not_applied',sm['cha1_applied'] is False)
ck('diagnostic_deep_off',sm['deep_biological_coupling'] is False)
full=ROOT/'local_runs/v0_6D1_R3_9'; cps=list(full.glob('WORLD1_H0_66Ma_PRE_CHA1_CANONICAL_CHECKPOINT_v0_6D1_R3_9.*')) if full.exists() else []
ck('candidate_has_no_unvalidated_precha1_checkpoint',len(cps)==0,cps)
for f in ['CANONICAL_150_TO_66_PRE_CHA1_CONTINUATION_CONTRACT_v0_6D1_R3_9.md','R3_9_DIAGNOSTIC_SMOKE_AUDIT.md','V0_6D1_R3_9_STATUS.md','README_R3_9.md','NEXT_STAGE_HANDOFF_v0_6D1_R3_9.md','run_v0_6D1_R3_9_precha1_continuation.ps1']:
 ck('file_'+f,(ROOT/f).exists())
passed=sum(x['pass'] for x in checks); out={'stage':'v0.6D1-R3.9','verdict':'PASS_R39_IMPLEMENTATION_AND_PRECHA1_BOUNDARY_AUDIT__FULL_150_TO_66_LOCAL_RUN_PENDING' if passed==len(checks) else 'FAIL_R39_FORMAL_AUDIT','checks_passed':passed,'check_count':len(checks),'checks':checks}
p=ROOT/'outputs/v0_6D1_R3_9/FORMAL_AUDIT_v0_6D1_R3_9.json'; p.write_text(json.dumps(out,indent=2)); print(json.dumps({k:out[k] for k in ['stage','verdict','checks_passed','check_count']},indent=2))
if passed!=len(checks):
 [print('FAIL',x['name'],x['detail']) for x in checks if not x['pass']]; raise SystemExit(2)
