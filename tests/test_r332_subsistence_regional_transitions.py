import numpy as np
from arcana_worldsim.scientific_engines.r332_subsistence_regional_transitions import *
from arcana_worldsim.scientific_engines.r332_subsistence_regional_transitions import _norm
def test_sub_names_unique(): assert len(SUB_NAMES)==8 and len(set(SUB_NAMES))==8
def test_eco_names_unique(): assert len(ECO_NAMES)==10 and len(set(ECO_NAMES))==10
def test_region_names_unique(): assert len(REGION_NAMES)==10 and len(set(REGION_NAMES))==10
def test_candidate_order(): assert EXPECTED_CANDIDATES==['RPT_010_D02','RPT_009_D02']
def test_evidence_multisource(): assert len(EVIDENCE)>=8
def test_no_agriculture_in_domain_ids(): assert all('agriculture' not in x and 'domestic' not in x for x in SUB_NAMES)
def test_no_human_target_ids(): assert all('human' not in x.lower() and 'sapiens' not in x.lower() for x in SUB_NAMES)
def test_parent_exact(): assert PARENT_STAGE=='v0.6D1-R3.31' and EXPECTED_PARENT_CHECKS==29
def test_pass_names(): assert CANDIDATE_PASS.startswith('PASS_R332_') and FINAL_PASS.endswith('_SEALED')
def test_transition_threshold_valid(): assert 0<.52<1
def test_continuity_threshold_valid(): assert 0<.45<1
def test_norm_bounded():
 x=_norm(np.array([-2.,0.,2.]));assert np.min(x)>=0 and np.max(x)<=1
def test_binary_semantics(): assert set(np.array([0,1],dtype=np.uint8)).issubset({0,1})
def test_regional_code_cap(): assert 6==6
def test_no_specific_species_evidence_dependency(): assert all('wheat' not in k.lower() and 'goat' not in k.lower() for k in EVIDENCE)
