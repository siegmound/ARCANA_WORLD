from __future__ import annotations
from pathlib import Path
from collections import defaultdict
import json, math
import numpy as np

from . import diversity_recovery as dr
from . import adaptive_radiation as ar
from . import dynamic_demes as dd
from . import additive_variance as av


def _empty_budget():
    return {
        'selection_loss_q_sum':0.0,'drift_loss_q_sum':0.0,'mutation_gain_q_sum':0.0,
        'gene_flow_first_moment_error_max':0.0,'gene_flow_second_moment_error_max':0.0,
        'gene_flow_total_pair_exchange_mass':0.0,
    }


def initialize(root: Path, cfg: dr.DiversityRecoveryConfig):
    data=dr._load_inputs(root,cfg); p=data['parent']
    state={
      'relative_year':float(cfg.start_relative_year),
      'root_species_ids':p['root_species_id'].tolist(),
      'deme_ids':p['deme_id'].tolist(),
      'current_species':p['current_species_id'].tolist(),
      'root_idx':p['root_species_index'].astype(np.int32).copy(),
      'guild':p['guild_id'].astype(np.uint8).copy(),
      'lat':p['lat'].astype(float).copy(),'lon':p['lon'].astype(float).copy(),
      'pop':p['endpoint_population'].astype(float).copy(),
      'trait':p['endpoint_trait'].astype(float).copy(),
      'va':p['endpoint_additive_variance'].astype(float).copy(),
      'generation_time':p['generation_time_proxy_years'].astype(float).copy(),
      'ri':p['endpoint_intrinsic_RI'].astype(float).copy(),
      'clock':p['endpoint_isolation_clock_generations'].astype(float).copy(),
      'registry':{r['species_id']:dict(r) for r in data['parent_registry']},
      'new_speciation_events':[], 'new_fission_events':[],
      'variance_budget':_empty_budget(),
      'initial_total_population':float(p['endpoint_population'].sum()),
      'initial_species_richness':len(set(p['current_species_id'].tolist())),
      'initial_deme_count':len(p['deme_id']),
      'initial_variance_summary':av.normalized_variance_summary(p['endpoint_additive_variance'],p['root_species_index'],p['root_species_id'].tolist(),data['metadata'],cfg.body_mass_scale),
      'snapshot_rows':[],
    }
    G,c,td=dr._pair_metrics_fast(state['pop'],state['trait'],state['root_idx'],state['root_species_ids'],data['metadata'],state['lat'],state['lon'],cfg)
    m=ar._snapshot_metrics(state['pop'],state['trait'],state['root_idx'],state['current_species'],c,td,state['ri'],state['clock'],cfg.occupancy_floor)
    sub=dr._piecewise_substrate(data['a1'],state['relative_year'])
    state['snapshot_rows'].append({'relative_year':state['relative_year'],'age_ma':sub['age_ma'],'frame_older_ma':sub['frame_older_ma'],'frame_younger_ma':sub['frame_younger_ma'],'frame_alpha':sub['frame_alpha'],'deme_count':len(state['deme_ids']),**m})
    return data,state


def advance(root: Path, cfg: dr.DiversityRecoveryConfig, state: dict, end_relative_year: float):
    data=dr._load_inputs(root,cfg); md=data['metadata']; roots=state['root_species_ids']
    baseT,baseO=dr._reconstruct_d31_demography_baseline(data,cfg)
    species_guild=data['baseline']['guild_id'].astype(np.uint8)
    dt=float(cfg.dt_years); start=float(state['relative_year']); end=float(end_relative_year)
    nf=(end-start)/dt
    if abs(nf-round(nf))>1e-9: raise ValueError('segment must be integer timesteps')
    snap_every=max(1,int(round(cfg.snapshot_interval_years/dt))); fiss_every=max(1,int(round(cfg.deme_fission_check_interval_years/dt)))
    # Segment boundaries are materialized snapshot/fission boundaries in D3.2.
    if abs((start-cfg.start_relative_year)/cfg.snapshot_interval_years-round((start-cfg.start_relative_year)/cfg.snapshot_interval_years))>1e-9:
        raise ValueError('segment start must align with global checkpoint cadence')
    offset_steps=int(round((start-cfg.start_relative_year)/dt))
    counters=dr._child_counters_from_registry(state['registry'])

    for local in range(1,int(round(nf))+1):
        global_step=offset_steps+local; rel=start+local*dt
        sub=dr._piecewise_substrate(data['a1'],rel)
        hab=ar._habitats(state['pop'],state['trait'],state['root_idx'],roots,species_guild,md,sub,cfg)
        state['pop']=ar._migration(state['pop'],hab,state['root_idx'],roots,md,state['lat'],state['lon'],sub,dt,cfg)
        hab=ar._habitats(state['pop'],state['trait'],state['root_idx'],roots,species_guild,md,sub,cfg)
        state['pop']=ar._demography(state['pop'],hab,state['root_idx'],roots,species_guild,md,baseT,baseO,sub,dt)
        G,contact,td=dr._pair_metrics_fast(state['pop'],state['trait'],state['root_idx'],roots,md,state['lat'],state['lon'],cfg)
        targets=dd._selection_targets(state['pop'],sub['temperature_c'],sub['aridity_index'])
        before=state['trait'].copy()
        selected=dd._selection_update(state['trait'],state['va'],targets,state['root_idx'],roots,md,dt,cfg.dynamic_cfg())
        totals=state['pop'].sum(axis=(1,2))
        state['trait'],state['va'],flow=av.gene_flow_moment_mix(selected,state['va'],totals,G,state['ri'],state['root_idx'],cfg.variance_cfg())
        state['va'],components=av.advance_nonflow_variance(state['va'],before,targets,totals,state['generation_time'],state['root_idx'],roots,md,cfg.body_mass_scale,dt,cfg.variance_cfg())
        b=state['variance_budget']; b['gene_flow_first_moment_error_max']=max(b['gene_flow_first_moment_error_max'],float(flow['first_moment_conservation_max_abs'])); b['gene_flow_second_moment_error_max']=max(b['gene_flow_second_moment_error_max'],float(flow['second_moment_conservation_max_abs'])); b['gene_flow_total_pair_exchange_mass']+=float(flow['total_pair_exchange_mass'])
        for row in components:
            qb=np.asarray(row['q_before']); qs=np.asarray(row['q_after_selection']); qd=np.asarray(row['q_after_drift']); qm=np.asarray(row['q_after_mutation']); b['selection_loss_q_sum']+=float(np.maximum(qb-qs,0).sum()); b['drift_loss_q_sum']+=float(np.maximum(qs-qd,0).sum()); b['mutation_gain_q_sum']+=float(np.maximum(qm-qd,0).sum())
        td=dr._trait_distance_only(state['trait'],state['root_idx'],roots,md,cfg)
        state['ri'],state['clock']=ar._advance_pair_state(state['ri'],state['clock'],contact,td,state['generation_time'],state['root_idx'],dt)
        if global_step%fiss_every==0:
            (state['deme_ids'],state['root_idx'],state['guild'],state['current_species'],state['pop'],state['trait'],state['va'],state['generation_time'],state['ri'],state['clock'],fiss)=ar._fission_demes(state['deme_ids'],state['root_idx'],state['guild'],state['current_species'],state['pop'],state['trait'],state['va'],state['generation_time'],state['ri'],state['clock'],rel,state['lat'],state['lon'],cfg)
            for row in fiss: row['root_species_id']=roots[int(state['root_idx'][state['deme_ids'].index(row['daughter_deme_id'])])]
            state['new_fission_events'].extend(fiss)
            if fiss: G,contact,td=dr._pair_metrics_fast(state['pop'],state['trait'],state['root_idx'],roots,md,state['lat'],state['lon'],cfg)
        if cfg.speciation_enabled and global_step%snap_every==0:
            births=ar._maybe_speciate(state['current_species'],state['root_idx'],roots,state['deme_ids'],state['pop'],contact,td,state['ri'],state['clock'],state['registry'],counters,rel)
            state['new_speciation_events'].extend(births)
        if global_step%snap_every==0:
            sm=ar._snapshot_metrics(state['pop'],state['trait'],state['root_idx'],state['current_species'],contact,td,state['ri'],state['clock'],cfg.occupancy_floor)
            state['snapshot_rows'].append({'relative_year':float(rel),'age_ma':float(sub['age_ma']),'frame_older_ma':float(sub['frame_older_ma']),'frame_younger_ma':float(sub['frame_younger_ma']),'frame_alpha':float(sub['frame_alpha']),'deme_count':len(state['deme_ids']),**sm})
    state['relative_year']=end
    return data,state


def save(path: Path,state:dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(path,
      relative_year=np.asarray([state['relative_year']]),root_species_id=np.asarray(state['root_species_ids']),deme_id=np.asarray(state['deme_ids']),current_species_id=np.asarray(state['current_species']),root_species_index=state['root_idx'],guild_id=state['guild'],lat=state['lat'],lon=state['lon'],population=state['pop'],trait=state['trait'],additive_variance=state['va'],generation_time=state['generation_time'],intrinsic_RI=state['ri'],isolation_clock=state['clock'])
    meta={k:v for k,v in state.items() if k not in {'root_species_ids','deme_ids','current_species','root_idx','guild','lat','lon','pop','trait','va','generation_time','ri','clock','relative_year'}}
    path.with_suffix('.json').write_text(json.dumps(meta,indent=2,sort_keys=True),encoding='utf-8')


def load(path:Path):
    z=np.load(path,allow_pickle=False); meta=json.loads(path.with_suffix('.json').read_text())
    return {**meta,'relative_year':float(z['relative_year'][0]),'root_species_ids':z['root_species_id'].tolist(),'deme_ids':z['deme_id'].tolist(),'current_species':z['current_species_id'].tolist(),'root_idx':z['root_species_index'].astype(np.int32),'guild':z['guild_id'].astype(np.uint8),'lat':z['lat'].astype(float),'lon':z['lon'].astype(float),'pop':z['population'].astype(float),'trait':z['trait'].astype(float),'va':z['additive_variance'].astype(float),'generation_time':z['generation_time'].astype(float),'ri':z['intrinsic_RI'].astype(float),'clock':z['isolation_clock'].astype(float)}


def finalize(root:Path,cfg:dr.DiversityRecoveryConfig,state:dict):
    data=dr._load_inputs(root,cfg); md=data['metadata']; roots=state['root_species_ids']
    G,c,td=dr._pair_metrics_fast(state['pop'],state['trait'],state['root_idx'],roots,md,state['lat'],state['lon'],cfg)
    final_species=sorted(set(state['current_species'])); va_summary=av.normalized_variance_summary(state['va'],state['root_idx'],roots,md,cfg.body_mass_scale); gates=dr._pair_gate_counts(state['root_idx'],c,td,state['ri'],state['clock'])
    lineage=defaultdict(int)
    for sid in final_species: lineage[state['registry'][sid]['root_species_id']]+=1
    diversified={k:v for k,v in lineage.items() if v>1}; birth_times=[float(x['relative_year']) for x in state['new_speciation_events']]
    rows=state['snapshot_rows']
    diag={
      'status':dr.STATUS,'config':cfg.__dict__,'parent_status':data['parent_diag']['status'],'continuation_semantics':'CHECKPOINTED_EXACT_STATE_CONTINUATION_NO_RESET_BETWEEN_5_10_15_20_MYR','checkpoint_boundaries_relative_year':[10_000_000.0,15_000_000.0,17_500_000.0],
      'start_relative_year':cfg.start_relative_year,'end_relative_year':state['relative_year'],'start_physical_age_ma':61.0,'end_physical_age_ma':66.0-state['relative_year']/1e6,'physical_provider':cfg.physical_provider,'materialized_physical_frames_crossed_ma':[60.0],
      'physical_interpolation_brackets_used':sorted({(r['frame_older_ma'],r['frame_younger_ma']) for r in rows},reverse=True),'initial_species_richness':state['initial_species_richness'],'final_species_richness':len(final_species),'new_speciation_event_count':len(state['new_speciation_events']),'cumulative_speciation_event_count':len(data['inherited_speciation_events'])+len(state['new_speciation_events']),
      'initial_deme_count':state['initial_deme_count'],'final_deme_count':len(state['deme_ids']),'new_deme_fission_event_count':len(state['new_fission_events']),'cumulative_deme_fission_event_count':len(data['inherited_fission_events'])+len(state['new_fission_events']),'initial_total_population':state['initial_total_population'],'final_total_population':float(state['pop'].sum()),'relative_total_population_change':float((state['pop'].sum()-state['initial_total_population'])/state['initial_total_population']),
      'initial_normalized_additive_variance_summary':state['initial_variance_summary'],'final_normalized_additive_variance_summary':va_summary,'max_normalized_additive_variance':float(va_summary['max']),'variance_budget':state['variance_budget'],'pair_gate_counts':gates,'diversified_root_lineage_count':len(diversified),'diversified_root_lineages':dict(sorted(diversified.items())),'first_new_speciation_relative_year':min(birth_times) if birth_times else None,'last_new_speciation_relative_year':max(birth_times) if birth_times else None,
      'background_species_extinction_enabled':False,'species_fusion_enabled':False,'Deep_adaptation_enabled':False,'dragon_lineage_selection_enabled':False,'sapience_enabled':False,'civilization_enabled':False,'author_selected_winner_enabled':False,'HSG_025_trait_provenance':md['HSG_025'].get('trait_provenance'),'snapshot_rows':rows,
      'interpretation':'D3.2 is an emergent 5-20 Myr diversity-recovery replay. Checkpoint boundaries serialize the complete dynamic state and do not reset evolutionary variables.'}
    out=root/'outputs/hybrid1/diversity_recovery_v0_6_3D3_2'; out.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(out/'diversity_recovery_state.npz',root_species_id=np.asarray(roots),final_species_id=np.asarray(final_species),deme_id=np.asarray(state['deme_ids']),current_species_id=np.asarray(state['current_species']),root_species_index=state['root_idx'],guild_id=state['guild'],lat=state['lat'].astype(np.float32),lon=state['lon'].astype(np.float32),snapshot_relative_year=np.asarray([r['relative_year'] for r in rows]),species_richness_history=np.asarray([r['species_richness'] for r in rows],dtype=np.int32),total_population_history=np.asarray([r['total_population'] for r in rows]),occupied_cell_history=np.asarray([r['occupied_deme_cells'] for r in rows],dtype=np.int64),max_trait_distance_history=np.asarray([r['max_trait_distance'] for r in rows]),max_intrinsic_RI_history=np.asarray([r['max_intrinsic_RI'] for r in rows]),max_isolation_clock_history=np.asarray([r['max_isolation_clock_generations'] for r in rows]),endpoint_population=state['pop'],endpoint_trait=state['trait'],endpoint_additive_variance=state['va'],generation_time_proxy_years=state['generation_time'],endpoint_intrinsic_RI=state['ri'],endpoint_isolation_clock_generations=state['clock'],endpoint_contact_connectivity=c,endpoint_trait_distance=td)
    (out/'diversity_recovery_diagnostics.json').write_text(json.dumps(diag,indent=2,sort_keys=True),encoding='utf-8'); (out/'species_registry.json').write_text(json.dumps({'species':[state['registry'][k] for k in sorted(state['registry'])]},indent=2,sort_keys=True),encoding='utf-8'); (out/'speciation_events_5_20myr.json').write_text(json.dumps({'events':state['new_speciation_events']},indent=2,sort_keys=True),encoding='utf-8'); (out/'deme_fission_events_5_20myr.json').write_text(json.dumps({'events':state['new_fission_events']},indent=2,sort_keys=True),encoding='utf-8')
    return diag
