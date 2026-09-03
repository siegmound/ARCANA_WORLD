from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.late_cenozoic.production_interface import D3LateCenozoicSubstrateAdapter
from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
from arcana_worldsim.scientific_engines import r319_phase_aware_transport_closure as r319


def metadata_rows() -> list[dict]:
    data=json.loads((ROOT/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text(encoding='utf-8'))
    return data['species'] if isinstance(data,dict) and 'species' in data else data


def chronology(events: list[dict], event_name: str) -> list[dict]:
    keys=("age_ma","elapsed_year","species_id","parent_species_id","daughter_species_id","parent_component_id","daughter_component_id","retained_component_id","absorbed_component_ids")
    return [{k:e.get(k) for k in keys if k in e} for e in events if e.get('event')==event_name]


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--out-dir',type=Path,default=ROOT/'local_runs/v0_6D1_R3_19')
    args=ap.parse_args(); args.out_dir.mkdir(parents=True,exist_ok=True)
    t0=time.time()

    parent=r319.validate_parent_r318_authority(ROOT)
    st=parent['state']; a1=parent['a1']; c2=parent['c2']; bundle=parent['bundle']; envelope=parent['envelope']
    if not hasattr(a1,'files'):
        raise TypeError('R3.19 canonical runtime requires A1 as NpzFile preserving the SEALED R3.8 .files contract')
    md=metadata_rows(); cfg=r319.R319Config()
    public_parent={k:v for k,v in parent.items() if k not in ('state','a1','c2','clock','bundle','envelope')}

    macro_env, phase_envs=r319.environments_from_r318_bundle(bundle)
    # Mandatory promotion gate on the exact canonical parent: the generalized path must collapse to R3.8 when E1=E2=E.
    eq=r319.constant_forcing_equivalence(st,a1,md,macro_env,cfg,r319.END_AGE_MA)
    if not eq['passed']:
        raise RuntimeError('R3.19 constant-forcing equivalence gate failed; production phase-aware transport is not promotable')

    endpoint0=D3LateCenozoicSubstrateAdapter(a1,c2).state_at_age(0.0)
    endpoint_access=np.asarray(endpoint0['accessible'],bool)
    shadow_state, shadow_records=r319.run_single_environment_shadow(st,a1,md,macro_env,cfg)
    state, records, coupling=r319.run_phase_aware_macrostep(
        st,a1,md,bundle,cfg,endpoint_accessible=endpoint_access
    )
    before=r319.event_counts(st); after=r319.event_counts(state); delta=r319.delta_event_counts(st,state)
    inv=r319.invariant_report(state,md,cfg)
    new_events=state.events[len(st.events):]
    clip_steps=sum(1 for r in records if int(r.get('clipping_count',0))>0)
    clip_contacts=sum(int(r.get('clipping_count',0)) for r in records)
    peak_q=max((float(r.get('max_q',0.0)) for r in records),default=float(inv['q_max']))
    peak_unclipped=max((float(r.get('max_unclipped_q',0.0)) for r in records),default=float(inv['q_max']))

    shadow_cmp=r38.compare_runtime_states(shadow_state,state,atol=0.0)
    endpoint_inaccessible_mass=float(np.asarray(state.pop,float)[:,~endpoint_access].sum())
    endpoint_inaccessible_tolerance=max(1e-8,1e-12*max(float(state.pop.sum()),1.0))
    endpoint_support_ok=endpoint_inaccessible_mass<=endpoint_inaccessible_tolerance

    report={
        'start_age_ma':r319.START_AGE_MA,'end_age_ma':r319.END_AGE_MA,
        'ordinary_biology_steps':len(records),'biology_cadence_years':float(cfg.biology_cadence_years),
        'transport_substeps':len(coupling['transport_trace']),'transport_cadence_years':float(cfg.transport_cadence_years),
        'phase_aware_transport':True,'transport_trace':coupling['transport_trace'],
        'constant_forcing_equivalence_gate':eq,
        'single_environment_shadow':{
            'role':'DIAGNOSTIC_NON_AUTHORITATIVE_OLD_SINGLE_ENVIRONMENT_COUPLING',
            'state_exactly_equal_to_phase_aware':bool(shadow_cmp.get('equivalent')),
            'state_comparison':shadow_cmp,
            'species':len(set(shadow_state.current_species)),'components':len(shadow_state.component_ids),'population':float(shadow_state.pop.sum()),
            'records':len(shadow_records),
        },
        'r318_phase_environment_global_max_abs_difference':float(envelope['transport_phases']['effective_environment_divergence']['global_max_abs_difference']),
        'parent_species':len(set(st.current_species)),'parent_components':len(st.component_ids),'parent_total_population':float(st.pop.sum()),
        'final_species':len(set(state.current_species)),'final_components':len(state.component_ids),'final_total_population':float(state.pop.sum()),
        'event_counts_before':before,'event_counts_after':after,'event_counts_delta':delta,
        'peak_q_recorded':peak_q,'peak_unclipped_q_recorded':peak_unclipped,'clipping_steps':clip_steps,'clipping_contacts':clip_contacts,
        'invariants':inv,'guild_species':r319.species_counts_by_guild(state),
        'speciation_chronology':chronology(new_events,'speciation'),'ordinary_extinction_chronology':chronology(new_events,'ordinary_background_extinction'),
        'fission_chronology':chronology(new_events,'deme_fission'),'coalescence_chronology':chronology(new_events,'deme_coalescence'),
        'support_remap_semantics':cfg.support_remap_semantics,
        'endpoint_support_reconciliation':coupling['endpoint_support_reconciliation'],
        'exact_0ka_endpoint_support_diagnostic':{
            'population_mass_on_exact_0ka_inaccessible_cells':endpoint_inaccessible_mass,
            'numerical_audit_tolerance':endpoint_inaccessible_tolerance,
            'pass':bool(endpoint_support_ok),'additional_endpoint_remap_applied':bool(coupling['endpoint_support_reconciliation'].get('applied',False)),
        },
        'deep_biological_coupling':False,'scientific_parameter_changes':False,'human_lineage_target_used':False,
    }

    q_ceiling=float(cfg.variance_ceiling_normalized)
    valid=(
        eq['passed'] is True and len(records)==1 and len(coupling['transport_trace'])==2
        and all(abs(float(x['dt_years'])-62500.0)<=1e-9 for x in coupling['transport_trace'])
        and abs(float(state.age_ma))<=1e-12 and endpoint_support_ok
        and float(inv['q_max'])<=q_ceiling+1e-12 and clip_steps==0
        and report['deep_biological_coupling'] is False and report['scientific_parameter_changes'] is False
    )
    if not valid:
        fail={
            'stage':r319.STAGE,'verdict':'FAIL_CLOSED_R319_PHASE_AWARE_TRANSPORT_OR_ENDPOINT_SUPPORT_GATE',
            'wall_seconds':time.time()-t0,'report':report,
            'checkpoint_written':False,
        }
        fp=args.out_dir/'R3_19_FAIL_CLOSED_DIAGNOSTIC.json'; fp.write_text(json.dumps(fail,indent=2),encoding='utf-8')
        print(json.dumps(fail,indent=2)); return 2

    checkpoint=r319.save_checkpoint(state,args.out_dir,public_parent,cfg,report)
    loaded=r319.load_checkpoint(Path(checkpoint['json']))
    ser=r38.compare_runtime_states(state,loaded,atol=0.0)
    if ser.get('equivalent') is not True:
        raise RuntimeError('R3.19 checkpoint serialization identity failed')

    summary={
        'schema':r319.SUMMARY_SCHEMA,'stage':r319.STAGE,'verdict':r319.VERDICT,'wall_seconds':time.time()-t0,
        'biology_steps':1,'biology_age_ma':0.0,'species':len(set(state.current_species)),'components':len(state.component_ids),'population':float(state.pop.sum()),
        'event_counts_delta':delta,'peak_q':peak_q,'peak_unclipped_q':peak_unclipped,'clipping_steps':clip_steps,
        'transport_substeps':2,'transport_phase_years':[62500.0,62500.0],'phase_aware_transport':True,
        'r318_phase_environment_global_max_abs_difference':report['r318_phase_environment_global_max_abs_difference'],
        'constant_forcing_equivalence_bit_exact':True,
        'single_environment_shadow_exactly_equal':bool(shadow_cmp.get('equivalent')),
        'single_environment_shadow_population':float(shadow_state.pop.sum()),
        'exact_0ka_inaccessible_population_mass':endpoint_inaccessible_mass,
        'exact_0ka_inaccessible_population_tolerance':endpoint_inaccessible_tolerance,
        'support_remap_semantics':cfg.support_remap_semantics,
        'deep_biological_coupling':False,'scientific_parameter_changes':False,'human_lineage_target_used':False,
        'checkpoint':checkpoint,'serialization_identity':True,'parent_r318_authority':public_parent,
    }
    sp=args.out_dir/'R3_19_H0_PRESENT_BIOLOGY_CLOSURE_SUMMARY.json'; sp.write_text(json.dumps(summary,indent=2),encoding='utf-8')

    print(json.dumps({
        'stage':r319.STAGE,'verdict':r319.VERDICT,'wall_seconds':summary['wall_seconds'],'biology_steps':1,'biology_age_ma':0.0,
        'species':summary['species'],'components':summary['components'],'population':summary['population'],'event_counts_delta':delta,
        'peak_q':peak_q,'peak_unclipped_q':peak_unclipped,'clipping_steps':clip_steps,'transport_substeps':2,
        'transport_phase_years':[62500.0,62500.0],'phase_aware_transport':True,'constant_forcing_equivalence_bit_exact':True,
        'single_environment_shadow_exactly_equal':summary['single_environment_shadow_exactly_equal'],
        'single_environment_shadow_population':summary['single_environment_shadow_population'],
        'exact_0ka_inaccessible_population_mass':endpoint_inaccessible_mass,'serialization_identity':True,
    },indent=2))
    print(json.dumps({'checkpoint':checkpoint,'summary':str(sp)},indent=2))
    try:
        if hasattr(a1,'close'): a1.close()
    except Exception: pass
    return 0

if __name__=='__main__': raise SystemExit(main())
