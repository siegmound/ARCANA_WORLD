from pathlib import Path
from collections import defaultdict
import hashlib, json, sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import rebased_natural_control_runtime_v0_6D1_R2_1 as m


def test_sealed_d3_speciation_gate_byte_hash():
    p=ROOT/'src/d3_speciation_gate_v0_6_3D3_0C.py'
    assert hashlib.sha256(p.read_bytes()).hexdigest()=='1927744f10e39c8c2af39b6e72799bef8b7b8466bea123d1aa28d38c812af028'


def test_cadence_requires_integer_nesting():
    m.validate_cadence(m.R21Config())
    try:
        m.validate_cadence(m.R21Config(macrostep_years=300000.0))
    except ValueError:
        pass
    else:
        raise AssertionError('non-nested external macrostep must fail closed')


def test_scipy_reproductive_components_matches_d3_semantics():
    cfg=m.R21Config()
    contact=np.zeros((4,4));td=np.zeros((4,4));ri=np.zeros((4,4));clock=np.zeros((4,4))
    # 0-1 remain reproductively connected; 2 is isolated from both; 3 is connected to 2.
    td[0,2]=td[2,0]=2.;ri[0,2]=ri[2,0]=.9;clock[0,2]=clock[2,0]=100000
    td[1,2]=td[2,1]=2.;ri[1,2]=ri[2,1]=.9;clock[1,2]=clock[2,1]=100000
    td[0,3]=td[3,0]=2.;ri[0,3]=ri[3,0]=.9;clock[0,3]=clock[3,0]=100000
    td[1,3]=td[3,1]=2.;ri[1,3]=ri[3,1]=.9;clock[1,3]=clock[3,1]=100000
    comps=m.reproductive_components_scipy(np.arange(4),contact,td,ri,clock,cfg)
    assert sorted(map(tuple,comps))==[(0,1),(2,3)]


def _synthetic_founder_fixture():
    cfg=m.R21Config();shape=(5,5);pop=np.zeros((2,*shape));pop[0].flat[:12]=.02;pop[1].flat[13:25]=.02
    meta={'R':{'relative_reproduction_rate':1.0,'thermal_niche_sigma_c':5.0,'aridity_niche_sigma':0.5}}
    sc=np.array([5.0,0.5/1.55,cfg.body_mass_scale]);va=np.zeros((2,3));va[:]=0.045*sc**2
    gen=np.array([5.,5.]);contact=np.zeros((2,2));td=np.array([[0.,2.],[2.,0.]])
    ri=np.array([[0.,.9],[.9,0.]]);clock=np.array([[0.,100000.],[100000.,0.]])
    cur=['R','R'];roots=['R','R'];ids=['R_C1','R_C2'];reg={'R':{'root_species_id':'R','guild_id':1,'birth_elapsed_year':0.}}
    return cfg,pop,meta,va,gen,contact,td,ri,clock,cur,roots,ids,reg


def test_founder_birth_requires_persistence_and_conserves_population():
    cfg,pop,meta,va,gen,contact,td,ri,clock,cur,roots,ids,reg=_synthetic_founder_fixture()
    counters=defaultdict(int);state={};total=float(pop.sum())
    for t in (0.,500000.):
        ev,state,_=m.maybe_speciate_founder(current_species=cur,root_species=roots,component_ids=ids,pop=pop,va=va,gen=gen,
            metadata=meta,contact=contact,td=td,ri=ri,clock=clock,registry=reg,child_counters=counters,
            elapsed_year=t,age_ma=210-t/1e6,founder_state=state,cfg=cfg)
        assert ev==[]
    ev,state,_=m.maybe_speciate_founder(current_species=cur,root_species=roots,component_ids=ids,pop=pop,va=va,gen=gen,
        metadata=meta,contact=contact,td=td,ri=ri,clock=clock,registry=reg,child_counters=counters,
        elapsed_year=1000000.,age_ma=209.,founder_state=state,cfg=cfg)
    assert len(ev)==1 and ev[0]['daughter_species_id']=='R_D01'
    assert set(cur)=={'R','R_D01'}
    assert abs(float(pop.sum())-total)<1e-15
    assert ev[0]['founder_viability']['gate_ready'] is True


def test_persistent_vicariance_fission_is_not_speciation():
    cfg=m.R21Config(persistent_vicariance_fission_enabled=True);pop=np.zeros((1,10,20));pop[0,1:4,1:5]=.02;pop[0,6:9,12:16]=.02;hab=np.ones_like(pop)
    state={};mature={}
    for t in (0.,500000.,1000000.,1500000.,2000000.):
        state,mature=m.update_vicariance_persistence(['R_C1'],pop,hab,['R'],t,state,cfg)
    assert 'R_C1' in mature
    out=m.apply_mature_fissions(component_ids=['R_C1'],root_species=['R'],current_species=['R'],guild=np.array([1],np.uint8),
        pop=pop,trait=np.zeros((1,3)),va=np.ones((1,3))*.01,gen=np.array([5.]),hab=hab,lat=np.arange(10.),lon=np.linspace(-180,171,20),
        ri_state={},clock_state={},mature=mature,persistence=state,elapsed_year=2000000.,age_ma=208.,cfg=cfg)
    ids,roots,cur,guild,pop2,tr,va,gen,ri,cl,events=out
    assert len(ids)==2 and set(cur)=={'R'}
    assert abs(float(pop2.sum())-.48)<1e-12
    assert events[0]['semantic_status']=='PERSISTENT_VICARIANCE_DEMOGRAPHIC_FRAGMENT_NOT_SPECIES'


def test_ordinary_extinction_requires_persistent_deterministic_nonviability():
    cfg=m.R21Config();pop=np.full((1,4,4),1e-6);cur=['R'];roots=['R'];ids=['R_C1'];gen=np.array([5.])
    meta={'R':{'relative_reproduction_rate':1.0}};reg={'R':{'root_species_id':'R','guild_id':1,'birth_elapsed_year':0.}}
    bas={'population':{'R':1.0},'occupied_cells':{'R':100},'opportunity':{'R':1.0},'elapsed_year':{'R':0.0}}
    st={};mature=[]
    for k,t in enumerate((2000000.,2500000.,3000000.,3500000.,4000000.)):
        pop[:] = 1e-6 * (0.95 ** k)
        mature,st,_=m.ordinary_extinction_update(current_species=cur,root_species=roots,component_ids=ids,pop=pop,gen=gen,
            metadata=meta,registry=reg,baselines=bas,opportunity={'R':0.001},elapsed_year=t,ext_state=st,cfg=cfg)
    assert mature==['R']


def test_macrostep_chunking_bit_exact_on_one_myr():
    common=np.load(ROOT/'references/v0_6D1_R2/WORLD1_210Ma_REBASELINE_COMMON_STATE_PARENT_R1.npz',allow_pickle=False)
    a1=np.load(ROOT/'references/v0_6D1_R2/A1_WORLD1_210_180_REFERENCE_v0_6D1_R2.npz',allow_pickle=False)
    meta=json.loads((ROOT/'references/v0_6D1_R2/D1_species_metadata_120.json').read_text())
    a=m.run(common,a1,meta,m.R21Config(end_age_ma=209.,macrostep_years=250000.))
    b=m.run(common,a1,meta,m.R21Config(end_age_ma=209.,macrostep_years=500000.))
    for k in ('population','trait','va','ri','clock'):
        assert np.array_equal(a[k],b[k])
    assert a['component_ids']==b['component_ids'] and a['component_species']==b['component_species'] and a['events']==b['events']


def test_no_global_random_rates_and_deep_off():
    assert m.R21_GLOBAL_SPECIATION_RATE is None
    assert m.R21_GLOBAL_EXTINCTION_RATE is None
    assert m.R21_DEEP_BIOLOGICAL_COUPLING_ENABLED is False
