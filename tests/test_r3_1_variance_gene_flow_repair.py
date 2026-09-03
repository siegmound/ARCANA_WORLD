from pathlib import Path
import hashlib, sys, numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import d3_additive_variance_v0_6_3D3_3A as av
import rebased_natural_control_runtime_v0_6D1_R3 as r3

EXPECTED_AV_SHA='3b235b186e234f66a77443bec3a46c80ef699ecd715737be7d36103db01b4c21'

def test_reused_d3_3a_additive_variance_source_hash():
    p=ROOT/'src'/'d3_additive_variance_v0_6_3D3_3A.py'
    assert hashlib.sha256(p.read_bytes()).hexdigest()==EXPECTED_AV_SHA

def test_r3_1_stage_id():
    assert r3.R3_STAGE_ID=='v0.6D1-R3.1'

def test_gene_flow_then_homeostasis_restores_hard_ceiling():
    # Two same-root demes with widely separated means: moment mixing can increase within-deme VA.
    trait=np.array([[0.,0.,0.],[2.,0.,0.]],float)
    va=np.full((2,3),0.049,float)
    n=np.array([1.,1.])
    G=np.array([[0.,0.15],[0.15,0.]])
    ri=np.zeros((2,2))
    root_idx=np.array([0,0],np.int32)
    cfg=av.AdditiveVarianceConfig(
        mutation_variance_supply_normalized_per_myr=0.002,
        mutation_variance_ceiling_normalized=0.05,
        variance_homeostasis_enabled=True,
        nonlinear_stabilizing_variance_depletion_per_myr_per_q=0.9876543209876544,
        selection_variance_depletion_per_generation=2e-8,
        drift_individual_equivalents_per_population_unit=250_000_000.0,
        drift_min_effective_size=500.0,
        maximum_total_exchange_fraction_per_deme=0.45,
    )
    tm, vm, _=av.gene_flow_moment_mix(trait,va,n,G,ri,root_idx,cfg)
    assert vm[:,0].max()>0.05
    md={'X':{'thermal_niche_sigma_c':1.0,'aridity_niche_sigma':1.55}}
    target=np.array([[0.,0.],[0.,0.]])
    gen=np.array([5.,5.])
    vh,_=av.advance_nonflow_variance(vm,trait,target,n,gen,root_idx,['X'],md,1.0,125_000.,cfg)
    assert float(vh.max())<=0.05+1e-15

def test_root_index_groups_same_root():
    idx,ids=r3._root_index(['B','A','B','C'])
    assert ids==['A','B','C']
    assert idx.tolist()==[1,0,1,2]
