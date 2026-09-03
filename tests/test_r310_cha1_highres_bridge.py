from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
from arcana_worldsim.scientific_engines import r310_cha1_highres_bridge as r


def _inputs():
 parent=r.validate_parent_r39_authority(ROOT)
 a1=np.load(ROOT/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz',allow_pickle=False)
 d=json.loads((ROOT/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text())
 md=d['species'] if isinstance(d,dict) and 'species' in d else d
 return parent,a1,md


def test_reporting_schedule_preserves_governed_event_window_and_count():
 t=r.reporting_schedule()
 assert len(t)==917
 assert t[0]==-100000.0 and t[-1]==500000.0
 assert np.count_nonzero(t==0.0)==1
 assert np.all(np.diff(t)>0)


def test_preimpact_forcing_is_exact_baseline_and_impact_anchor_is_exact():
 pre=r.physical_forcing(-0.1); impact=r.physical_forcing(0.0)
 assert pre['par_fraction']==1.0 and pre['npp_multiplier']==1.0
 assert pre['temperature_anomaly_c']==0.0 and pre['extinction_pressure_index']==0.0
 for k,v in r.PHYSICAL_ANCHORS['impact'].items():
  if k!='relative_year': assert abs(impact[k]-v)<=5e-13


def test_recovered_physical_anchors_close_at_machine_precision():
 a=r.physical_anchor_audit()
 assert a['impact_exact']
 assert max(a['max_relative_error_by_field'].values())<2e-12


def test_foodweb_minima_match_recovered_d22_oracle_without_using_r39_outcome():
 t=np.geomspace(.001,2000.0,4000); fw=r.foodweb_states(t)
 target=np.asarray([.395,.433,.782,.974])
 assert np.max(np.abs(fw.min(axis=0)-target))<5e-4
 assert np.max(np.abs(fw[-1]-1.0))<1e-5


def test_parent_is_exact_rebased_305_species_r39_boundary():
 parent,_,_=_inputs(); st=parent['state']
 assert st.age_ma==66.0
 assert len(set(st.current_species))==305
 assert abs(float(st.pop.sum())-1617.104703585379)<2e-10


def test_hazard_table_is_deterministic_and_guild_centered():
 parent,a1,md=_inputs(); cfg=r.R310Config()
 a=r.build_species_hazard_table(parent['state'],a1,md,cfg)
 b=r.build_species_hazard_table(parent['state'],a1,md,cfg)
 assert len(a)==305 and r.deterministic_hazard_identity(a,b)
 for g in range(1,7):
  vv=np.asarray([x['vulnerability'] for x in a if x['guild_id']==g])
  assert abs(float(np.mean(np.log(vv))))<2e-13


def test_canonical_bridge_regression_is_emergent_93_survivors():
 parent,a1,md=_inputs(); st,rep=r.run_event_bridge(parent['state'],a1,md,r.R310Config())
 assert rep['preimpact_species']==305
 assert rep['postimpact_survivor_species']==93
 assert rep['direct_cha1_extinctions']==212
 assert rep['postimpact_survivor_species']+rep['direct_cha1_extinctions']==305
 assert rep['extinction_time']['all_within_20_year_acute_window']
 assert st.age_ma==65.5


def test_bridge_does_not_reset_or_modify_surviving_genetic_coordinates():
 parent,a1,md=_inputs(); pre=parent['state']; post,_=r.run_event_bridge(pre,a1,md,r.R310Config())
 pos={cid:i for i,cid in enumerate(pre.component_ids)}
 for j,cid in enumerate(post.component_ids):
  i=pos[cid]
  assert np.array_equal(post.trait[j],pre.trait[i])
  assert np.array_equal(post.va[j],pre.va[i])
  assert np.array_equal(post.reduced_state.adaptive_coordinate[j],pre.reduced_state.adaptive_coordinate[i])


def test_post_event_population_and_segregation_invariants():
 parent,a1,md=_inputs(); st,rep=r.run_event_bridge(parent['state'],a1,md,r.R310Config())
 assert np.min(st.pop)>=0
 assert np.all(st.pop[:,~st.current_accessible]==0)
 assert abs(st.pop.sum()-rep['preimpact_total_population'])<2e-10
 s=st.reduced_state.neutral_segregation_potential
 assert np.max(np.abs(s-np.swapaxes(s,0,1)))<2e-12
 assert np.max(np.abs(np.diagonal(s,axis1=0,axis2=1)))<2e-12
 assert np.min(s)>=-2e-12


def test_serialization_identity(tmp_path:Path):
 parent,a1,md=_inputs(); st,rep=r.run_event_bridge(parent['state'],a1,md,r.R310Config())
 cp=r.save_postcha1_checkpoint(st,tmp_path,{k:v for k,v in parent.items() if k!='state'},r.R310Config(),rep)
 loaded=r.load_postcha1_checkpoint(Path(cp['json']))
 assert r38.compare_runtime_states(st,loaded)['equivalent']


def test_stronger_predeclared_hazard_never_increases_survivors():
 parent,a1,md=_inputs(); n=[]
 for scale in (.85,1.0,1.15):
  _,rep=r.run_event_bridge(parent['state'],a1,md,r.R310Config(guild_hazard_scale=scale))
  n.append(rep['postimpact_survivor_species'])
 assert n[0]>=n[1]>=n[2]


def test_fail_closed_governance_rejects_ordinary_or_deep_event_modes():
 with pytest.raises(ValueError): r.R310Config(deep_biological_coupling=True)
 with pytest.raises(ValueError): r.R310Config(ordinary_speciation_enabled=True)
 with pytest.raises(ValueError): r.R310Config(adaptive_radiation_enabled=True)
 with pytest.raises(ValueError): r.R310Config(impact_distance_mortality_enabled=True)
 with pytest.raises(ValueError): r.R310Config(post_event_years=499999.0)
