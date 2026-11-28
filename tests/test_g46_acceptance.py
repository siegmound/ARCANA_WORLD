"""Test production acceptance predicates, including explicit forbidden promotions."""
import copy,sys
from pathlib import Path
import numpy as np
import pytest
P=Path(__file__).parents[1]/'experiments/r6_thermo_provider_pilot_v1';sys.path[:0]=[str(P),str(P/'g46_constrained_gauge_v1')]
import oracle
import restart
import scientific_design as design
import arcana_g46_campaign as c

def exact_mode():return dict(C_defect=0.,H_defect=0.,operator_relative=0.,divergence_operator_relative=0.,energy_relative=0.,forcing_compatibility_relative=0.)
def test_exact_gauge_gate_positive_and_non_null():
 assert oracle.exact_gauge_admission(exact_mode())
 x=exact_mode();x['energy_relative']=1e-8
 with pytest.raises(RuntimeError,match='NON_NULL'):oracle.exact_gauge_admission(x)
def test_incompatible_force_is_not_projected():
 x=exact_mode();x['forcing_compatibility_relative']=1e-5
 with pytest.raises(RuntimeError,match='INCOMPATIBLE_FORCING'):oracle.exact_gauge_admission(x)
def test_unconstrained_mode_rejected():
 x=exact_mode();x['H_defect']=3e-5
 with pytest.raises(RuntimeError,match='UNCONSTRAINED'):oracle.exact_gauge_admission(x)
def test_missing_operator_proof_rejected():
 x=exact_mode();del x['operator_relative']
 with pytest.raises(RuntimeError,match='MISSING_FINITE'):oracle.exact_gauge_admission(x)
def test_constraint_empty_rows_and_closure():
 C,ids,lift=oracle.constraint(np.array([[1,-1,0],[2,-1,0],[2,0,.25],[2,3,.75]]),np.arange(4))
 assert np.array_equal(ids,[0,3]);assert np.allclose(C@np.array([4.,8.]),[4.,0.,7.,8.])
 with pytest.raises(RuntimeError,match='NOT_CLOSED'):oracle.constraint(np.array([[1,-1,0],[1,2,1],[2,-1,0],[2,0,1]]),np.arange(4))
def test_restart_clock_and_schema():
 x={'contract_sha256':c.PIN,'realization_sha256':restart.REALIZATION_PIN,'accepted_native_clock_increments':1,'serialized_time_s':.001,'next_step_s':.001,'files':{'native':'pin'}}
 restart.clock_gate(x,x['files']);bad=dict(x,serialized_time_s=.002)
 with pytest.raises(RuntimeError,match='CLOCK'):restart.clock_gate(bad,x['files'])
 with pytest.raises(RuntimeError,match='INVENTORY'):restart.clock_gate(x,{})
def test_g15_legacy_seed_and_predictor_exclusion():
 d=c.read(c.CODE/'g15_corrected_executable_contract.json');assert design.validate_g15(d)['execution_authorized'] is False
 bad=copy.deepcopy(d);bad['seed']['kind']='LEGACY_112YR'
 with pytest.raises(RuntimeError,match='CONTAMINATED'):design.validate_g15(bad)
 bad=copy.deepcopy(d);bad['predictor_in_accepted_energy_ledger']=True
 with pytest.raises(RuntimeError,match='PHYSICS_MASKS'):design.validate_g15(bad)
def test_no_physical_T0_assignments():
 d=c.read(c.CODE/'mantle_T0_decision_matrix.json');assert len(d['rows'])==10
 assert all(x['author_choice'] is None and x['assigned_value'] is None and not x['physical_admission'] for x in d['rows'])
 assert d['M01_engine_executions']==0 and d['additional_time_advance_years']==0
