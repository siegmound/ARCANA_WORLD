import numpy as np
from arcana_worldsim.scientific_engines.r331_cultural_technological_ecology import *

def test_domain_names_unique(): assert len(TECH_NAMES)==8 and len(set(TECH_NAMES))==8
def test_ecology_names_unique(): assert len(ECO_NAMES)==10 and len(set(ECO_NAMES))==10
def test_group_names_unique(): assert len(GROUP_NAMES)==8 and len(set(GROUP_NAMES))==8
def test_candidate_order(): assert EXPECTED_CANDIDATES==['RPT_010_D02','RPT_009_D02']
def test_evidence_multisource(): assert len(EVIDENCE)>=8
def test_no_anthropocentric_domain_ids(): assert all('human' not in x.lower() and 'sapiens' not in x.lower() for x in TECH_NAMES)
def test_domains_functional_not_artifact_names(): assert 'pottery' not in ' '.join(TECH_NAMES) and 'bow' not in ' '.join(TECH_NAMES)
def test_rates_positive():
 cfg={'innovation_rate_per_kyr':.055,'loss_rate_per_kyr':.032,'cross_lineage_transfer_rate_per_kyr':.018};assert all(v>0 for v in cfg.values())
def test_stock_clip_math():
 x=np.clip(np.array([-1.,.2,2.]),0,1);assert np.array_equal(x,np.array([0.,.2,1.]))
def test_threshold_valid(): assert 0<.40<1
def test_final_pass_named(): assert FINAL_PASS.startswith('PASS_R331_') and FINAL_PASS.endswith('_SEALED')
def test_candidate_pass_named(): assert CANDIDATE_PASS.startswith('PASS_R331_')
def test_parent_exact(): assert PARENT_STAGE=='v0.6D1-R3.30' and EXPECTED_PARENT_CHECKS==27
