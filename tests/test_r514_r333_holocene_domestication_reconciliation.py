from pathlib import Path
import copy, json
from arcana_worldsim.state_query.r514_r333_holocene_domestication_reconciliation import (
 run_reconciliation, r513_handoff_semantics_ok, r333_checkpoint_semantics_ok, r333_sensitivity_robust_non_emergence)

ROOT=Path(__file__).resolve().parents[1]

def test_real_r333_reconciliation_passes():
 out=run_reconciliation(ROOT,False)
 assert out['scientific_candidate_eligible'] is True
 assert out['failed']==[]

def test_checkpoint_agriculture_promotion_fails_closed():
 cp=json.loads((ROOT/'outputs/v0_6D1_R3_33/R3_33_FOOD_PRODUCTION_CHECKPOINT.json').read_text())
 assert r333_checkpoint_semantics_ok(cp)
 bad=copy.deepcopy(cp); bad['agriculture_materialized']=True
 assert not r333_checkpoint_semantics_ok(bad)

def test_r513_unique_identity_drift_fails_closed():
 h=json.loads((ROOT/'outputs/v0_6D1_R5_13/R5_13_0KA_SUBSISTENCE_REGIONAL_READINESS_RECONCILED_HANDOFF.json').read_text())
 assert r513_handoff_semantics_ok(h)
 bad=copy.deepcopy(h); bad['unique_human_identity_materialized']=True; bad['unique_human_identity']='RPT_010_D02'
 assert not r513_handoff_semantics_ok(bad)

def test_sensitivity_nonzero_domestication_drift_fails_closed():
 s=json.loads((ROOT/'outputs/v0_6D1_R3_33/R3_33_SENSITIVITY_AND_ROBUSTNESS.json').read_text())
 assert r333_sensitivity_robust_non_emergence(s)
 bad=copy.deepcopy(s); bad['variants'][0]['domestication_species_frequency']=[0.03125,0.0]
 assert not r333_sensitivity_robust_non_emergence(bad)
