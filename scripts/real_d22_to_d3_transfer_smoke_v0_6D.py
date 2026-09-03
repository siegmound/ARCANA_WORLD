from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from historical_deep_bridge_v0_6D import (
    HistoricalLineageSidecar, HistoricalEnergyState, validate_d1_metadata,
    filter_to_authoritative_survivors, expand_survivors_to_d3_demes,
    verify_species_to_deme_moment_identity, validate_d22_d3_reference,
)

ref=ROOT/'references'
d1=json.loads((ref/'D1_species_metadata.json').read_text())
reg=json.loads((ref/'D3_0A_deme_seed_registry.json').read_text())
audit=json.loads((ref/'D3_0A_spatial_bridge_audit.json').read_text())
sumry=json.loads((ref/'HISTORICAL_BRIDGE_REFERENCE_v0_6D.json').read_text())
cal=json.loads((ref/'WORLD1_DEEP_FREE_ENERGY_CALIBRATION_v0_5.json').read_text())
ids=validate_d1_metadata(d1)

# Structural identity probe only: unique deterministic moments prove exact routing.
# They are NOT claimed to be the historical D1/D2 Deep state.
n=len(ids); z=np.arange(n*10,dtype=float).reshape(n,10)*1e-7
va=np.full((n,10),0.0123456789)
base=HistoricalLineageSidecar(ids,z,va,np.linspace(0,.1,n),np.linspace(0,.05,n),np.linspace(0,.2,n),np.linspace(0,.01,n),provenance=['STRUCTURAL_PROBE_NOT_HX']*n)
proxy={k:v['parent_species_id'] for k,v in sumry['authorized_D2_child_proxy_provenance'].items()}
auth=validate_d22_d3_reference(ids,sumry['D22_survivor_species_ids'],reg,audit,authorized_proxy_parent=proxy)
surv=filter_to_authoritative_survivors(base,sumry['D22_survivor_species_ids'],authorized_proxy_parent=proxy)

# Real v0.5 global 210-Ma reservoir partition is represented as a 1x1 physical
# ledger for a boundary-transfer invariance test. No spatial claim is made.
modes=['E','th','p','I','N']; init=cal['initial_210Ma_background_partition']
bg=np.asarray([init['mode_surface_background_j'][m] for m in modes],float)[:,None,None]
buf=np.asarray([init['mode_deep_buffer_j'][m] for m in modes],float)[:,None,None]
photo=np.zeros_like(bg); photo[:2]=0.05*bg[:2]
energy=HistoricalEnergyState(bg.copy(),bg.copy(),photo.copy(),photo.copy(),buf.copy(),np.zeros(5),np.zeros(5),np.zeros(5),np.zeros(5))
d3=expand_survivors_to_d3_demes(surv,energy,reg,endpoint_relative_year=500000.0)
diag=verify_species_to_deme_moment_identity(surv,d3,reg)

energy_error=max(
 float(np.max(np.abs(d3.surface_background_energy_j-energy.surface_background_energy_j))),
 float(np.max(np.abs(d3.photo_energy_j-energy.photo_energy_j))),
 float(np.max(np.abs(d3.source_buffer_j-energy.source_buffer_j))),
)
hsg_i=surv.species_ids.index('HSG_025')
report={
 'status':'PASS_REAL_AUTHORITY_D22_TO_D3_STRUCTURAL_TRANSFER_SMOKE_NOT_HISTORICAL_HX',
 'authority':auth,
 'D22_survivor_count':len(surv.species_ids),
 'D3_deme_seed_count':len(d3.deme_ids),
 'D22_parent_population_66ma_total':sumry['D22_parent_population_66ma_total'],
 'D3_0A_endpoint_population_500kyr_total':sumry['D3_0A_endpoint_population_500kyr_total'],
 'D3_0A_species_total_max_abs_error_vs_endpoint_raster':sumry['D3_0A_species_total_max_abs_error_vs_endpoint_raster'],
 **diag,
 'max_energy_ledger_transfer_abs_error_j':energy_error,
 'HSG_025_deep_provenance':surv.provenance[hsg_i],
 'historical_HX_claimed':False,
 'reason_not_HX':'actual D1/D2 historical Deep sidecar/runtime is not mounted; HSG_025 uses explicit structural parent proxy only',
}
assert diag['max_latent_mean_abs_error']==0 and diag['max_latent_va_abs_error']==0 and diag['max_physiology_abs_error']==0
assert energy_error==0
out=ROOT/'outputs'/'REAL_D22_TO_D3_TRANSFER_SMOKE_v0_6D.json'; out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
