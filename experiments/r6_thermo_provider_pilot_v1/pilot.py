"""ARCANA R6 thermodynamic external-provider validation (no physical T0).

This pilot checks provider refs and official examples, not solver superiority.
Never infer Earth-to-Arcana mineral identity or compare inequivalent systems.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import tempfile
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIN = HERE / 'pilot.json'
STATUS = 'EARTH_UPSTREAM_PROVIDER_OFFICIAL_FIXTURES_ONLY__NO_T0_PHASE_SELECTION'
CASE_IDS = ('MAGEMIN_PREDEFINED_KLB1', 'MAGEMIN_CUSTOM_IG', 'PERPLEX_BL691_MEEMUM')

class PilotError(ValueError):
    pass


def need(test, code):
    if not test:
        raise PilotError(code)


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def source_git_blob(p):
    return blob(Path(p).read_bytes())


def pins():
    x=json.loads(PIN.read_text())
    validate_registry(x)
    return x


def validate_registry(x):
    need(type(x) is dict and x.get('schema')=='ARCANA_R6_THERMO_PROVIDER_PILOT_V1'
         and x.get('epoch')=='EARTH_OFFICIAL_REFERENCE_ONLY_NOT_ARCANA_T0'
         and x.get('physical_T1') is None
         and x.get('D_024')=='ACTIVE'
         and x.get('mechanical_solve_authorized') is False
         and x.get('WORLD_HISTORY_PRODUCTION_AUTHORIZED') is False
         and x.get('HistoryStore_modified') is False
         and x.get('original_rock_phase_assignments')==0
         and x.get('source_8x8_physical_rock_selection') is None
         and x.get('cross_provider_equivalence_qualified') is False
         and x.get('cross_provider_scientific_comparison_authorized') is False,
         'PILOT_AUTHORITY_OR_CROSS_MODEL_PROMOTION')
    p=x.get('providers',{})
    need(set(p)=={'MAGEMin_C.jl','Perple_X','GeoParams.jl'}, 'PILOT_PROVIDER_SET_INVALID')
    pinned={'MAGEMin_C.jl':('v2.4.5','f4fd5ce3670b73693d046e65585e2b79d45c8e3a'),
            'Perple_X':('v7.3.3','950d882bb6a9325a627109aa7154f7b526aa3087')}
    for key,(v,sha) in pinned.items():
        need(p[key].get('version')==v and p[key].get('commit_sha')==sha
             and p[key].get('repository_license_metadata')=='GPL-3.0',
             'PILOT_UPSTREAM_PIN_DRIFT_'+key)
    need(p['GeoParams.jl'].get('version')=='v0.10.0'
         and p['GeoParams.jl'].get('phase_1_execute') is False
         and p['GeoParams.jl'].get('repository_license_metadata')=='MIT'
         and p['GeoParams.jl'].get('commit_sha')=='5be510f50614774a20eb98856c1ca7c197984a4a',
         'PILOT_GEOPARAMS_SCOPE_DRIFT')
    need(p['Perple_X'].get('linux_release_sha256')==
         'ace6f81064c25709b401c3c49bc88410badad95fd7a876831c120eeed45f28e7',
         'PILOT_PERPLEX_RELEASE_DIGEST_CHANGED')
    cases=x.get('fixtures',{})
    need(set(cases)==set(CASE_IDS), 'PILOT_CASES_INVALID')
    a,b,c=(cases[name] for name in CASE_IDS)
    need(a.get('provider')==b.get('provider')=='MAGEMin_C.jl'
         and c.get('provider')=='Perple_X'
         and a.get('bulk_composition') is None
         and a.get('pressure_kbar')==8.0 and a.get('temperature_c')==800.0
         and b.get('pressure_kbar')==10.0 and b.get('temperature_c')==1100.0
         and c.get('pressure_bar')==4000.0 and c.get('temperature_k')==1050.0,
         'PILOT_OFFICIAL_FIXTURE_IDENTITY_CHANGED')
    need(len(b.get('oxides',[]))==len(b.get('amounts_wt_percent',[]))==11
         and len(set(b['oxides']))==11
         and all(type(z) in (int,float) and math.isfinite(z) and z>=0
                 for z in b['amounts_wt_percent'])
         and math.isclose(sum(b['amounts_wt_percent']),99.75,abs_tol=1e-10)
         and b['as_reported_sum_wt_percent']==99.75
         and b.get('oxide_basis')=='AS_REPORTED_WT_PERCENT_NO_NORMALIZATION'
         and {'FeO','Fe2O3','H2O'}<=set(b['oxides']),
         'PILOT_OFFICIAL_OXIDE_COMPOSITION_CHANGED')
    need(all(item.get('not_eligible_for_direct_cross_solver_comparison') is True
                 for item in cases.values()),
         'PILOT_FAKE_COMPARABILITY')
    return True


def verify_perplex_source(repo):
    repo=Path(repo).resolve()
    need(repo.is_dir(), 'PILOT_PERPLEX_SOURCE_DIR_MISSING')
    commit=subprocess.run(['git','-C',str(repo),'rev-parse','HEAD'],capture_output=True,
                          text=True,check=True).stdout.strip()
    need(commit==pins()['providers']['Perple_X']['commit_sha'], 'PILOT_PERPLEX_GIT_HEAD_DRIFT')
    path=repo/'test/bl691_MEEMUM/output/bl691_MEEMUM.prn'
    need(source_git_blob(path)==pins()['providers']['Perple_X']['official_expected_report_git_blob_sha'],
         'PILOT_PERPLEX_UPSTREAM_EXPECTED_OUTPUT_CHANGED')
    return repo


def parse_perplex_meemum(p):
    """Read only directly displayed quantities from the real official PRN."""
    raw=Path(p).read_text(errors='replace')
    def get(name):
        m=re.search(r'(?m)^\s*'+re.escape(name)+r'\s*=\s*([+\-]?[0-9]+(?:\.[0-9]*)?(?:[EeDd][+\-]?[0-9]+)?)',raw)
        need(m is not None,'PILOT_PERPLEX_MISSING_'+name)
        return float(m.group(1).replace('D','E'))
    temp,pbar=get('T(K)'),get('P(bar)')
    need(math.isclose(temp,1050.,abs_tol=.1) and math.isclose(pbar,4000.,abs_tol=.1),
         'PILOT_PERPLEX_OFFICIAL_P_T_CHANGED')
    try:
        block=raw.split('Phase Compositions (molar  proportions):',1)[1].split('Phase speciation',1)[0]
    except IndexError as e:
        raise PilotError('PILOT_PERPLEX_PHASE_SECTION_MISSING') from e
    vals={}
    for line in block.splitlines()[2:]:
        words=line.split()
        if len(words)>2 and re.match(r'^[A-Za-z]',words[0]):
            try: wt=float(words[1])
            except ValueError: continue
            need(0<=wt<=100 and words[0] not in vals,'PILOT_PERPLEX_PHASE_MODE_BAD')
            vals[words[0]]=wt
    need(vals and math.isclose(sum(vals.values()),100.,rel_tol=0,abs_tol=.3),
         'PILOT_PERPLEX_PHASE_TOTAL_BAD')
    return {'temperature_k':temp,'pressure_bar':pbar,'phases_wt_percent':vals}


def validate_magemin_result(result):
    need(result.get('provider')=='MAGEMin_C.jl'
         and result.get('version')=='2.4.5'
         and set(result.get('fixtures',{}))==set(CASE_IDS[:2]),
         'PILOT_MAGEMIN_OUTPUT_IDENTITY_INVALID')
    for name,case in result['fixtures'].items():
        fixture=pins()['fixtures'][name]
        need(math.isclose(case['P_kbar'],fixture['pressure_kbar'],abs_tol=1e-9)
             and math.isclose(case['T_C'],fixture['temperature_c'],abs_tol=1e-9)
             and case['status']==0
             and case['rho_kg_m3']>0 and math.isfinite(case['rho_kg_m3'])
             and len(case['phases'])==len(case['phase_mass_fractions'])>0
             and len(set(case['phases']))==len(case['phases'])
             and all(0<=v<=1 and math.isfinite(v) for v in case['phase_mass_fractions'])
             and abs(sum(case['phase_mass_fractions'])-1)<.02,
             'PILOT_MAGEMIN_SOLVER_OR_MASS_BALANCE_INVALID_'+name)
    return True


def load_magemin_toml(path):
    doc=tomllib.loads(Path(path).read_text())
    validate_magemin_result(doc)
    return doc


def comparable_pair(a,b):
    """Strict cross-tool comparison gate, never auto-match Earth official fixtures."""
    keys=('oxide_basis','oxide_moles','pressure_pa','temperature_k','water_state',
          'oxygen_redox_state','thermodynamic_model_crosswalk',
          'phase_name_crosswalk','chemical_reference_system')
    need(all(a.get(k) is not None and b.get(k) is not None for k in keys),
         'PILOT_CROSS_TOOL_INCOMPARABLE_MISSING_CHEMISTRY_OR_DATABASE')
    need(a['oxide_basis']==b['oxide_basis'] and a['oxide_moles']==b['oxide_moles']
         and a['water_state']==b['water_state']
         and a['oxygen_redox_state']==b['oxygen_redox_state']
         and a['thermodynamic_model_crosswalk']==b['thermodynamic_model_crosswalk']
         and a['phase_name_crosswalk']==b['phase_name_crosswalk']
         and a['chemical_reference_system']==b['chemical_reference_system']
         and math.isclose(a['pressure_pa'],b['pressure_pa'],rel_tol=1e-10)
         and math.isclose(a['temperature_k'],b['temperature_k'],rel_tol=1e-10),
         'PILOT_CROSS_TOOL_INPUT_MISMATCH')
    return True


def preflight():
    info=pins()
    return {'schema':'ARCANA_R6_THERMO_PROVIDER_PREFLIGHT_V1',
            'status':'SOURCE_REGISTER_PINNED__EXTERNAL_RUNTIME_NOT_YET_QUALIFIED',
            'registry_file_sha256':digest(PIN),
            'providers':{k:{'version':v['version'], 'commit_or_tag_sha':v.get('commit_sha',v.get('annotated_tag_sha'))}
                         for k,v in info['providers'].items()},
            'official_fixtures':list(info['fixtures']),
            'scientific_cross_provider_comparison_authorized':False,
            'official_engine_executions':0,
            'original_ARCANA_rock_assignments':0,
            'physical_T1':None,'D_024':'ACTIVE',
            'mechanical_solve_authorized':False,
            'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False}


def write_once(path,data):
    path=Path(path)
    need(not path.exists(), 'PILOT_OUTPUT_EXISTS_NO_OVERWRITE')
    need(data['physical_T1'] is None and data['D_024']=='ACTIVE'
         and data['mechanical_solve_authorized'] is False
         and data['WORLD_HISTORY_PRODUCTION_AUTHORIZED'] is False,
         'PILOT_UNAUTHORIZED_OUTPUT')
    body=json.dumps(data,indent=2,allow_nan=False)+'\n'
    path.write_text(body)
    return digest(path)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preflight-out',type=Path,required=True)
    args=ap.parse_args()
    result=preflight()
    sha=write_once(args.preflight_out,result)
    print(json.dumps({'status':result['status'],'sha256':sha,
                      'official_engine_executions':0,'physical_T1':None}))

if __name__=='__main__': main()
