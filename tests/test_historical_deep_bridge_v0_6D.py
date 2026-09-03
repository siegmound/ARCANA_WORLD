import json
from pathlib import Path
import numpy as np
import pytest

from historical_deep_bridge_v0_6D import (
    HistoricalLineageSidecar, HistoricalEnergyState, validate_d1_metadata,
    initialize_historical_sidecar, filter_to_authoritative_survivors,
    expand_survivors_to_d3_demes, verify_species_to_deme_moment_identity,
    historical_d2_runtime_gate, validate_d22_d3_reference,
)

ROOT=Path(__file__).resolve().parents[1]
REF=ROOT/'references'

def refs():
    d1=json.loads((REF/'D1_species_metadata.json').read_text())
    reg=json.loads((REF/'D3_0A_deme_seed_registry.json').read_text())
    audit=json.loads((REF/'D3_0A_spatial_bridge_audit.json').read_text())
    summary=json.loads((REF/'HISTORICAL_BRIDGE_REFERENCE_v0_6D.json').read_text())
    return d1,reg,audit,summary

def energy():
    sh=(5,2,3)
    arr=np.arange(np.prod(sh),dtype=float).reshape(sh)+1.0
    return HistoricalEnergyState(arr.copy(),arr.copy()+10,arr.copy()+20,arr.copy()+30,arr.copy()+40,
                                 np.arange(5,dtype=float)+1,np.arange(5,dtype=float)+2,
                                 np.arange(5,dtype=float)+3,np.arange(5,dtype=float)+4)

def full_sidecar(ids):
    n=len(ids); z=np.arange(n*10,dtype=float).reshape(n,10)/1000.0
    va=np.full((n,10),0.02)
    return HistoricalLineageSidecar(list(ids),z,va,np.linspace(0,0.2,n),np.linspace(0,0.1,n),np.linspace(0,0.3,n),np.linspace(0,0.05,n))

def test_real_d1_identity_binding_120_and_no_prelabelled_deep():
    d1,_,_,_=refs(); ids=validate_d1_metadata(d1)
    assert len(ids)==120 and len(set(ids))==120
    assert all(not x['Deep_adapted'] for x in d1)

def test_initialization_requires_grounded_d1_variance():
    d1,_,_,_=refs(); ids=validate_d1_metadata(d1)
    with pytest.raises(RuntimeError,match='requires real/derived D1 Deep VA'):
        initialize_historical_sidecar(ids,np.zeros((120,9)))

def test_initialization_zero_mean_nonzero_va_when_supplied():
    d1,_,_,_=refs(); ids=validate_d1_metadata(d1)
    va=np.full((120,10),0.0125); st=initialize_historical_sidecar(ids,va)
    assert np.array_equal(st.latent_mean,np.zeros((120,10)))
    assert np.array_equal(st.latent_va,va)

def test_real_d22_to_d3_reference_authority_boundary():
    d1,reg,audit,s=refs(); ids=validate_d1_metadata(d1)
    proxy={k:v['parent_species_id'] for k,v in s['authorized_D2_child_proxy_provenance'].items()}; out=validate_d22_d3_reference(ids,s['D22_survivor_species_ids'],reg,audit,authorized_proxy_parent=proxy)
    assert out=={'D1_species_count':120,'survivor_count':31,'deme_seed_count':115,'proxy_survivor_count':1,'parent':'0.6.3D2.2','authority_preserved':True}

def test_survivor_filter_is_exact_copy_and_ordered_by_d22():
    d1,_,_,s=refs(); ids=validate_d1_metadata(d1); st=full_sidecar(ids)
    proxy={k:v['parent_species_id'] for k,v in s['authorized_D2_child_proxy_provenance'].items()}; surv=filter_to_authoritative_survivors(st,s['D22_survivor_species_ids'],authorized_proxy_parent=proxy)
    assert surv.species_ids==s['D22_survivor_species_ids']
    old={sid:i for i,sid in enumerate(ids)}
    proxy={k:v['parent_species_id'] for k,v in s['authorized_D2_child_proxy_provenance'].items()}
    for j,sid in enumerate(surv.species_ids):
        src=sid if sid in old else proxy[sid]; i=old[src]
        assert np.array_equal(surv.latent_mean[j],st.latent_mean[i])
        assert np.array_equal(surv.latent_va[j],st.latent_va[i])
    j=surv.species_ids.index('HSG_025')
    assert 'STRUCTURAL_PARENT_PROXY_HSG_003' in surv.provenance[j]

def test_survivor_filter_cannot_add_named_winner():
    d1,_,_,s=refs(); ids=validate_d1_metadata(d1); st=full_sidecar(ids)
    with pytest.raises(RuntimeError,match='missing from historical sidecar'):
        filter_to_authoritative_survivors(st,list(s['D22_survivor_species_ids'])+['DRAGON_001'],authorized_proxy_parent={k:v['parent_species_id'] for k,v in s['authorized_D2_child_proxy_provenance'].items()})

def test_real_31_species_expand_to_115_authorized_d3_demes_exactly():
    d1,reg,_,s=refs(); ids=validate_d1_metadata(d1); st=full_sidecar(ids)
    proxy={k:v['parent_species_id'] for k,v in s['authorized_D2_child_proxy_provenance'].items()}; surv=filter_to_authoritative_survivors(st,s['D22_survivor_species_ids'],authorized_proxy_parent=proxy); en=energy()
    d3=expand_survivors_to_d3_demes(surv,en,reg,endpoint_relative_year=500000.0)
    assert len(d3.deme_ids)==115
    diag=verify_species_to_deme_moment_identity(surv,d3,reg)
    assert diag['max_latent_mean_abs_error']==0.0
    assert diag['max_latent_va_abs_error']==0.0
    assert diag['max_physiology_abs_error']==0.0

def test_energy_ledger_is_not_reset_or_scaled_across_d22_to_d3_boundary():
    d1,reg,_,s=refs(); ids=validate_d1_metadata(d1); proxy={k:v['parent_species_id'] for k,v in s['authorized_D2_child_proxy_provenance'].items()}; surv=filter_to_authoritative_survivors(full_sidecar(ids),s['D22_survivor_species_ids'],authorized_proxy_parent=proxy); en=energy()
    d3=expand_survivors_to_d3_demes(surv,en,reg,endpoint_relative_year=500000.0)
    assert np.array_equal(d3.surface_background_energy_j,en.surface_background_energy_j)
    assert np.array_equal(d3.photo_energy_j,en.photo_energy_j)
    assert np.array_equal(d3.source_buffer_j,en.source_buffer_j)
    assert np.array_equal(d3.cumulative_net_sink_j,en.cumulative_net_sink_j)
    assert np.array_equal(d3.cumulative_stellar_pump_j,en.cumulative_stellar_pump_j)

def test_unknown_or_nonderived_d3_seed_fails_closed():
    d1,reg,_,s=refs(); ids=validate_d1_metadata(d1); proxy={k:v['parent_species_id'] for k,v in s['authorized_D2_child_proxy_provenance'].items()}; surv=filter_to_authoritative_survivors(full_sidecar(ids),s['D22_survivor_species_ids'],authorized_proxy_parent=proxy); en=energy()
    bad=json.loads(json.dumps(reg)); bad['demes'][0]['semantic_status']='SPECIES'
    with pytest.raises(RuntimeError,match='seed semantics'):
        expand_survivors_to_d3_demes(surv,en,bad,endpoint_relative_year=500000.0)

def test_production_hx_gate_fails_without_archived_d1_d2_runtime():
    with pytest.raises(RuntimeError,match='D2_RUNTIME_PACKAGE'):
        historical_d2_runtime_gate(False,False,False)
    historical_d2_runtime_gate(True,True,True)

def test_real_reference_totals_are_expected():
    _,reg,audit,s=refs()
    assert s['D22_parent_population_66ma_total']==pytest.approx(386.41912841796875,rel=0,abs=1e-8)
    assert s['D3_0A_endpoint_population_500kyr_total']==pytest.approx(1616.4896997213361,rel=0,abs=1e-10)
    assert s['D3_0A_species_total_max_abs_error_vs_endpoint_raster']<=2e-14
    assert audit['criteria']['parent_is_D2_2'] is True
    assert audit['criteria']['no_Deep'] is True

from historical_deep_bridge_v0_6D import (
    historical_passive_pressure, reconcile_d2_authorized_lineages,
    historical_selection_variance_step, cha1_surface_pulse_energy_by_mode,
    validate_cha1_reference_against_v05, d22_deep_extension_gate,
)

def test_d1_d2_passive_pressure_is_unit_scale_invariant_and_zero_population_zero_pressure():
    ids=['A','B']; st=full_sidecar(ids); st.latent_mean[:]=0
    pop=np.zeros((2,2,2)); pop[0,0,0]=2; pop[1,1,1]=3
    ref=np.ones((2,2,2)); guild=np.asarray([1,2])
    a=historical_passive_pressure(pop,ref,guild,st)
    b=historical_passive_pressure(pop*17,ref*17,guild,st)
    assert np.allclose(a['mode_site_saturation'],b['mode_site_saturation'],rtol=0,atol=2e-16)
    z=historical_passive_pressure(np.zeros_like(pop),ref,guild,st)
    assert np.array_equal(z['mode_site_saturation'],np.zeros((5,2,2)))
    assert str(a['reference_population_semantics'])=='NORMALIZATION_ANCHOR_NOT_K_NOT_PHYSICAL_N'

def test_d2_authorized_hsg003_to_hsg025_inherits_exact_deep_state():
    st=full_sidecar(['HSG_003','HSG_004'])
    current=['HSG_003','HSG_004','HSG_025']
    ev=[{'event_type':'SPECIATION_BRANCH','parent_species_id':'HSG_003','daughter_species_id':'HSG_025'}]
    out=reconcile_d2_authorized_lineages(st,current,ev)
    i=out.species_ids.index('HSG_025'); p=out.species_ids.index('HSG_003')
    assert np.array_equal(out.latent_mean[i],out.latent_mean[p])
    assert np.array_equal(out.latent_va[i],out.latent_va[p])
    assert out.provenance[i]=='D2_AUTHORIZED_INHERITANCE_HSG_003_TO_HSG_025'

def test_unknown_d2_birth_fails_closed():
    st=full_sidecar(['A'])
    with pytest.raises(RuntimeError,match='unknown D2 lineage birth'):
        reconcile_d2_authorized_lineages(st,['A','B'],[])

def test_historical_selection_requires_explicit_life_history_and_mutation_has_zero_mean():
    cfg=json.loads((REF/'deep_biological_coupling_v0_4.json').read_text())
    st=full_sidecar(['A','B']); st.latent_mean[:]=0; st.latent_va[:]=0.012
    pop=np.zeros((2,2,2)); pop[0,0,0]=2; pop[1,1,1]=3
    opp=np.full((5,2,2),1e-3)
    with pytest.raises(RuntimeError,match='explicit generation time'):
        historical_selection_variance_step(st,pop,opp,cfg,dt_years=1000,generation_time_years=np.ones(1),relative_reproduction_rate=np.ones(2))
    out,diag=historical_selection_variance_step(st,pop,opp,cfg,dt_years=1000,generation_time_years=np.asarray([4.,5.]),relative_reproduction_rate=np.asarray([1.,1.]))
    assert diag['mutation_mean_shift']==0.0
    assert out.latent_va.shape==(2,10)

def test_cha1_analytic_pulse_matches_known_v05_checkpoint_values():
    y=np.asarray([0.,1.,10.,30.])
    # exact v0.5 materialized ledger values from CHA1_HIGH_RES_EXPOSURE_STATS_v0_5.json
    ref=np.asarray([
      [5428672105403162.0,2171468842161264.8,2171468842161264.8,760014094756442.8,325720326324189.7],
      [5264915194110093.0,2105966077644037.2,2105966077644037.2,737088127175413.0,315894911646605.56],
      [4012705130738114.5,1605082052295245.8,1605082052295245.8,561778718303336.06,240762307844286.88],
      [2270971928006753.0,908388771202701.2,908388771202701.2,317936069920945.5,136258315680405.17],
    ])
    d=validate_cha1_reference_against_v05(y,ref)
    assert d['checkpoint_count']==4 and d['max_relative_error']<1e-9
    assert np.array_equal(cha1_surface_pulse_energy_by_mode(-1.0),np.zeros(5))

def test_d22_deep_extension_cannot_be_implemented_from_survivor_summary_only():
    with pytest.raises(RuntimeError,match='D2_2_RUNTIME_ADAPTER'):
        d22_deep_extension_gate(d22_runtime_adapter_present=False,continuous_hazard_hook_present=False)
    d22_deep_extension_gate(d22_runtime_adapter_present=True,continuous_hazard_hook_present=True)
