from __future__ import annotations

import argparse, json, sys, hashlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any
import numpy as np


def hfile(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

class FakeC2:
    def supports_age(self, age):
        y=round(float(age)*1_000_000)
        return -1e-12 <= float(age) <= .25+1e-12 and abs(float(age)*1_000_000-y)<1e-7

class FakeAdapter:
    def __init__(self,*_a,constant=False,**_k): self.constant=constant
    def state_at_age(self, age):
        age=float(age); x=.05 if self.constant else age
        support=np.ones((2,3),float)
        if not self.constant and age <= .0625+1e-12: support[0,0]=0.0
        if not self.constant and age <= 1e-12: support[1,2]=0.0
        browse=np.full((2,3),1+x); low=np.full((2,3),.5+.5*x); wet=np.full((2,3),.25+.25*x)
        return {'age_ma':age,'land_support':support,'accessible':support>1e-9,
                'temperature_c':np.full((2,3),10+x),'aridity_index':np.full((2,3),.3+.01*x),
                'browse_forage':browse,'low_forage':low,'wetland_forage':wet,'total_edible_forage':browse+low+wet,
                'reference_population':np.full((2,2,3),3+x)}

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args(); root=args.root.resolve(); out=args.out.resolve(); sys.path.insert(0,str(root/'src'))
    from arcana_worldsim.scientific_engines import r318_recent_exposure_transport_readiness as r318

    checks=[]
    def ck(name,cond,actual=None,expected=None): checks.append({'name':name,'pass':bool(cond),'actual':actual,'expected':expected})

    c=r318.R318Config()
    constants={'physical_start_age_ma':(.12,c.physical_start_age_ma),'physical_end_age_ma':(0,c.physical_end_age_ma),
               'biology_state_age_ma':(.125,c.biology_state_age_ma),'transport_boundary_age_ma':(.0625,c.transport_boundary_age_ma),
               'biology_cadence_years':(125000,c.biology_cadence_years),'transport_cadence_years':(62500,c.transport_cadence_years)}
    for k,(want,got) in constants.items(): ck('config::'+k,abs(float(got)-float(want))<=1e-12,got,want)
    for k in ('advance_biology','advance_transport','advance_gene_flow','advance_lifecycle_gates','deep_biological_coupling'):
        ck('config_false::'+k,getattr(c,k) is False,getattr(c,k),False)

    clock={'age_ma':np.asarray([.120,.115,.110,.105,.100,.095,.090,.085,.080,.075,.070,.065,.060,.055,.050,.045,.040,.035,.030,.025,.020,.015,.010,.005,0.0])}
    p=r318.recent_partition(clock)
    ck('recent_duration_120k',abs(p['total_years']-120000)<1e-6,p['total_years'],120000)
    ck('recent_contains_62p5',p['contains_62p5ka_transport_boundary'] is True,p['nodes_age_ma'])
    ck('recent_endpoints',abs(p['nodes_age_ma'][0]-.12)<1e-12 and abs(p['nodes_age_ma'][-1])<1e-12,p['nodes_age_ma'][0:1]+p['nodes_age_ma'][-1:])
    for i,s in enumerate(p['segments']):
        ck(f'recent_positive_dt::{i}',float(s['dt_years'])>0,s['dt_years'])
        ck(f'recent_order::{i}',float(s['older_age_ma'])>float(s['younger_age_ma']),s)

    orig=r318.D3LateCenozoicSubstrateAdapter; r318.D3LateCenozoicSubstrateAdapter=FakeAdapter
    try:
        pending_state=FakeAdapter().state_at_age(.1225)
        pending={'duration_years':5000.0,'integrals':{k:np.asarray(pending_state[k],float)*5000.0 for k in r318.AVERAGED_FIELDS}}
        parent=SimpleNamespace(age_ma=.125,pop=np.ones((2,2,3),float),current_accessible=np.ones((2,3),bool))
        env,groups=r318.build_recent_exposure_readiness(parent,None,FakeC2(),clock,pending)
    finally:
        r318.D3LateCenozoicSubstrateAdapter=orig

    ck('env_schema',env['schema']==r318.ENVELOPE_SCHEMA,env['schema'],r318.ENVELOPE_SCHEMA)
    ck('env_bio_125',env['biology_state_age_ma']==.125,env['biology_state_age_ma'],.125)
    ck('env_not_mutated',env['biology_state_mutated'] is False,env['biology_state_mutated'])
    ck('env_not_relabelled',env['biology_state_relabelled_to_0ka'] is False,env['biology_state_relabelled_to_0ka'])
    ck('full_duration_125k',env['full_125ka_macrostep']['duration_years']==125000.0,env['full_125ka_macrostep'])
    ck('pending_5k',env['full_125ka_macrostep']['r317_pending_years']==5000.0,env['full_125ka_macrostep'])
    ck('recent_120k',env['full_125ka_macrostep']['r318_recent_years']==120000.0,env['full_125ka_macrostep'])
    ck('phase1_62500',env['transport_phases']['phase1']['duration_years']==62500.0,env['transport_phases']['phase1'])
    ck('phase2_62500',env['transport_phases']['phase2']['duration_years']==62500.0,env['transport_phases']['phase2'])
    ck('phase_boundary',env['transport_phases']['boundary_age_ma']==.0625,env['transport_phases']['boundary_age_ma'],.0625)
    ck('phase_closure',env['full_125ka_macrostep']['integral_phase_closure_max_abs']<1e-6,env['full_125ka_macrostep']['integral_phase_closure_max_abs'])
    for group in ('recent_120_to_0','full_125_to_0','transport_phase1_125_to_62p5','transport_phase2_62p5_to_0'):
        ck('group_exists::'+group,group in groups,sorted(groups))
        for k in r318.AVERAGED_FIELDS:
            a=np.asarray(groups[group][k],float)
            ck(f'group_field::{group}::{k}',k in groups[group])
            ck(f'group_finite::{group}::{k}',bool(np.isfinite(a).all()))
    for k in r318.AVERAGED_FIELDS:
        err=np.asarray(groups['full_125_to_0'][k])-(np.asarray(groups['transport_phase1_125_to_62p5'][k])+np.asarray(groups['transport_phase2_62p5_to_0'][k]))
        ck('field_phase_closure::'+k,float(np.max(np.abs(err)))<1e-6,float(np.max(np.abs(err))))

    div=env['transport_phases']['effective_environment_divergence']
    ck('variable_forcing_detected',div['roundoff_equivalent_all_fields'] is False,div['global_max_abs_difference'])
    ck('phase_operator_required',env['transport_phases']['phase_aware_transport_operator_required'] is True,env['transport_phases']['phase_aware_transport_operator_required'])
    for k,row in div['fields'].items():
        ck('div_field_shape::'+k,row['max_abs_error']>=0,row)
        ck('div_field_tol::'+k,row['roundoff_tolerance']>0,row)

    gov=env['governance']
    for k in ('biology_advanced','transport_advanced','gene_flow_advanced','lifecycle_gates_advanced','biology_cadence_changed','transport_cadence_changed','adaptive_clock_used_as_biology_timestep','support_remap_applied','scientific_parameter_changes','deep_biological_coupling','richness_target_used','human_lineage_target_used','production_biology_closure_authorized_in_r318'):
        ck('gov_false::'+k,gov[k] is False,gov[k],False)
    ck('next_stage_guard','R3.19_MUST_VALIDATE' in env['next_stage_requirement'],env['next_stage_requirement'])

    # Constant forcing must collapse the two transport exposure environments to numerical roundoff equivalence.
    class ConstAdapter(FakeAdapter):
        def __init__(self,*a,**k): super().__init__(*a,constant=True,**k)
    orig=r318.D3LateCenozoicSubstrateAdapter; r318.D3LateCenozoicSubstrateAdapter=ConstAdapter
    try:
        cs=ConstAdapter().state_at_age(.05)
        pend={'duration_years':5000.0,'integrals':{k:np.asarray(cs[k],float)*5000.0 for k in r318.AVERAGED_FIELDS}}
        parent=SimpleNamespace(age_ma=.125,pop=np.ones((2,2,3),float),current_accessible=np.ones((2,3),bool))
        cenv,_=r318.build_recent_exposure_readiness(parent,None,FakeC2(),clock,pend)
    finally:
        r318.D3LateCenozoicSubstrateAdapter=orig
    ck('constant_phase_equivalence',cenv['transport_phases']['effective_environment_divergence']['roundoff_equivalent_all_fields'] is True,cenv['transport_phases']['effective_environment_divergence'])
    ck('constant_no_phase_operator_required',cenv['transport_phases']['phase_aware_transport_operator_required'] is False,cenv['transport_phases']['phase_aware_transport_operator_required'])

    # R3.18 must remain evidence-only: no biology/transport production operator call in source.
    src=root/'src/arcana_worldsim/scientific_engines/r318_recent_exposure_transport_readiness.py'
    text=src.read_text(encoding='utf-8')
    forbidden=('r38.advance_state(','_apply_demography(','_migration_subcycled_r3(','select_traits(','gene_flow_moment_mix(','advance_nonflow_variance(','advance_pair_states(','maybe_speciate_founder(','ordinary_extinction_update(','apply_mature_fissions_r3(','apply_mature_coalescences_r33(')
    for token in forbidden: ck('source_forbidden_absent::'+token,token not in text,token if token in text else None)
    required=('TRANSPORT_BOUNDARY_AGE_MA = 0.0625','production_biology_closure_authorized_in_r318','R3.19_MUST_VALIDATE_A_PHASE_AWARE_TRANSPORT_COUPLING_OPERATOR')
    for token in required: ck('source_required_present::'+token[:40],token in text)

    mp=root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_18.json'
    ck('manifest_exists',mp.is_file(),str(mp))
    manifest=json.loads(mp.read_text(encoding='utf-8')) if mp.is_file() else {}
    ck('manifest_stage',manifest.get('stage')==r318.STAGE,manifest.get('stage'),r318.STAGE)
    ck('manifest_science_unchanged',manifest.get('scientific_parameter_changes') is False,manifest.get('scientific_parameter_changes'))
    ck('manifest_biology_unchanged',manifest.get('biology_cadence_changes') is False,manifest.get('biology_cadence_changes'))
    for rel,want in manifest.get('inherited_authorities_unchanged',{}).items():
        q=root/rel; ck('authority_exists::'+rel,q.is_file(),str(q))
        if q.is_file(): ck('authority_sha::'+rel,hfile(q)==want,hfile(q),want)
    for rel,want in manifest.get('r318_files',{}).items():
        q=root/rel; ck('r318_exists::'+rel,q.is_file(),str(q))
        if q.is_file(): ck('r318_sha::'+rel,hfile(q)==want,hfile(q),want)

    failed=[x for x in checks if not x['pass']]
    verdict='PASS_R318_CANDIDATE_FORMAL_AUDIT__READY_FOR_LOCAL_RECENT_EXPOSURE_TRANSPORT_PHASE_READINESS_RUN' if not failed else 'FAIL_R318_CANDIDATE_FORMAL_AUDIT'
    audit={'schema':'ARCANA_R318_FORMAL_CANDIDATE_AUDIT_V1','stage':r318.STAGE,'verdict':verdict,
           'checks':f"{len(checks)-len(failed)}/{len(checks)}",'failed':failed,
           'decision':'COMPLETE_RECENT_EXPOSURE_AND_DEFER_PRODUCTION_BIOLOGY_UNTIL_PHASE_AWARE_TRANSPORT_OPERATOR_IS_VALIDATED',
           'physical_start_age_ma':.120,'physical_end_age_ma':0.0,'biology_state_age_ma':.125,'transport_boundary_age_ma':.0625,
           'production_biology_closure_authorized':False,'scientific_parameter_changes':False,'deep_biological_coupling':False,
           'source_manifest_sha256':hfile(mp) if mp.is_file() else None}
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print(json.dumps({'verdict':verdict,'checks':audit['checks'],'out':str(out)},indent=2))
    return 0 if not failed else 1

if __name__=='__main__': raise SystemExit(main())
