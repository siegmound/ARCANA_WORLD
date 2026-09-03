from pathlib import Path
from collections import defaultdict
import json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import rebased_natural_control_runtime_v0_6D1_R2_1 as m
cfg=m.R21Config()
# Founder/speciation fixture
shape=(5,5);pop=np.zeros((2,*shape));pop[0].flat[:12]=.02;pop[1].flat[13:25]=.02
meta={'R':{'relative_reproduction_rate':1.0,'thermal_niche_sigma_c':5.0,'aridity_niche_sigma':0.5}}
sc=np.array([5.0,0.5/1.55,cfg.body_mass_scale]);va=np.zeros((2,3));va[:]=0.045*sc**2
gen=np.array([5.,5.]);contact=np.zeros((2,2));td=np.array([[0.,2.],[2.,0.]]);ri=np.array([[0.,.9],[.9,0.]]);clock=np.array([[0.,100000.],[100000.,0.]])
cur=['R','R'];roots=['R','R'];ids=['R_C1','R_C2'];reg={'R':{'root_species_id':'R','guild_id':1,'birth_elapsed_year':0.}};counter=defaultdict(int);fs={};timeline=[]
for t in (0.,500000.,1000000.):
 ev,fs,stats=m.maybe_speciate_founder(current_species=cur,root_species=roots,component_ids=ids,pop=pop,va=va,gen=gen,metadata=meta,contact=contact,td=td,ri=ri,clock=clock,registry=reg,child_counters=counter,elapsed_year=t,age_ma=210-t/1e6,founder_state=fs,cfg=cfg)
 timeline.append({'elapsed_year':t,'birth_count':len(ev),'species':list(cur),'active_founder_timers':len(fs)})
birth_event=ev[0]
# Vicariance fixture
cf=m.R21Config(persistent_vicariance_fission_enabled=True);pp=np.zeros((1,10,20));pp[0,1:4,1:5]=.02;pp[0,6:9,12:16]=.02;hab=np.ones_like(pp);vs={};mature={}
for t in (0.,500000.,1000000.,1500000.,2000000.):vs,mature=m.update_vicariance_persistence(['R_C1'],pp,hab,['R'],t,vs,cf)
out=m.apply_mature_fissions(component_ids=['R_C1'],root_species=['R'],current_species=['R'],guild=np.array([1],np.uint8),pop=pp,trait=np.zeros((1,3)),va=np.ones((1,3))*.01,gen=np.array([5.]),hab=hab,lat=np.arange(10.),lon=np.linspace(-180,171,20),ri_state={},clock_state={},mature=mature,persistence=vs,elapsed_year=2000000.,age_ma=208.,cfg=cf)
fission_event=out[-1][0]
# Extinction fixture
pe=np.full((1,4,4),1e-6);ereg={'R':{'root_species_id':'R','guild_id':1,'birth_elapsed_year':0.}};bas={'population':{'R':1.0},'occupied_cells':{'R':100},'opportunity':{'R':1.0},'elapsed_year':{'R':0.0}};es={};mature_ext=[]
for k,t in enumerate((2000000.,2500000.,3000000.,3500000.,4000000.)):
 pe[:]=1e-6*(.95**k);mature_ext,es,_=m.ordinary_extinction_update(current_species=['R'],root_species=['R'],component_ids=['R_C1'],pop=pe,gen=np.array([5.]),metadata={'R':{'relative_reproduction_rate':1.0}},registry=ereg,baselines=bas,opportunity={'R':.001},elapsed_year=t,ext_state=es,cfg=cfg)
res={'stage':'v0.6D1-R2.1','speciation':{'timeline':timeline,'event':birth_event,'pass':birth_event['daughter_species_id']=='R_D01' and birth_event['founder_viability']['gate_ready']},'fission':{'event':fission_event,'pass':fission_event['semantic_status']=='PERSISTENT_VICARIANCE_DEMOGRAPHIC_FRAGMENT_NOT_SPECIES'},'extinction':{'mature_species':mature_ext,'pass':mature_ext==['R']},'verdict':'PASS'}
(ROOT/'outputs/v0_6D1_R2_1/ACTUATOR_SYNTHETIC_AUDIT_v0_6D1_R2_1.json').write_text(json.dumps(res,indent=2,sort_keys=True));print(json.dumps(res,indent=2))
