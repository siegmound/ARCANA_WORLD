from __future__ import annotations

from pathlib import Path
from typing import Any
from collections import OrderedDict
import copy
import hashlib
import importlib.util
import json
import random

import numpy as np

STAGE='v0.6D1-R4.38'
PARENT_COMPLETE='PASS_R437_GEONOMICS_CANONICAL_LAYER_BINDING_AND_EXACT_STATE_INJECTION_DRY_RUN_VALIDATION_COMPLETE'
PARENT_SEALED='PASS_R437_GEONOMICS_CANONICAL_LAYER_BINDING_AND_EXACT_STATE_INJECTION_DRY_RUN_VALIDATION_SEALED'
PARENT_R3='PASS_R437_R3_VALIDATION_CLOSURE_AND_R437_RESEAL_VERIFIED'
PARENT_NEXT='BUILD_R438_GEONOMICS_EXACT_INITIALIZATION_ADAPTER_AND_CONSTRUCTION_PROBE_ELIMINATION_PREFLIGHT'
COMPLETE='PASS_R438_GEONOMICS_EXACT_INITIALIZATION_ADAPTER_AND_CONSTRUCTION_PROBE_ELIMINATION_PREFLIGHT_COMPLETE'
SEALED='PASS_R438_GEONOMICS_EXACT_INITIALIZATION_ADAPTER_AND_CONSTRUCTION_PROBE_ELIMINATION_PREFLIGHT_SEALED'
BLOCKED='BLOCKED_R438_EXACT_INITIALIZATION_ADAPTER_OR_CONSTRUCTION_PROBE_ELIMINATION_PREFLIGHT_FAILURE'
NEXT='BUILD_R439_GEONOMICS_RUNTIME_TIME_MAPPING_NONLITERAL_CARRIER_DYNAMICS_AND_DYNAMIC_LAYER_CHANGE_PREFLIGHT'

OUT=Path('outputs/v0_6D1_R4_38')
SEAL=Path('outputs/v0_6D1_R4_38_SEAL/R4_38_FINAL_SEAL_AUDIT.json')
CFG=Path('configs/world1_r438_geonomics_exact_initialization_adapter_construction_probe_elimination_preflight_v0_6D1_R4_38.json')
R437=Path('outputs/v0_6D1_R4_37/R4_37_INTEGRATED_AUDIT.json')
R437_SEAL=Path('outputs/v0_6D1_R4_37_SEAL/R4_37_FINAL_SEAL_AUDIT.json')
R437_R3=Path('outputs/v0_6D1_R4_37_R3/R4_37_R3_POSTREPAIR_RESEAL_AUDIT.json')
R436_NATIVE=Path('outputs/v0_6D1_R4_36/R4_36_GEONOMICS_NATIVE_PARAMETER_AND_MODEL_CONSTRUCTION_PREFLIGHT.json')
R436_PAYLOAD=Path('outputs/v0_6D1_R4_36/R4_36_EXACT_STATE_INJECTION_AND_CANONICAL_PAYLOAD_PREFLIGHT.json')

J14='R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS'
J18='R42_J18_SAPIENT_200KA_TO_0_GEONOMICS'
J14_MANIFEST=Path(f'outputs/v0_6D1_R4_36/exact_state_injection/{J14}/INITIAL_STATE_INJECTION_PREFLIGHT.json')
J18_MANIFEST=Path(f'outputs/v0_6D1_R4_36/exact_state_injection/{J18}/INITIAL_STATE_INJECTION_PREFLIGHT.json')


def load(p:Path)->Any:
    return json.loads(p.read_text(encoding='utf-8'))

def write(p:Path,obj:Any)->None:
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf-8')

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def _import_params_module(path:Path)->dict[str,Any]:
    name='r438_params_'+hashlib.sha1(str(path).encode()).hexdigest()[:12]
    spec=importlib.util.spec_from_file_location(name,str(path))
    if spec is None or spec.loader is None: raise RuntimeError(f'cannot import {path}')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    params=getattr(mod,'params',None)
    if not isinstance(params,dict): raise TypeError(f'{path} missing dict params')
    return params

def _native_records(native:dict[str,Any],job_id:str)->list[dict[str,Any]]:
    rows=[r for r in native.get('records') or [] if r.get('job_id')==job_id and r.get('construction_pass') is True]
    return sorted(rows,key=lambda r:int(r['replicate_index']))

def _rng_digest()->dict[str,str]:
    py=repr(random.getstate()).encode('utf-8')
    npst=np.random.get_state()
    np_blob=(str(npst[0])+'|'+npst[1].tobytes().hex()+'|'+str(npst[2])+'|'+str(npst[3])+'|'+repr(float(npst[4]))).encode('utf-8')
    return {'python_random':hashlib.sha256(py).hexdigest(),'numpy_random':hashlib.sha256(np_blob).hexdigest()}

def _array_digest(a:np.ndarray)->str:
    a=np.asarray(a); h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(str(a.shape).encode()); h.update(a.tobytes(order='C')); return h.hexdigest()

def _land_digest(land:Any)->str:
    h=hashlib.sha256()
    for k,lyr in land.items():
        h.update(str(k).encode()); h.update(str(lyr.name).encode()); h.update(_array_digest(np.asarray(lyr.rast)).encode())
    return h.hexdigest()

def _coords(branch:dict[str,Any])->list[list[float]]:
    return [[float(c['x_grid_col']),float(c['y_grid_row'])] for c in branch.get('carriers') or []]

def _coords_digest(coords:list[list[float]])->str:
    return hashlib.sha256(json.dumps(coords,separators=(',',':')).encode()).hexdigest()


def _install_exact_nonliteral_carriers(mod:Any, probe_template:Any, coords:list[list[float]])->dict[str,Any]:
    # Narrow adapter for the intentionally nongenomic carrier Species.
    spp=mod.comm[0]
    if spp.gen_arch is not None or getattr(spp,'_tc',None) is not None:
        raise RuntimeError('R438 adapter is authorized only for nongenomic construction-probe Species')
    if len(coords)<=0:
        raise RuntimeError('R438 zero-carrier branch unsupported; fail closed')

    rng_before=_rng_digest(); land_before=_land_digest(mod.land)
    k_before=_array_digest(np.asarray(spp.K)) if spp.K is not None else None
    old_objects=list(spp.values())

    inds=OrderedDict()
    for idx,(x,y) in enumerate(coords):
        ind=copy.deepcopy(probe_template)
        ind.idx=int(idx); ind._set_pos(float(x),float(y)); ind.age=0; ind.sex=None
        ind.e=None; ind.z=[]; ind.fit=None; ind._individuals_tab_id=None; ind._nodes_tab_ids={}
        inds[idx]=ind

    spp.clear(); spp.update(inds)
    spp.max_ind_idx=len(inds)-1; spp.start_N=len(inds)
    spp.Nt=[]; spp.n_births=[]; spp.n_deaths=[]
    spp.extinct=False; spp.burned=False; spp.t=-1
    spp.N=None; spp._coords=None; spp._cells=None; spp._kd_tree=None; spp._dens_grids=None

    spp._set_coords_and_cells(); spp._set_kd_tree(); spp._set_dens_grids(mod.land)
    spp._calc_density(set_N=True); spp._set_e(mod.land)

    if mod.rand_comm is not False:
        raise RuntimeError('R438 requires rand_comm=False so orig_comm is authoritative reset state')
    mod.orig_comm=copy.deepcopy(mod.comm)

    expected=np.asarray(coords,dtype=float)
    observed=np.asarray([[float(ind.x),float(ind.y)] for ind in spp.values()],dtype=float)
    orig_observed=np.asarray([[float(ind.x),float(ind.y)] for ind in mod.orig_comm[0].values()],dtype=float)
    cache=np.asarray(spp._coords,dtype=float); cells=np.asarray(spp._cells); expected_cells=np.int32(np.floor(expected))
    env_ok=all(ind.e is not None and len(ind.e)==len(mod.land) for ind in spp.values())
    n_ok=spp.N is not None and np.all(np.isfinite(np.asarray(spp.N)))
    k_after=_array_digest(np.asarray(spp.K)) if spp.K is not None else None
    land_after=_land_digest(mod.land); rng_after=_rng_digest()
    old_probe_eliminated=all(all(ind is not old for old in old_objects) for ind in spp.values())
    exact=observed.shape==expected.shape and np.array_equal(observed,expected)
    cache_exact=cache.shape==expected.shape and np.array_equal(cache,expected)
    cells_exact=cells.shape==expected_cells.shape and np.array_equal(cells,expected_cells)
    orig_exact=orig_observed.shape==expected.shape and np.array_equal(orig_observed,expected)
    unrun=mod.t==-1 and mod.burn_t==-1 and mod.it==-1 and spp.t==-1

    passed=all([len(spp)==len(coords),exact,cache_exact,cells_exact,orig_exact,env_ok,n_ok,old_probe_eliminated,unrun,k_before==k_after,land_before==land_after,rng_before==rng_after,spp.burned is False,spp.gen_arch is None,getattr(spp,'_tc',None) is None])
    return {'pass':bool(passed),'carrier_count':len(coords),'coordinate_digest':_coords_digest(coords),'exact_coordinates_installed':bool(exact),'coords_cache_exact':bool(cache_exact),'cells_cache_exact_floor_mapping':bool(cells_exact),'orig_comm_exact_and_probe_free':bool(orig_exact and old_probe_eliminated),'construction_probe_eliminated':bool(old_probe_eliminated),'environment_cache_initialized':bool(env_ok),'density_cache_initialized':bool(n_ok),'K_unchanged':k_before==k_after,'landscape_unchanged':land_before==land_after,'rng_state_unchanged':rng_before==rng_after,'model_and_species_unrun':bool(unrun),'species_burned':bool(spp.burned),'species_gen_arch_is_none':spp.gen_arch is None,'species_tskit_table_is_none':getattr(spp,'_tc',None) is None,'population_proxy_used_as_individual_count':False,'population_proxy_consumed_by_adapter':False,'nonliteral_carrier_semantics':True,'direct_ordereddict_state_adapter_used':True,'geonomics_private_population_add_remove_called':False,'model_run_performed':False}


def _validate_job(root:Path,native:dict[str,Any],job_id:str,manifest:dict[str,Any])->dict[str,Any]:
    import geonomics as gnx
    if str(getattr(gnx,'__version__',''))!='1.4.9': return {'status':'BLOCKED_R438_GEONOMICS_VERSION','geonomics_version':getattr(gnx,'__version__',None)}
    rows=_native_records(native,job_id); branches=manifest.get('branches') or []
    if len(rows)!=4: return {'status':'BLOCKED_R438_NATIVE_RECORD_COUNT','record_count':len(rows)}
    zero=sum(1 for b in branches if len(_coords(b))==0)
    if zero: return {'status':'BLOCKED_R438_ZERO_CARRIER_BRANCH','zero_carrier_branch_count':zero}

    records=[]
    for base in rows:
        rep=int(base['replicate_index']); seed=int(base['frozen_seed']); pf=root/base['native_parameter_file']
        if sha256(pf)!=base['native_parameter_file_sha256']:
            records.append({'replicate_index':rep,'pass':False,'error':'R436_NATIVE_PARAMETER_HASH_MISMATCH'}); continue
        try:
            params=_import_params_module(pf); pdict=gnx.make_params_dict(params,model_name=params['model']['name']); mod=gnx.make_model(parameters=pdict,verbose=False)
            spp=mod.comm[0]; initial_probe_count=len(spp); probe=copy.deepcopy(next(iter(spp.values()))) if len(spp)==1 else None
            seed_ok=mod.seed==seed; unrun0=mod.t==-1 and mod.burn_t==-1 and mod.it==-1
            preconditions=initial_probe_count==1 and probe is not None and spp.gen_arch is None and getattr(spp,'_tc',None) is None and mod.rand_comm is False and mod.orig_comm is not None
            branch_results=[]
            if preconditions and seed_ok and unrun0:
                for bi,b in enumerate(branches):
                    res=_install_exact_nonliteral_carriers(mod,probe,_coords(b)); res['branch_index']=bi; branch_results.append(res)
                    if not res['pass']: break
            pass_count=sum(bool(x.get('pass')) for x in branch_results); passed=bool(preconditions and seed_ok and unrun0 and pass_count==len(branches))
            records.append({'replicate_index':rep,'frozen_seed':seed,'model_seed_match':seed_ok,'model_unrun_before_adapter':unrun0,'initial_construction_probe_count':initial_probe_count,'construction_probe_is_nongenomic':spp.gen_arch is None,'rand_comm_false':mod.rand_comm is False,'orig_comm_present':mod.orig_comm is not None,'branch_count':len(branches),'branch_pass_count':pass_count,'all_branches_exact_adapter_pass':pass_count==len(branches),'model_run_performed':False,'pass':passed,'first_failed_branch':next((x for x in branch_results if not x.get('pass')),None)})
            del mod
        except Exception as exc:
            records.append({'replicate_index':rep,'frozen_seed':seed,'pass':False,'error':repr(exc)})
    rp=sum(bool(r.get('pass')) for r in records)
    return {'status':'R438_EXACT_INITIALIZATION_ADAPTER_VALIDATED' if len(records)==4 and rp==4 else BLOCKED,'job_id':job_id,'replicate_count':len(records),'replicate_pass_count':rp,'branch_count':len(branches),'zero_carrier_branch_count':zero,'total_carrier_count':manifest.get('total_carrier_count'),'exact_initialization_adapter_validated':len(records)==4 and rp==4,'construction_probe_elimination_validated':len(records)==4 and rp==4,'all_branch_coordinates_installed_exactly':len(records)==4 and rp==4,'orig_comm_reset_state_updated':len(records)==4 and rp==4,'population_proxy_used_as_individual_count':False,'model_run_performed_count':0,'records':records}


def build(root:Path)->dict[str,Any]:
    root=root.resolve(); cfg=load(root/CFG); pa=load(root/R437); ps=load(root/R437_SEAL); pr3=load(root/R437_R3); native=load(root/R436_NATIVE); pp=load(root/R436_PAYLOAD)
    j14m=load(root/J14_MANIFEST); j18m=load(root/J18_MANIFEST)
    h14=sha256(root/J14_MANIFEST)==pp['j14_injection_manifest_sha256']; h18=sha256(root/J18_MANIFEST)==pp['j18_injection_manifest_sha256']
    j14=_validate_job(root,native,J14,j14m) if h14 else {'status':'BLOCKED_HASH'}; j18=_validate_job(root,native,J18,j18m) if h18 else {'status':'BLOCKED_HASH'}
    write(root/OUT/'R4_38_J14_EXACT_INITIALIZATION_ADAPTER_AUDIT.json',j14); write(root/OUT/'R4_38_J18_EXACT_INITIALIZATION_ADAPTER_AUDIT.json',j18)
    checks={'parent_r437_complete_40_40':pa.get('status')==PARENT_COMPLETE and pa.get('checks_passed')==40 and pa.get('checks_failed')==0,'parent_r437_sealed_28_28':ps.get('status')==PARENT_SEALED and ps.get('verdict')=='SEALED' and ps.get('checks_passed')==28,'parent_r437_r3_verified_17_17':pr3.get('status')==PARENT_R3 and pr3.get('checks_passed')==17,'parent_next_action_r438':pa.get('next_action')==PARENT_NEXT and ps.get('next_action')==PARENT_NEXT and pr3.get('next_action')==PARENT_NEXT,'policy_frozen':cfg.get('policy')=='R438_EXACT_NONGENOMIC_CARRIER_INITIALIZATION_ADAPTER_PREFLIGHT_NO_EXECUTION','j14_manifest_hash':h14,'j18_manifest_hash':h18,'j14_4_replicates':j14.get('replicate_pass_count')==4,'j18_4_replicates':j18.get('replicate_pass_count')==4,'j14_192_branches':j14.get('branch_count')==192,'j18_64_branches':j18.get('branch_count')==64,'j14_854_carriers':j14.get('total_carrier_count')==854,'j18_319_carriers':j18.get('total_carrier_count')==319,'no_zero_carrier_branches':j14.get('zero_carrier_branch_count')==0 and j18.get('zero_carrier_branch_count')==0,'j14_adapter_validated':j14.get('exact_initialization_adapter_validated') is True,'j18_adapter_validated':j18.get('exact_initialization_adapter_validated') is True,'probe_elimination_validated':j14.get('construction_probe_elimination_validated') is True and j18.get('construction_probe_elimination_validated') is True,'orig_comm_reset_state_updated':j14.get('orig_comm_reset_state_updated') is True and j18.get('orig_comm_reset_state_updated') is True,'population_proxy_not_count':j14.get('population_proxy_used_as_individual_count') is False and j18.get('population_proxy_used_as_individual_count') is False,'no_model_run':j14.get('model_run_performed_count')==0 and j18.get('model_run_performed_count')==0,'no_scientific_execution':cfg.get('scientific_engine_execution_performed') is False,'no_target_numeric':cfg.get('target_numeric_execution_performed') is False,'no_readjudication':cfg.get('readjudication_performed') is False,'canonical_unchanged':cfg.get('canonical_state_changed') is False,'deep_off':cfg.get('deep_biological_coupling') is False,'r437_j21_binding_preserved':pa.get('j21_canonical_layer_binding_count')==596,'deferred_p2_two':pa.get('active_deferred_p2_cell_count')==2,'proxy_context_two':pa.get('proxy_context_only_count')==2,'p3_backlog_six':pa.get('p3_backlog_cell_count')==6}
    ok=all(checks.values())
    out={'stage':STAGE,'status':COMPLETE if ok else BLOCKED,'checks':checks,'checks_passed':sum(checks.values()),'checks_total':len(checks),'checks_failed':len(checks)-sum(checks.values()),'geonomics_version':'1.4.9','j14_replicate_pass_count':j14.get('replicate_pass_count'),'j18_replicate_pass_count':j18.get('replicate_pass_count'),'j14_branch_count':j14.get('branch_count'),'j18_branch_count':j18.get('branch_count'),'j14_carrier_count':j14.get('total_carrier_count'),'j18_carrier_count':j18.get('total_carrier_count'),'exact_initialization_adapter_validated':bool(ok),'construction_probe_elimination_validated':bool(ok),'orig_comm_reset_state_binding_validated':bool(ok),'canonical_carrier_state_installed_in_validation_models':bool(ok),'production_execution_state_materialized':False,'geonomics_execution_ready':False,'model_run_performed_count':0,'scientific_engine_execution_performed':False,'target_numeric_execution_performed':False,'readjudication_performed':False,'canonical_state_changed':False,'active_deferred_p2_cell_count':2,'proxy_context_only_count':2,'p3_backlog_cell_count':6,'next_action':NEXT if ok else 'REPAIR_R438_EXACT_INITIALIZATION_ADAPTER_PREFLIGHT'}
    write(root/OUT/'R4_38_INTEGRATED_AUDIT.json',out); return out


def final_seal(root:Path)->dict[str,Any]:
    root=root.resolve(); a=load(root/OUT/'R4_38_INTEGRATED_AUDIT.json'); j14=load(root/OUT/'R4_38_J14_EXACT_INITIALIZATION_ADAPTER_AUDIT.json'); j18=load(root/OUT/'R4_38_J18_EXACT_INITIALIZATION_ADAPTER_AUDIT.json')
    checks={'r438_complete':a.get('status')==COMPLETE and a.get('checks_failed')==0,'j14_adapter_4_of_4':j14.get('replicate_pass_count')==4,'j18_adapter_4_of_4':j18.get('replicate_pass_count')==4,'j14_all_192_branches':j14.get('branch_count')==192,'j18_all_64_branches':j18.get('branch_count')==64,'j14_854_carriers':j14.get('total_carrier_count')==854,'j18_319_carriers':j18.get('total_carrier_count')==319,'probe_elimination_validated':a.get('construction_probe_elimination_validated') is True,'orig_comm_reset_state_validated':a.get('orig_comm_reset_state_binding_validated') is True,'validation_models_only':a.get('canonical_carrier_state_installed_in_validation_models') is True and a.get('production_execution_state_materialized') is False,'population_proxy_nonliteral':j14.get('population_proxy_used_as_individual_count') is False and j18.get('population_proxy_used_as_individual_count') is False,'no_model_run':a.get('model_run_performed_count')==0,'no_scientific_execution':a.get('scientific_engine_execution_performed') is False,'no_target_numeric':a.get('target_numeric_execution_performed') is False,'no_readjudication':a.get('readjudication_performed') is False,'canonical_unchanged':a.get('canonical_state_changed') is False,'execution_not_ready':a.get('geonomics_execution_ready') is False,'deferred_p2_two':a.get('active_deferred_p2_cell_count')==2,'proxy_context_two':a.get('proxy_context_only_count')==2,'p3_backlog_six':a.get('p3_backlog_cell_count')==6,'next_r439':a.get('next_action')==NEXT}
    ok=all(checks.values())
    out={'stage':STAGE,'audit':'FINAL_GEONOMICS_EXACT_INITIALIZATION_ADAPTER_AND_CONSTRUCTION_PROBE_ELIMINATION_PREFLIGHT','status':SEALED if ok else BLOCKED,'verdict':'SEALED' if ok else 'BLOCKED','checks':checks,'checks_passed':sum(checks.values()),'checks_total':len(checks),'checks_failed':len(checks)-sum(checks.values()),'summary':{'j14_replicates':j14.get('replicate_pass_count'),'j18_replicates':j18.get('replicate_pass_count'),'j14_branches':j14.get('branch_count'),'j18_branches':j18.get('branch_count'),'j14_carriers':j14.get('total_carrier_count'),'j18_carriers':j18.get('total_carrier_count'),'exact_initialization_adapter_validated':a.get('exact_initialization_adapter_validated'),'construction_probe_elimination_validated':a.get('construction_probe_elimination_validated'),'production_execution_state_materialized':False,'geonomics_execution_ready':False,'scientific_engine_execution_performed':False,'canonical_state_changed':False,'deep_biological_coupling':False,'next_action':NEXT},'next_action':NEXT}
    write(root/SEAL,out); return out
