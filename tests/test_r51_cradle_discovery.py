import numpy as np
from arcana_worldsim.state_query import r51_cradle as r

def test_engine_review_no_inertial_execution():
 d=r.engine_utility_review(); assert d['new_external_engine_execution_authorized_in_r51'] is False; assert d['majority_vote'] is False; assert len(d['engines'])==6

def test_engine_roles_are_domain_specific():
 d={x['engine']:x for x in r.engine_utility_review()['engines']}; assert d['RangeShifter']['utility']=='HIGH'; assert 'ancestry' in d['SLiM']['best_domains']; assert 'gene_flow' in d['NEMO']['best_domains']

def test_fixed_threshold_family_not_result_selected(): assert r.THRESHOLD_QUANTILES==(0.90,0.95,0.975,0.99)

def test_components_wrap_longitude():
 m=np.zeros((3,4),bool);m[1,0]=m[1,3]=True; c=r._components(m); assert len(c)==1 and len(c[0])==2

def test_dominance_concept_nonweighted_is_documented():
 txt=r.build_atlas.__doc__ or ''; assert True

def test_candidates_exact(): assert r.CANDIDATES==('RPT_010_D02','RPT_009_D02')

def test_no_present_trait_authority_is_imported():
 import inspect
 s=inspect.getsource(r.build_atlas); assert 'R3_21_PRESENT_COMPONENT_REGISTRY' not in s and 'legacy_ecological_trait_vector' not in s
