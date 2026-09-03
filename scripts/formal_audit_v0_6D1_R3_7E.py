from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r37e_short_shadow_replay import R37EShortShadowConfig

checks=[]
def check(name,cond,detail=None): checks.append({'name':name,'pass':bool(cond),'detail':detail})

sm=json.loads((ROOT/'outputs/v0_6D1_R3_7E/DIAGNOSTIC_SMOKE_210_209.json').read_text())
check('stage',sm['stage']=='v0.6D1-R3.7E')
check('parent_stage',sm['parent_stage']=='v0.6D1-R3.7D')
check('smoke_210_209',sm['shadow']['window']=={'start_age_ma':210.0,'end_age_ma':209.0,'biology_steps':8})
check('canonical_core_parity',sm['canonical_parity']['all_core_parity'])
for k,v in sm['canonical_parity']['bit_exact_core_arrays'].items(): check('parity_'+k,v)
check('events_exact',sm['canonical_parity']['events_exact'])
check('K_order',sm['shadow']['K_envelope']['K_LOW'] < sm['shadow']['K_envelope']['K_CENTER'] < sm['shadow']['K_envelope']['K_HIGH'])
check('K_low_parent_value',abs(sm['shadow']['K_envelope']['K_LOW']-37.614)<1e-12)
check('K_center_parent_value',abs(sm['shadow']['K_envelope']['K_CENTER']-38.470)<1e-12)
check('K_high_parent_value',abs(sm['shadow']['K_envelope']['K_HIGH']-41.002)<1e-12)
check('no_ceiling_contacts',all(v==0 for v in sm['shadow']['ceiling_contacts_by_variant'].values()))
check('smoke_verdict',sm['verdict'].startswith('PASS_SHORT_WORLD1_ADAPTIVE_GENETIC_SHADOW_REPLAY'))
check('canonical_write_denied',sm['shadow']['governance']['canonical_write_allowed'] is False)
check('runtime_replacement_denied',sm['shadow']['governance']['production_runtime_replacement_authorized'] is False)
check('scalar_K_denied',sm['shadow']['governance']['scalar_K_eff_production_authorized'] is False)
check('worldsim_N_mapping_denied',sm['shadow']['governance']['direct_WorldSim_N_to_NEMO_N_mapping_authorized'] is False)
check('mu_b_ceiling_change_denied',sm['shadow']['governance']['mu_b_or_ceiling_change_authorized'] is False)
check('recombination_not_world1_constant',sm['shadow']['governance']['recombination_fraction_is_reference_shadow_architecture_not_world1_constant'] is True)

cfg=R37EShortShadowConfig()
check('full_window_210_205',cfg.start_age_ma==210.0 and cfg.end_age_ma==205.0)
check('full_step_count',round((cfg.start_age_ma-cfg.end_age_ma)*1e6/cfg.biology_cadence_years)==40)
check('ceiling_unchanged',abs(cfg.variance_ceiling_normalized-0.08)<1e-15)
check('biology_cadence_unchanged',abs(cfg.biology_cadence_years-125000.0)<1e-12)
check('transport_cadence_unchanged',abs(cfg.transport_cadence_years-62500.0)<1e-12)

# Parent R3.7D source authority entries must still match.
parent=json.loads((ROOT/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_7D.json').read_text())
for rec in parent.get('new_r3_7D_sources',[]):
    p=ROOT/rec['path']; h=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    check('parent_r37d_'+rec['path'],h==rec['sha256'],{'expected':rec['sha256'],'actual':h})

for doc in [
 'SHORT_WORLD1_ADAPTIVE_GENETIC_SHADOW_REPLAY_CONTRACT_v0_6D1_R3_7E.md',
 'README_R3_7E.md','V0_6D1_R3_7E_STATUS.md','NEXT_STAGE_HANDOFF_v0_6D1_R3_7E.md',
 'configs/world1_short_adaptive_genetic_shadow_replay_v0_6D1_R3_7E.json',
 'scripts/run_v0_6D1_R3_7E_short_shadow.py','run_v0_6D1_R3_7E_short_shadow.ps1','run_v0_6D1_R3_7E_smoke.ps1',
]: check('exists_'+doc,(ROOT/doc).exists())

ok=all(x['pass'] for x in checks)
out={'stage':'v0.6D1-R3.7E','status':'PASS' if ok else 'FAIL','check_count':len(checks),'checks':checks}
od=ROOT/'outputs/v0_6D1_R3_7E'; od.mkdir(parents=True,exist_ok=True)
(od/'FORMAL_AUDIT_v0_6D1_R3_7E.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'status':out['status'],'checks_passed':sum(x['pass'] for x in checks),'check_count':len(checks)},indent=2))
raise SystemExit(0 if ok else 2)
