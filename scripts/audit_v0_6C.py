from pathlib import Path
import json, sys
P=Path(__file__).resolve().parents[1]
checks=[]
def check(name, cond, detail=''):
    checks.append({'name':name,'pass':bool(cond),'detail':detail})

def load(rel): return json.loads((P/rel).read_text())

src=(P/'src/deep_production_runtime_v0_6C.py').read_text()
contract=(P/'DEEP_PRODUCTION_RUNTIME_CONTRACT_v0_6C.md').read_text()
status=(P/'V0_6C_STATUS.md').read_text()
par=load('outputs/PRODUCTION_DEEP_OFF_PARITY_v0_6C.json')
sm=load('outputs/REAL_WORLD_DEEP_ON_25K_SMOKE_v0_6C.json')
ck=load('outputs/DEEP_ON_CHECKPOINT_RESUME_v0_6C.json')
fi=load('outputs/REAL_D3_FISSION_INHERITANCE_v0_6C.json')
cfg=load('configs/world1_deep_production_runtime_v0_6C.json')

check('D3 source modification forbidden', "'D3_source_modified':False" in src)
check('direct Deep speciation absent', "'direct_Deep_speciation_operator':False" in src)
check('Deep RI insertion absent', "'Deep_latent_traits_inserted_into_D3_RI':False" in src)
check('directional mutation absent', "'directional_mutation_operator':False" in src)
check('photo Deep fixed to additive 5 percent E/th', abs(cfg['runtime']['photo_deep_additive_share_E_th']-.05)<1e-15 and cfg['runtime']['photo_deep_zero_modes']==['p','I','N'])
check('geological and stellar reservoirs separate', 'surface_background_energy_j' in src and 'photo_energy_j' in src and 'cumulative_stellar_pump_j' in src)
check('finite geological source buffer present', 'source_buffer_j' in src and 'finite_source_buffer_j=state.source_buffer_j' in src)
check('physiology macrostep analytic fixed point present', 'physiology_macrostep' in src and '_frozen_exact_physiology' in src and 'FAIL_CLOSED' in src)
check('checkpoint source fingerprint fail closed', 'Deep checkpoint source fingerprint mismatch: FAIL_CLOSED' in src)
check('historical proxy forbidden', "'historical_210Ma_proxy_allowed':False" in src and 'true 210 Ma D3 checkpoint: FAIL_CLOSED' in src)
check('Deep OFF production parity PASS', par.get('status')=='PASS_DEEP_OFF_PRODUCTION_WRAPPER_PARITY' and all(par['field_bit_exact'].values()) and par['species_ids_exact'] and par['deme_ids_exact'])
check('Deep OFF event parity PASS', par['speciation_events_exact'] and par['fission_events_exact'])
check('real Deep ON 25 kyr smoke PASS', sm.get('status')=='PASS_REAL_WORLD_DEEP_ON_25K_RUNTIME_SMOKE' and sm.get('D3_source_modified') is False and sm.get('historical_HX') is False)
check('real energy closure sub-joule', float(sm['diag']['energy_closure_max_abs_j']) < 1.0, str(sm['diag']['energy_closure_max_abs_j']))
check('gene-flow first moment closure', float(sm['diag']['gene_flow_first_moment_closure']) < 1e-12)
check('gene-flow second moment closure', float(sm['diag']['gene_flow_second_moment_closure']) < 1e-10)
check('Deep ON checkpoint resume bit exact', ck.get('status')=='PASS_DEEP_ON_CHECKPOINT_RESUME_BIT_EXACT' and all(ck['d3_field_bit_exact'].values()) and all(ck['deep_field_bit_exact'].values()))
check('real D3 fission inheritance PASS', fi.get('status')=='PASS_REAL_D3_FISSION_SIDECAR_INHERITANCE' and fi['new_fission_count']==1 and fi['sidecar_ids_match_d3'])
check('fission is not speciation', fi['new_fission_events'][0].get('semantic_status')=='PERSISTENT_VICARIANCE_DEMOGRAPHIC_FRAGMENT_NOT_SPECIES')
check('historical D1-D2 bridge explicitly pending', 'D1 + Deep → D2 + Deep → D2.2 CHA-1 + Deep' in status and 'FULL_210_TO_0_MA_HX_AUTHORIZED = false' in status)
check('contract keeps reference_population nonphysical', 'reference_population' in contract and 'not K and not physical N' in contract)
check('no active spellcasting in runtime scope', 'spell' not in src.lower())

out={'stage':'v0.6C','status':'PASS_FORMAL_AUDIT_v0_6C' if all(c['pass'] for c in checks) else 'FAIL_FORMAL_AUDIT_v0_6C','passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks}
(P/'outputs/FORMAL_AUDIT_v0_6C.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
sys.exit(0 if out['status'].startswith('PASS') else 1)
