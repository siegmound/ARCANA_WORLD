from pathlib import Path
import json, numpy as np, importlib.util, sys
ROOT=Path(__file__).resolve().parents[1]
O=ROOT/'outputs/v0_6D1_R2'
def loadmod():
 p=ROOT/'src/rebased_natural_control_runtime_v0_6D1_R2.py';s=importlib.util.spec_from_file_location('r2',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);return m

def test_canonical_output_richness_and_hsg025():
 z=np.load(O/'H0_REBASED_210_180_250KYR_STATE_v0_6D1_R2.npz',allow_pickle=False);s=set(z['component_species'].astype(str));assert len(s)==120;assert 'HSG_025' not in s

def test_endpoint_reference_error():
 d=json.load(open(O/'H0_REBASED_210_180_ENDPOINT_AUDIT_v0_6D1_R2.json'));assert d['global_relative_error_vs_A1']<1e-3;assert d['speciation_ready_pair_count']==0

def test_a1_reference_contains_exact_endpoints():
 z=np.load(ROOT/'references/v0_6D1_R2/A1_WORLD1_210_180_REFERENCE_v0_6D1_R2.npz',allow_pickle=False);assert np.array_equal(z['age_ma'],np.array([210.,180.],dtype=z['age_ma'].dtype))

def test_environment_topology_is_discrete():
 m=loadmod();a=np.load(ROOT/'references/v0_6D1_R2/A1_WORLD1_210_180_REFERENCE_v0_6D1_R2.npz',allow_pickle=False);e196=m.environment_at(196,a,195);e194=m.environment_at(194,a,195);assert e196['topology']=='210Ma';assert e194['topology']=='180Ma';assert not np.array_equal(e196['land'],e194['land'])

def test_conservative_component_partition():
 m=loadmod();c=np.load(ROOT/'references/v0_6D1_R2/WORLD1_210Ma_REBASELINE_COMMON_STATE_PARENT_R1.npz',allow_pickle=False);ids=[str(x) for x in c['species_id']];ci,cs,g,p=m.partition_components(ids,c['species_population'].astype(float),c['guild_id'].astype(int));reb=np.zeros_like(c['species_population'],dtype=float)
 for i,s in enumerate(cs):reb[ids.index(s)]+=p[i]
 assert np.allclose(reb,c['species_population'],rtol=0,atol=1e-12)

def test_resolution_qualification_is_not_raster_seal():
 d=json.load(open(O/'RESOLUTION_CONVERGENCE_METRICS_v0_6D1_R2.json'));assert d['interpretation']['micro_raster_status']=='NOT_SEALED';assert d['short_210_205_250_vs_125_kyr']['species_total_abundance_weighted_l1']<0.005

def test_topology_midpoint_not_driver():
 d=json.load(open(O/'TOPOLOGY_SWITCH_SENSITIVITY_v0_6D1_R2.json'));assert d['192.5']['species_weighted_l1_vs_195']<0.005;assert d['197.5']['species_weighted_l1_vs_195']<0.005
