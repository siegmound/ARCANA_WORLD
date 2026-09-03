from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import hashlib, json
import numpy as np

from . import r38_restartable_checkpoint as r38
from .segregation_potential_lifecycle import ReducedGeneticLifecycleState

STAGE='v0.6D1-R3.9'
PARENT_STAGE='v0.6D1-R3.8_SEALED'
PRE_CHA1_AGE_MA=66.0
PRE_CHA1_SCHEMA='ARCANA_R39_WORLD1_H0_PRE_CHA1_66MA_CHECKPOINT_V1'
EXPECTED_STEPS_150_TO_66=672
NOMINAL_K=r38.NOMINAL_K

@dataclass(frozen=True)
class R39Config(r38.R38Config):
    end_age_ma: float = PRE_CHA1_AGE_MA
    def __post_init__(self)->None:
        super().__post_init__()
        if abs(self.end_age_ma-PRE_CHA1_AGE_MA)>1e-12:
            raise ValueError('R3.9 governed production continuation is fixed to 150->66.0 Ma pre-CHA1')


def _sha256(path:Path)->str:
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()


def validate_r38_checkpoint_authority(root:Path)->dict[str,Any]:
    root=Path(root)
    auth=json.loads((root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_8.json').read_text(encoding='utf-8'))
    if auth.get('state')!='SEALED' or not auth.get('governance',{}).get('canonical_150ma_checkpoint_authorized'):
        raise RuntimeError('R3.9 requires sealed R3.8 150 Ma checkpoint authority')
    cp=auth['canonical_checkpoint']
    jp=root/cp['json']['path']; npzp=root/cp['npz']['path']
    if _sha256(jp)!=cp['json']['sha256'] or _sha256(npzp)!=cp['npz']['sha256']:
        raise RuntimeError('R3.8 checkpoint hash mismatch')
    st=r38.load_checkpoint(jp)
    return {'state':st,'json_path':jp,'npz_path':npzp,'json_sha256':cp['json']['sha256'],'npz_sha256':cp['npz']['sha256']}


def validate_cha1_exact_event_authority(root:Path)->dict[str,Any]:
    p=Path(root)/'outputs/CHA1_PULSE_REFERENCE_AUDIT_v0_6D.json'
    d=json.loads(p.read_text(encoding='utf-8'))
    if d.get('status')!='PASS_CHA1_EXACT_EVENT_TIME_PULSE_REFERENCE_AUDIT':
        raise RuntimeError('CHA-1 exact-event audit not authoritative')
    if d.get('exact_event_time_preferred') is not True:
        raise RuntimeError('CHA-1 exact event time not preferred')
    pre=np.asarray(d.get('pulse_before_impact_j',[]),float)
    if pre.shape!=(5,) or np.any(pre!=0.0):
        raise RuntimeError('CHA-1 pre-impact pulse must be exactly zero')
    if not float(d.get('pulse_at_impact_total_j',0.0))>0.0:
        raise RuntimeError('CHA-1 impact pulse missing')
    return {'path':p,'sha256':_sha256(p),'audit':d}


def _pair_rows(d):
    return r38._pair_dict_rows(d)

def _pair_from(rows):
    return r38._pair_dict_from_rows(rows)


def save_precha1_checkpoint(st:r38.R38RuntimeState,out_dir:Path,r38_authority:dict[str,Any],cha1_authority:dict[str,Any],cfg:R39Config)->dict[str,Any]:
    if abs(st.age_ma-PRE_CHA1_AGE_MA)>1e-12:
        raise ValueError('R3.9 PRE_CHA1 checkpoint must be exactly 66.0 Ma')
    out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    stem='WORLD1_H0_66Ma_PRE_CHA1_CANONICAL_CHECKPOINT_v0_6D1_R3_9'
    npzp=out_dir/f'{stem}.npz'; jp=out_dir/f'{stem}.json'
    np.savez_compressed(npzp,
        guild=st.guild,population=st.pop,trait=st.trait,va=st.va,generation_time=st.gen,
        current_accessible=st.current_accessible.astype(np.uint8),
        reduced_va_within=st.reduced_state.va_within,
        reduced_ancestry_covariance=st.reduced_state.ancestry_covariance,
        reduced_neutral_segregation_potential=st.reduced_state.neutral_segregation_potential,
        reduced_adaptive_coordinate=st.reduced_state.adaptive_coordinate,
        lat=np.asarray(st._lat,float),lon=np.asarray(st._lon,float))
    meta={
      'schema':PRE_CHA1_SCHEMA,'stage':STAGE,'parent_stage':PARENT_STAGE,'age_ma':float(st.age_ma),'event_side':'PRE_IMPACT_66P0_MINUS',
      'elapsed_year':float(st.elapsed_year),'r38_checkpoint_authority':{
         'json_sha256':r38_authority['json_sha256'],'npz_sha256':r38_authority['npz_sha256']},
      'cha1_exact_event_authority':{
         'sha256':cha1_authority['sha256'],'exact_event_time_ma':66.0,
         'pulse_before_impact_j':cha1_authority['audit']['pulse_before_impact_j'],
         'pulse_at_impact_total_j':cha1_authority['audit']['pulse_at_impact_total_j']},
      'nominal_reduced_order_reference':{'label':'K_CENTER','K_eff':NOMINAL_K,'semantic_role':'OPERATIONAL_REDUCED_ORDER_COORDINATE_REFERENCE_NOT_PHYSICAL_CONSTANT'},
      'component_ids':st.component_ids,'root_species':st.root_species,'current_species':st.current_species,
      'registry':st.registry,'child_counters':st.child_counters,'baselines':st.baselines,
      'ri_state':_pair_rows(st.ri_state),'clock_state':_pair_rows(st.clock_state),
      'ext_state':st.ext_state,'founder_state':st.founder_state,'vicariance_state':st.vicariance_state,
      'reconnection_state':_pair_rows(st.reconnection_state),'events':r38._jsonable(st.events),'snapshots':r38._jsonable(st.snapshots),
      'founder_stats_last':r38._jsonable(st.founder_stats_last),'gene_flow_closure':r38._jsonable(st.gene_flow_closure),
      'topology_remap_mass':st.topology_remap_mass,'initial_total_population':st.initial_total_population,
      'config':asdict(cfg),'npz_file':npzp.name,
      'governance':{
        'cha1_applied':False,'deep_biological_coupling':False,
        'ordinary_125kyr_continuation_ends_here':True,
        'next_operator_must_be_dedicated_cha1_high_resolution_event':True,
        'scalar_k_physical_constant_authorized':False,
        'mu_b_or_ceiling_change_authorized':False,
      }
    }
    jp.write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return {'json':str(jp),'npz':str(npzp),'json_sha256':_sha256(jp),'npz_sha256':_sha256(npzp)}


def load_precha1_checkpoint(json_path:Path)->r38.R38RuntimeState:
    jp=Path(json_path); m=json.loads(jp.read_text(encoding='utf-8'))
    if m.get('schema')!=PRE_CHA1_SCHEMA or m.get('stage')!=STAGE or m.get('event_side')!='PRE_IMPACT_66P0_MINUS':
        raise RuntimeError('R3.9 PRE_CHA1 checkpoint metadata mismatch')
    if abs(float(m['age_ma'])-66.0)>1e-12 or m.get('governance',{}).get('cha1_applied') is not False:
        raise RuntimeError('R3.9 checkpoint is not the 66.0 Ma pre-impact state')
    z=np.load(jp.parent/m['npz_file'],allow_pickle=False)
    st=r38.R38RuntimeState(
      age_ma=float(m['age_ma']),elapsed_year=float(m['elapsed_year']),component_ids=list(m['component_ids']),
      root_species=list(m['root_species']),current_species=list(m['current_species']),guild=z['guild'].astype(np.uint8),
      pop=z['population'].astype(float),trait=z['trait'].astype(float),va=z['va'].astype(float),gen=z['generation_time'].astype(float),
      registry={str(k):dict(v) for k,v in m['registry'].items()},child_counters={str(k):int(v) for k,v in m['child_counters'].items()},
      current_accessible=z['current_accessible'].astype(bool),baselines=m['baselines'],
      ri_state={k:float(v) for k,v in _pair_from(m['ri_state']).items()},clock_state={k:float(v) for k,v in _pair_from(m['clock_state']).items()},
      ext_state=m['ext_state'],founder_state=m['founder_state'],vicariance_state=m['vicariance_state'],
      reconnection_state={k:dict(v) for k,v in _pair_from(m['reconnection_state']).items()},events=list(m['events']),snapshots=list(m['snapshots']),
      founder_stats_last=list(m['founder_stats_last']),gene_flow_closure=dict(m['gene_flow_closure']),topology_remap_mass=float(m['topology_remap_mass']),
      initial_total_population=float(m['initial_total_population']),reduced_state=ReducedGeneticLifecycleState(
        z['reduced_va_within'].astype(float),z['reduced_ancestry_covariance'].astype(float),z['reduced_neutral_segregation_potential'].astype(float),z['reduced_adaptive_coordinate'].astype(float)))
    st._lat=z['lat'].astype(float); st._lon=z['lon'].astype(float)
    return st


def event_counts(st:r38.R38RuntimeState)->dict[str,int]:
    return r38._event_counts(st.events)
