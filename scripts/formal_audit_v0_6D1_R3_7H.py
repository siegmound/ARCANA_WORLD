from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r37h_closed_loop_binding import BRANCH_K,R37HClosedLoopConfig
checks=[]
def check(name,cond,detail=None): checks.append({'name':name,'pass':bool(cond),'detail':detail})

cfg=R37HClosedLoopConfig()
check('window_210_150',cfg.start_age_ma==210.0 and cfg.end_age_ma==150.0)
check('steps_480',round((cfg.start_age_ma-cfg.end_age_ma)*1e6/cfg.biology_cadence_years)==480)
check('K_envelope_exact',BRANCH_K=={'K_LOW':37.614,'K_CENTER':38.470,'K_HIGH':41.002})
check('ceiling_unchanged',abs(cfg.variance_ceiling_normalized-0.08)<1e-15)
check('mu_unchanged',abs(cfg.mutation_variance_supply_normalized_per_myr-0.002)<1e-15)
check('b_unchanged',abs(cfg.nonlinear_stabilizing_variance_depletion_per_myr_per_q-0.9876543209876544)<1e-15)
check('biology_cadence_unchanged',abs(cfg.biology_cadence_years-125000.0)<1e-12)
check('transport_cadence_unchanged',abs(cfg.transport_cadence_years-62500.0)<1e-12)

# R3.7G parent is immutable.
parent=json.loads((ROOT/'PACKAGE_MANIFEST_v0_6D1_R3_7G.json').read_text(encoding='utf-8'))
bad=[]
for rec in parent['files']:
    p=ROOT/rec['path']; actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    if actual!=rec['sha256']: bad.append({'path':rec['path'],'expected':rec['sha256'],'actual':actual})
check('parent_r37g_file_count_3370',len(parent['files'])==3370,len(parent['files']))
check('parent_r37g_all_files_unchanged',not bad,bad[:10])

# Full external R3.7G result is embedded and reviewed.
evzip=ROOT/'references/v0_6D1_R3_7G/v0_6D1_R3_7G_FULL_LOCAL_RESULTS.zip'
eva=ROOT/'outputs/v0_6D1_R3_7H/R3_7G_FULL_LOCAL_EVIDENCE_AUDIT.json'
check('r37g_full_zip_present',evzip.exists())
check('r37g_full_audit_present',eva.exists())
if evzip.exists() and eva.exists():
    e=json.loads(eva.read_text(encoding='utf-8'))
    check('r37g_full_zip_hash',hashlib.sha256(evzip.read_bytes()).hexdigest()==e['source_zip_sha256'])
    check('r37g_480_steps',e['biology_steps']==480)
    check('r37g_canonical_parity',e['canonical_parity'] is True)
    check('r37g_legacy_clipping_reproduced',e['legacy']['steps_with_clipping']==331)
    check('r37g_first_clip_191p25',abs(e['legacy']['first_clipping_age_ma']-191.25)<1e-12)
    check('r37g_shadow_zero_contacts',all(v==0 for v in e['shadow']['ceiling_contacts'].values()))
    check('r37g_center_headroom_positive',e['shadow']['center_headroom']>0)
    check('r37g_governed_pass',e['production_validation_gate']['governed_validation_pass'] is True)
    check('r37g_closed_loop_still_required',e['review']['closed_loop_feedback_validation_required'] is True)

sm=ROOT/'outputs/v0_6D1_R3_7H/R3_7H_DIAGNOSTIC_SMOKE_AUDIT.json'
check('r37h_smoke_audit_present',sm.exists())
if sm.exists():
    s=json.loads(sm.read_text(encoding='utf-8'))
    check('smoke_three_branch_valid',s['three_branch_210_209']['all_branches_valid'] is True)
    check('smoke_three_branch_clear',s['three_branch_210_209']['all_branches_clear_of_ceiling'] is True)
    check('lifecycle_smoke_40_steps',s['center_210_205_lifecycle']['biology_steps']==40)
    check('lifecycle_smoke_coalescence',s['center_210_205_lifecycle']['event_counts'].get('deme_coalescence',0)>0)
    check('lifecycle_smoke_fission',s['center_210_205_lifecycle']['event_counts'].get('deme_fission',0)>0)
    check('lifecycle_smoke_zero_clipping',s['center_210_205_lifecycle']['clipping_contacts']==0)
    check('lifecycle_smoke_gate',s['center_210_205_lifecycle']['closed_loop_gate_pass'] is True)

files=[
'src/arcana_worldsim/scientific_engines/r37h_closed_loop_binding.py',
'scripts/run_v0_6D1_R3_7H_closed_loop_validation.py',
'scripts/formal_audit_v0_6D1_R3_7H.py',
'tests/test_r37h_closed_loop_binding.py',
'configs/world1_closed_loop_binding_validation_v0_6D1_R3_7H.json',
'CLOSED_LOOP_SEGREGATION_AWARE_RUNTIME_BINDING_CONTRACT_v0_6D1_R3_7H.md',
'R3_7G_FULL_LOCAL_EVIDENCE_AUDIT.md','R3_7H_DIAGNOSTIC_SMOKE_AUDIT.md',
'README_R3_7H.md','V0_6D1_R3_7H_STATUS.md','NEXT_STAGE_HANDOFF_v0_6D1_R3_7H.md',
'run_v0_6D1_R3_7H_closed_loop_validation.ps1','run_v0_6D1_R3_7H_smoke.ps1','run_v0_6D1_R3_7H_checks.ps1']
for f in files: check('exists_'+f,(ROOT/f).exists())

src=(ROOT/'src/arcana_worldsim/scientific_engines/r37h_closed_loop_binding.py').read_text(encoding='utf-8')
contract=(ROOT/'CLOSED_LOOP_SEGREGATION_AWARE_RUNTIME_BINDING_CONTRACT_v0_6D1_R3_7H.md').read_text(encoding='utf-8')
check('source_returns_repaired_va','return z_new, v_new' in src)
check('source_selection_consumes_canonical_va','orig_select(trait, va' in src)
check('source_mean_legacy_only_closure','mean_authority_closure_max_abs' in src)
check('source_segaware_coalescence','SEGREGATION_AWARE_PERSISTENT_SECONDARY_CONTACT_DEME_COALESCENCE' in src)
check('source_parent_fission_reused','orig_fission(**kwargs)' in src)
check('source_parent_extinction_reused','orig_ext(species_ids, **kwargs)' in src)
check('source_scalar_K_denied','"scalar_K_eff_production_authorized": False' in src)
check('source_runtime_promotion_denied','"production_runtime_replacement_authorized": False' in src)
check('source_mu_b_change_denied','"mu_b_or_ceiling_change_authorized": False' in src)
check('contract_feedback_explicit','repaired within-deme VA is now returned to the runtime' in contract)
check('contract_no_auto_promotion','not yet production authority' in contract)
check('contract_no_fitted_macro_tolerance','No new arbitrary tolerance is fitted' in contract)
check('contract_r_not_world_constant','not promoted to a World-1 constant' in contract)

ok=all(x['pass'] for x in checks)
out={'stage':'v0.6D1-R3.7H','status':'PASS' if ok else 'FAIL','check_count':len(checks),'checks':checks}
od=ROOT/'outputs/v0_6D1_R3_7H'; od.mkdir(parents=True,exist_ok=True)
(od/'FORMAL_AUDIT_v0_6D1_R3_7H.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'status':out['status'],'checks_passed':sum(x['pass'] for x in checks),'check_count':len(checks)},indent=2))
raise SystemExit(0 if ok else 2)
