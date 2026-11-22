"""R6 provider-pilot guard tests: portable, no scientific engine mocked as evidence."""
from __future__ import annotations
import copy
import json
import os
import subprocess
from pathlib import Path
import pytest

from experiments.r6_thermo_provider_pilot_v1 import pilot as p
from experiments.r6_thermo_provider_pilot_v1 import run_perplex_official as per

@pytest.fixture
def registry():
    return p.pins()


def bad(fn, name):
    with pytest.raises(p.PilotError,match=name):fn()


def test_source_pins_and_schema_valid(registry):
    assert p.validate_registry(registry)
    assert p.blob(b'abc')=='f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f'  # git hash-object abc

@pytest.mark.parametrize('field,val',[('epoch','NATURAL_ARCANA_T0'),('physical_T1',{}),('D_024','CLOSED'),('mechanical_solve_authorized',True),('WORLD_HISTORY_PRODUCTION_AUTHORIZED',True),('HistoryStore_modified',True),('original_rock_phase_assignments',1),('source_8x8_physical_rock_selection','granite'),('cross_provider_equivalence_qualified',True),('cross_provider_scientific_comparison_authorized',True)])
def test_governance_fail_closed(registry,field,val):
    x=copy.deepcopy(registry);x[field]=val
    bad(lambda:p.validate_registry(x),'PILOT_AUTHORITY')

@pytest.mark.parametrize('key', ['MAGEMin_C.jl','Perple_X'])
def test_sha_pin_drift(registry,key):
    x=copy.deepcopy(registry);x['providers'][key]['commit_sha']='0'*40
    bad(lambda:p.validate_registry(x),'PILOT_UPSTREAM_PIN_DRIFT')

@pytest.mark.parametrize('field,val',[('oxide_basis','NORMALIZED_WT'),('as_reported_sum_wt_percent',100.),('pressure_kbar',11.),('temperature_c',900.)])
def test_fixture_drift(registry,field,val):
    x=copy.deepcopy(registry);x['fixtures']['MAGEMIN_CUSTOM_IG'][field]=val
    bad(lambda:p.validate_registry(x),'PILOT_')


def test_cannot_forge_cross_solver_equivalence(registry):
    x=copy.deepcopy(registry)
    x['fixtures']['MAGEMIN_CUSTOM_IG']['not_eligible_for_direct_cross_solver_comparison']=False
    bad(lambda:p.validate_registry(x),'PILOT_FAKE_COMPARABILITY')


def test_no_renormalize_official_oxides(registry):
    amounts=registry['fixtures']['MAGEMIN_CUSTOM_IG']['amounts_wt_percent']
    assert len(amounts)==11 and sum(amounts)==pytest.approx(99.75)
    assert 'FeO' in registry['fixtures']['MAGEMIN_CUSTOM_IG']['oxides']
    assert 'Fe2O3' in registry['fixtures']['MAGEMIN_CUSTOM_IG']['oxides']
    assert 'H2O' in registry['fixtures']['MAGEMIN_CUSTOM_IG']['oxides']


def test_official_PT_units_are_distinct(registry):
    x=registry['fixtures']
    assert x['MAGEMIN_PREDEFINED_KLB1']['pressure_kbar']==8
    assert x['PERPLEX_BL691_MEEMUM']['pressure_bar']==4000
    assert x['PERPLEX_BL691_MEEMUM']['temperature_k']==1050
    assert x['MAGEMIN_CUSTOM_IG']['temperature_c']==1100


def valid_mag():
    return {'provider':'MAGEMin_C.jl','version':'2.4.5','fixtures':{
        name: {'status':0,'P_kbar':v['pressure_kbar'],'T_C':v['temperature_c'],
               'rho_kg_m3':2900.,'phases':['ol','opx'],'phase_mass_fractions':[.6,.4]}
        for name,v in p.pins()['fixtures'].items() if v['provider']=='MAGEMin_C.jl'}}


def test_valid_magemin_result_metadata():
    assert p.validate_magemin_result(valid_mag())

@pytest.mark.parametrize('field,val',[('status',1),('rho_kg_m3',0),('phases',[]),('phase_mass_fractions',[.3,.3]),('P_kbar',999),('T_C',-100.)])
def test_bad_magemin_output_rejected(field,val):
    r=valid_mag();r['fixtures']['MAGEMIN_CUSTOM_IG'][field]=val
    bad(lambda:p.validate_magemin_result(r),'PILOT_MAGEMIN')


def test_magemin_toml_parsed(tmp_path):
    toml='provider = "MAGEMin_C.jl"\nversion="2.4.5"\n'
    for name,v in p.pins()['fixtures'].items():
        if v['provider']=='MAGEMin_C.jl':
            toml+=f'\n[fixtures.{name}]\nstatus=0\nP_kbar={v["pressure_kbar"]}\nT_C={v["temperature_c"]}\nrho_kg_m3=3000.0\nphases=["q","bi"]\nphase_mass_fractions=[0.45,0.55]\n'
    path=tmp_path/'mag.toml';path.write_text(toml)
    assert p.load_magemin_toml(path)['version']=='2.4.5'


def test_official_perplex_synthetic_prn_parser(tmp_path):
    path=tmp_path/'fixture.prn'
    path.write_text('Stable phases at:\n  T(K) = 1050.00\n  P(bar) = 4000.00\n'
     'Phase Compositions (molar  proportions):\n    wt %  vol %  mol %  mol\n'
     '  q 70.0 30.0 10.0 3.0\n  Fsp(C1) 30.0 70.0 90.0 7.0\n\nPhase speciation\n')
    x=p.parse_perplex_meemum(path)
    assert x['pressure_bar']==4000 and sum(x['phases_wt_percent'].values())==100
    path.write_text(path.read_text().replace('4000.00','5000.00'))
    bad(lambda:p.parse_perplex_meemum(path),'PILOT_PERPLEX_OFFICIAL_P_T_CHANGED')


def test_cross_solver_missing_data_cannot_compare():
    bad(lambda:p.comparable_pair({},{}),'PILOT_CROSS_TOOL_INCOMPARABLE')


def test_cross_solver_perfectly_equivalent_contract_only():
    x={k:'v' for k in ('oxide_basis','water_state','oxygen_redox_state',
        'thermodynamic_model_crosswalk','phase_name_crosswalk','chemical_reference_system')}
    x.update(oxide_moles={'SiO2':1.},pressure_pa=1e9,temperature_k=1100.)
    assert p.comparable_pair(x,x)
    y=copy.deepcopy(x);y['oxide_moles']={'SiO2':2.}
    bad(lambda:p.comparable_pair(x,y),'PILOT_CROSS_TOOL_INPUT_MISMATCH')
    y=copy.deepcopy(x);y['pressure_pa']=1e8
    bad(lambda:p.comparable_pair(x,y),'PILOT_CROSS_TOOL_INPUT_MISMATCH')


def test_preflight_always_pending_not_tool_execution():
    x=p.preflight()
    assert x['official_engine_executions']==0
    assert x['scientific_cross_provider_comparison_authorized'] is False
    assert x['physical_T1'] is None


def test_write_once_and_no_authorization(tmp_path):
    f=tmp_path/'r.json'
    report=p.preflight()
    sha=p.write_once(f,report)
    assert sha==p.digest(f)
    bad(lambda:p.write_once(f,report),'PILOT_OUTPUT_EXISTS')
    report['physical_T1']={'T':800}
    bad(lambda:p.write_once(tmp_path/'b.json',report),'PILOT_UNAUTHORIZED_OUTPUT')


def test_perplex_missing_executable_rejected(tmp_path,monkeypatch):
    # Synthetic harness only. Never claim that mocked Perple_X ran.
    source=tmp_path/'fixture'
    source.mkdir()
    monkeypatch.setattr(per,'verify_perplex_source',lambda p:source)
    bad(lambda:per.run(tmp_path/'repo',source,tmp_path/'absent',tmp_path/'new',
                       release_archive=tmp_path/'archive'),
        'PILOT_PERPLEX_RELEASE_ARCHIVE_SHA_MISMATCH')


def test_versioned_perplex_fixture_path():
    assert p.pins()['providers']['Perple_X']['official_fast_fixture']=='test/bl691_MEEMUM'
    assert p.pins()['providers']['Perple_X']['official_expected_report_git_blob_sha'].startswith('27f357')
