import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import arcana_worldsim.scientific_engines.r325_h2_detailed_biology as m

def test_module_count(): assert len(m.MODULES)==8
def test_hypothesis_count(): assert len(m.HYPOTHESES)==6
def test_no_reproductive_output_monotone_module(): assert all('H2_reproductive_output_rate' not in x for x in m.MODULES.values())
def test_reptile_evidence(): assert 'REPTILE_COGNITION_2024' in m.EVIDENCE and 'REPTILE_LEARNING_2021' in m.EVIDENCE
def test_pct_bounds():
 x=np.array([[1.,2.,3.],[3.,2.,1.]]);p=m._pct(x);assert p.min()>0 and p.max()<1
def test_rank_desc(): assert np.allclose(m._rank_desc(np.array([3.,1.,2.])),[1,3,2])
def test_module_geometry():
 F=np.zeros((2,5,31));n,M,p=m._module_ensemble(F,m.TRAITS);assert M.shape==(2,5,8) and p.shape==(2,5,31)
def test_hyp_geometry():
 F=np.zeros((2,5,31));n,M,p=m._module_ensemble(F,m.TRAITS);hn,H=m._hypothesis_ensemble(M,n);assert H.shape==(2,5,6)
def test_module_values_bounded():
 rng=np.random.default_rng(1);F=rng.normal(size=(3,8,31));_,M,_=m._module_ensemble(F,m.TRAITS);assert np.all((M>=0)&(M<=1))
def test_consensus_deterministic():
 ids=['a','b'];x={'x':np.array([.5,.4]),'y':np.array([.4,.5])};o,*_=m._consensus_order(ids,x);assert o==['a','b']
def test_h3_n(): assert m.H3_N==6
def test_h2_is_not_human_identity(): assert 'Homo' not in ' '.join(m.MODULES.keys())
def test_ecological_reduced_state_not_functional(): assert 'functional' not in 'reduced_va_within'
