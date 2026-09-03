from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
from arcana_worldsim.scientific_engines import r313_longterm_postcha1_reassembly as r313


def rows():
 d=json.loads((ROOT/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text(encoding='utf-8'))
 return d['species'] if isinstance(d,dict) and 'species' in d else d

def chronology(events,name):
 out=[]
 for e in events:
  if e.get('event')==name:
   out.append({k:e.get(k) for k in ('age_ma','elapsed_year','species_id','parent_species_id','daughter_species_id','parent_component_id','daughter_component_id','retained_component_id','absorbed_component_ids') if k in e})
 return out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--out-dir',type=Path,default=ROOT/'local_runs/v0_6D1_R3_13'); ap.add_argument('--smoke',action='store_true'); args=ap.parse_args()
 out=args.out_dir; out.mkdir(parents=True,exist_ok=True); t0=time.time()
 parent=r313.validate_parent_r312_authority(ROOT); pst=parent['state']; public={k:v for k,v in parent.items() if k!='state'}
 a1=np.load(ROOT/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz',allow_pickle=False); md=rows(); cfg=r313.R313Config(); end=r313.SMOKE_END_AGE_MA if args.smoke else r313.END_AGE_MA
 st,recs=r313.run_longterm_reassembly(pst,a1,md,cfg,end)
 inv=r313.invariant_report(st,md,cfg); before=r313.event_counts(pst); after=r313.event_counts(st); delta=r313.delta_event_counts(pst,st)
 clip_steps=sum(1 for r in recs if int(r.get('clipping_count',0))>0); clip_contacts=sum(int(r.get('clipping_count',0)) for r in recs)
 peak=max((float(r.get('max_q',0.0)) for r in recs),default=inv['q_max']); peak_u=max((float(r.get('max_unclipped_q',0.0)) for r in recs),default=inv['q_max'])
 new_events=st.events[len(pst.events):]
 reassembly=r313.ecological_reassembly_report(pst,st); provenance=r313.classify_speciation_origin_from_r312_boundary(pst,new_events)
 handoff=r313.validate_30ma_environment_handoff(a1,cfg) if abs(end-30.0)<1e-12 else None
 report={'start_age_ma':46.0,'end_age_ma':float(end),'ordinary_biology_steps':len(recs),'parent_species':len(set(pst.current_species)),'parent_components':len(pst.component_ids),'parent_total_population':float(pst.pop.sum()),'final_species':len(set(st.current_species)),'final_components':len(st.component_ids),'final_total_population':float(st.pop.sum()),'event_counts_before':before,'event_counts_after':after,'event_counts_delta':delta,'peak_q_recorded':peak,'peak_unclipped_q_recorded':peak_u,'clipping_steps':clip_steps,'clipping_contacts':clip_contacts,'invariants':inv,'ecological_reassembly':reassembly,'speciation_origin_diagnostic':provenance,'speciation_chronology':chronology(new_events,'speciation'),'ordinary_extinction_chronology':chronology(new_events,'ordinary_background_extinction'),'fission_chronology':chronology(new_events,'deme_fission'),'coalescence_chronology':chronology(new_events,'deme_coalescence'),'late_cenozoic_30ma_environment_handoff':handoff}
 exp=r313.EXPECTED_SMOKE_STEPS if args.smoke else r313.EXPECTED_STEPS
 valid_common=(len(recs)==exp and abs(st.age_ma-end)<=1e-12 and delta['CHA1_species_extinction']==0 and delta['CHA1_high_resolution_event_bridge_complete']==0 and delta['post_CHA1_ordinary_lifecycle_thaw']==0 and after['CHA1_species_extinction']==212 and after['CHA1_high_resolution_event_bridge_complete']==1 and after['post_CHA1_ordinary_lifecycle_thaw']==1 and inv['population_min']>=-1e-14 and abs(inv['population_on_inaccessible_cells'])<=1e-12 and inv['q_max']<=cfg.variance_ceiling_normalized+1e-12 and inv['s_symmetry_max_abs']<=2e-12 and inv['s_diagonal_max_abs']<=2e-12 and inv['s_min']>=-2e-12 and clip_steps==0 and clip_contacts==0 and (args.smoke or handoff['environmental_endpoint_identity_exact']))
 ck=r313.save_checkpoint(st,out,public,cfg,report,smoke=args.smoke); reload=r313.load_checkpoint(Path(ck['json']),smoke=args.smoke); ser=r38.compare_runtime_states(st,reload); valid=bool(valid_common and ser['equivalent'])
 verdict=('PASS_R313_LONGTERM_REASSEMBLY_SMOKE__ORDINARY_CONTINUATION_VALID' if valid else 'FAIL_R313_SMOKE') if args.smoke else ('PASS_CANONICAL_POST_CHA1_46_TO_30_H0_LONGTERM_DIVERSIFICATION_REASSEMBLY__30MA_LATE_CENOZOIC_HANDOFF_CHECKPOINT_READY' if valid else 'FAIL_R313_LONGTERM_REASSEMBLY')
 summary={'schema':r313.SUMMARY_SCHEMA,'stage':r313.STAGE,'mode':'SMOKE_46P0_TO_45P5' if args.smoke else 'CANONICAL_46P0_TO_30P0','verdict':verdict,'wall_seconds':time.time()-t0,'parent_r312_authority':public,'run':report,'checkpoint':ck,'serialization_identity':ser,'governance':{'cha1_already_applied':True,'cha1_reapplied':False,'lifecycle_thaw_reapplied':False,'deep_biological_coupling':False,'ordinary_lifecycle_continued':True,'richness_target_used':False,'guild_target_used':False,'positive_diversification_required_for_pass':False,'cross_guild_transition_operator_activated':False,'late_cenozoic_provider_activated_inside_stage':False,'late_cenozoic_30ma_boundary_identity_required':not args.smoke,'production_r37i_r38_runtime_used':True,'biology_cadence_years':cfg.biology_cadence_years,'mu_changed':False,'b_changed':False,'q_ceiling_changed':False,'K_center_reinterpreted_as_physical_constant':False}}
 sp=out/('R3_13_SMOKE_SUMMARY.json' if args.smoke else 'R3_13_LONGTERM_POST_CHA1_REASSEMBLY_SUMMARY.json'); sp.write_text(json.dumps(summary,indent=2),encoding='utf-8')
 print(json.dumps({'stage':r313.STAGE,'mode':summary['mode'],'verdict':verdict,'wall_seconds':summary['wall_seconds'],'biology_steps':len(recs),'age_ma':st.age_ma,'species':report['final_species'],'components':report['final_components'],'population':report['final_total_population'],'event_counts_delta':delta,'peak_q':peak,'peak_unclipped_q':peak_u,'clipping_steps':clip_steps,'active_guilds':reassembly['active_guild_count_at_end'],'absent_guilds':reassembly['guilds_absent_at_end'],'late_cenozoic_30ma_environment_identity':None if handoff is None else handoff['environmental_endpoint_identity_exact']},indent=2))
 print(json.dumps({'checkpoint':ck,'serialization_identity':ser['equivalent'],'summary':str(sp)},indent=2)); return 0 if valid else 2

if __name__=='__main__': raise SystemExit(main())
