from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r37i_production_runtime import NOMINAL_K_REFERENCE,R37IProductionConfig
checks=[]
def check(name,cond,detail=None): checks.append({'name':name,'pass':bool(cond),'detail':detail})

cfg=R37IProductionConfig()
check('window_210_150',cfg.start_age_ma==210.0 and cfg.end_age_ma==150.0)
check('nominal_K_center_exact',abs(NOMINAL_K_REFERENCE-38.470)<1e-12)

# Parent R3.7H immutable.
parent=json.loads((ROOT/'PACKAGE_MANIFEST_v0_6D1_R3_7H.json').read_text(encoding='utf-8'))
bad=[]
for rec in parent['files']:
    p=ROOT/rec['path']; actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    if actual!=rec['sha256']: bad.append({'path':rec['path'],'expected':rec['sha256'],'actual':actual})
check('parent_r37h_file_count_3405',len(parent['files'])==3405,len(parent['files']))
check('parent_r37h_all_files_unchanged',not bad,bad[:10])

required=[
'src/arcana_worldsim/scientific_engines/r37i_production_runtime.py',
'scripts/review_and_seal_v0_6D1_R3_7I.py','scripts/run_v0_6D1_R3_7I_canonical_runtime.py',
'scripts/formal_audit_v0_6D1_R3_7I.py','tests/test_r37i_production_promotion.py',
'configs/world1_production_promotion_v0_6D1_R3_7I.json',
'PRODUCTION_PROMOTION_SEAL_CONTRACT_v0_6D1_R3_7I.md','README_R3_7I.md','V0_6D1_R3_7I_STATUS.md',
'NEXT_STAGE_HANDOFF_v0_6D1_R3_7I.md','run_v0_6D1_R3_7I_promotion_review.ps1',
'run_v0_6D1_R3_7I_canonical_runtime.ps1','run_v0_6D1_R3_7I_checks.ps1']
for f in required: check('exists_'+f,(ROOT/f).exists())

src=(ROOT/'src/arcana_worldsim/scientific_engines/r37i_production_runtime.py').read_text(encoding='utf-8')
review=(ROOT/'scripts/review_and_seal_v0_6D1_R3_7I.py').read_text(encoding='utf-8')
contract=(ROOT/'PRODUCTION_PROMOTION_SEAL_CONTRACT_v0_6D1_R3_7I.md').read_text(encoding='utf-8')
check('runtime_requires_seal','validate_promotion_seal' in src and 'promotion seal is missing' in src)
check('runtime_uses_center_only','NOMINAL_K_LABEL = "K_CENTER"' in src)
check('physical_scalar_K_denied','scalar_k_physical_constant_authorized' in src and 'False' in src)
check('mu_b_change_denied','mu_b_or_ceiling_change_authorized' in src and 'False' in src)
check('review_requires_three_branches','BRANCHES = ("K_LOW", "K_CENTER", "K_HIGH")' in review)
check('review_requires_480','EXPECTED_STEPS = 480' in review)
check('review_requires_zero_clipping','zero_clipping' in review)
check('review_requires_explicit_approval','--approve-promotion' in review)
check('contract_no_auto_promotion','cannot self-promote from smoke evidence' in contract)
check('contract_retains_sentinels','remain release-validation uncertainty sentinels' in contract)
check('contract_retires_legacy_only_as_variance_authority','retired as **production variance authority**' in contract)

# Current candidate must fail closed because full H evidence is intentionally absent.
seal=ROOT/'outputs/v0_6D1_R3_7I/PRODUCTION_PROMOTION_SEAL_v0_6D1_R3_7I.json'
check('no_prebaked_promotion_seal',not seal.exists(),str(seal))

ok=all(x['pass'] for x in checks)
out={'stage':'v0.6D1-R3.7I','status':'PASS' if ok else 'FAIL','check_count':len(checks),'checks':checks,
     'candidate_state':'PROMOTION_IMPLEMENTED_FAIL_CLOSED_R37H_FULL_EVIDENCE_PENDING'}
od=ROOT/'outputs/v0_6D1_R3_7I'; od.mkdir(parents=True,exist_ok=True)
(od/'FORMAL_AUDIT_v0_6D1_R3_7I.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'status':out['status'],'checks_passed':sum(x['pass'] for x in checks),'check_count':len(checks),
                  'candidate_state':out['candidate_state']},indent=2))
raise SystemExit(0 if ok else 2)
