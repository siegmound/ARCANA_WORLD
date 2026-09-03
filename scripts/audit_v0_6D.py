from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import historical_deep_bridge_v0_6D as h

checks=[]
def ck(name, cond, detail=None):
    ok=bool(cond); checks.append({'name':name,'pass':ok,'detail':detail});
    if not ok: raise AssertionError(name)

ref=ROOT/'references'
d1=json.loads((ref/'D1_species_metadata.json').read_text())
reg=json.loads((ref/'D3_0A_deme_seed_registry.json').read_text())
audit=json.loads((ref/'D3_0A_spatial_bridge_audit.json').read_text())
sumry=json.loads((ref/'HISTORICAL_BRIDGE_REFERENCE_v0_6D.json').read_text())
ids=h.validate_d1_metadata(d1)
proxy={k:v['parent_species_id'] for k,v in sumry['authorized_D2_child_proxy_provenance'].items()}
auth=h.validate_d22_d3_reference(ids,sumry['D22_survivor_species_ids'],reg,audit,authorized_proxy_parent=proxy)
ck('D1_real_identity_count_120',len(ids)==120)
ck('D1_no_Deep_prelabel',all(not bool(x.get('Deep_adapted')) for x in d1))
ck('D22_survivors_exactly_31',auth['survivor_count']==31)
ck('D3_0A_demes_exactly_115',auth['deme_seed_count']==115)
ck('D3_0A_parent_is_D22',auth['parent']=='0.6.3D2.2')
ck('D3_0A_no_Deep_authority',audit['criteria']['no_Deep'] is True)
ck('D3_0A_no_speciation_authority',audit['criteria']['no_speciation'] is True)
ck('HSG025_proxy_explicit',audit['criteria']['HSG025_proxy_provenance_explicit'] is True and proxy.get('HSG_025')=='HSG_003')
ck('D22_to_D3_species_total_conservation_reference',sumry['D3_0A_species_total_max_abs_error_vs_endpoint_raster']<2e-14)
ck('reference_population_not_redefined',h.GOVERNANCE.get('D1_D2_reconstructed_from_summaries') is False)
ck('Deep_direct_survivor_selection_absent',h.GOVERNANCE['Deep_direct_survivor_selection'] is False)
ck('Deep_direct_speciation_absent',h.GOVERNANCE['Deep_direct_speciation'] is False)
ck('energy_reset_boundary_forbidden',h.GOVERNANCE['energy_reset_at_D22_D3_boundary'] is False)
ck('photo_deep_share_5pct',abs(h.GOVERNANCE['photo_deep_additive_share_E_th']-.05)<1e-15)
ck('production_HX_without_runtime_forbidden',h.GOVERNANCE['production_HX_allowed_without_D1_D2_runtime'] is False)

sm=json.loads((ROOT/'outputs'/'REAL_D22_TO_D3_TRANSFER_SMOKE_v0_6D.json').read_text())
ck('real_authority_transfer_smoke_pass',sm['status'].startswith('PASS_'))
ck('real_transfer_latent_mean_exact',sm['max_latent_mean_abs_error']==0)
ck('real_transfer_latent_va_exact',sm['max_latent_va_abs_error']==0)
ck('real_transfer_physiology_exact',sm['max_physiology_abs_error']==0)
ck('real_transfer_energy_exact',sm['max_energy_ledger_transfer_abs_error_j']==0)
ck('real_transfer_not_mislabeled_HX',sm['historical_HX_claimed'] is False)

cp=json.loads((ROOT/'outputs'/'CHA1_PULSE_REFERENCE_AUDIT_v0_6D.json').read_text())
ck('CHA1_15_checkpoints',cp['checkpoint_count']==15)
ck('CHA1_event_time_relative_error_lt_1e9',cp['max_relative_error']<1e-9,cp['max_relative_error'])
ck('CHA1_surface_energy_exact_at_impact',abs(cp['pulse_at_impact_total_j']-1.0857344210806324e16)<=2.0)
ck('CHA1_preimpact_pulse_zero',all(float(x)==0 for x in cp['pulse_before_impact_j']))

# Parent source immutability relative to v0.6C package.
parent=Path('/mnt/data/ARCANA_DEEP_D3_COUPLING_v0_6C_PRODUCTION_RUNTIME_AND_PHYSIOLOGY_CANDIDATE/src')
for fn in ['deep_d3_coupling_v0_6A.py','deep_heritable_selection_v0_6B.py','deep_production_runtime_v0_6C.py']:
    a=hashlib.sha256((ROOT/'src'/fn).read_bytes()).hexdigest(); b=hashlib.sha256((parent/fn).read_bytes()).hexdigest()
    ck('parent_source_unchanged_'+fn,a==b,a)

# Explicit fail-closed production gates.
for args,label in [((False,False,False),'historical_D2_gate'),]:
    try: h.historical_d2_runtime_gate(*args); ok=False
    except RuntimeError: ok=True
    ck(label+'_fails_closed',ok)
try: h.d22_deep_extension_gate(d22_runtime_adapter_present=False,continuous_hazard_hook_present=False); ok=False
except RuntimeError: ok=True
ck('D22_hazard_extension_gate_fails_closed',ok)

result={'status':'PASS_V0_6D_FORMAL_AUDIT','passed':sum(x['pass'] for x in checks),'total':len(checks),'checks':checks,
        'production_historical_HX_authorized':False,
        'remaining_blocker':'MOUNT_AND_BIND_EXECUTABLE_D1_D2_D2_2_HISTORICAL_RUNTIME_AND_D1_210MA_VARIANCE_STATE'}
(ROOT/'outputs'/'FORMAL_AUDIT_v0_6D.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'passed':result['passed'],'total':result['total'],'remaining_blocker':result['remaining_blocker']},indent=2))
