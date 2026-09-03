from pathlib import Path
import hashlib, json, sys
import numpy as np

from arcana_worldsim.scientific_engines.r37b_validation import analyze_r37a_b2_neutral_closure
from arcana_worldsim.scientific_engines.neutral_reduced_lifecycle import advance_neutral_one_generation
from arcana_worldsim.scientific_engines.r37b_shadow_binding import advance_neutral_world_interval_shadow

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'reference_results'/'v0_6D1_R3_7A_B2'/'v0_6D1_R3_7A_B2_RESULTS.zip'
OUT=ROOT/'outputs'/'v0_6D1_R3_7B'/'NEMO_B2_NEUTRAL_LIFECYCLE_CLOSURE_v0_6D1_R3_7B.json'
checks=[]
def check(name,cond): checks.append((name,bool(cond)))

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

check('raw_b2_results_present',RAW.is_file())
check('raw_b2_results_sha256',RAW.is_file() and sha(RAW)=='1f3484703c2482781222fb0de80cea5f2c7354b5eadc7e35f204c7885168d292')
ref=analyze_r37a_b2_neutral_closure(RAW)
check('b2_neutral_closure_pass',ref['verdict']=='PASS_NEUTRAL_S_LIFECYCLE_SUPPORTED_BY_NEMO_B2')
check('b2_has_24_phase_observations',ref['phase_observation_count']==24)
check('b2_S_median_near_unity',0.90 < ref['S_observed_over_predicted']['median'] < 1.10)
check('b2_S_all_within_review_envelope',ref['S_observed_over_predicted']['minimum']>=0.5 and ref['S_observed_over_predicted']['maximum']<=1.5)
check('b2_VA_median_abs_error_lt_2pct',ref['VA_fractional_error']['median_abs']<0.02)
check('b2_VA_max_abs_error_lt_5pct',ref['VA_fractional_error']['maximum_abs']<0.05)
check('no_free_parameter_fitted',ref['free_calibration_parameter_fitted'] is False)
check('b2_selection_was_disabled',ref['selection_enabled_in_b2'] is False)
check('keff_not_authorized',ref['selection_participation_K_eff_authorized'] is False)
check('production_binding_not_authorized',ref['production_runtime_binding_authorized'] is False)
check('analysis_artifact_present',OUT.is_file())
if OUT.is_file():
    saved=json.loads(OUT.read_text())
    check('analysis_artifact_matches_verdict',saved['verdict']==ref['verdict'])
    check('analysis_artifact_matches_median',abs(saved['S_observed_over_predicted']['median']-ref['S_observed_over_predicted']['median'])<1e-15)
else:
    check('analysis_artifact_matches_verdict',False); check('analysis_artifact_matches_median',False)

# Analytic single-generation closure.
va=np.array([[0.04],[0.04]])
s=np.zeros((2,2,1)); p=np.eye(2)
one=advance_neutral_one_generation(va,s,p,1000.0)
check('one_generation_VA_retention_exact',np.allclose(one.va_within[:,0],0.04*(1-1/2000),atol=1e-15,rtol=0))
check('one_generation_S_drift_transfer_exact',abs(one.segregation_potential[0,1,0]-4e-5)<1e-15)
check('new_drift_coefficient_not_introduced',one.diagnostics['new_drift_coefficient_introduced'] is False)

# World-interval bridge is shadow-only and refuses selection authority.
v2,s2,meta=advance_neutral_world_interval_shadow(
    va,s,p,np.array([1000.,1000.]),np.array([5.,5.]),125000.0
)
check('shadow_canonical_write_forbidden',meta['canonical_write_allowed'] is False)
check('shadow_runtime_replacement_forbidden',meta['production_runtime_replacement_authorized'] is False)
check('shadow_selection_keff_not_authorized',meta['selection_K_eff_authorized'] is False)
check('shadow_reuses_d3_3a_drift',meta['drift_authority']=='D3_3A_EXPONENTIAL_RETENTION_REUSED')

# Parent authorities remain byte-identical.
expected={
 'src/d3_additive_variance_v0_6_3D3_3A.py':'3b235b186e234f66a77443bec3a46c80ef699ecd715737be7d36103db01b4c21',
 'src/d3_paleogeographic_history_v0_6_3D3_2C.py':'5831f41ba9cd7bc05be0cd25f8cd84e895c6c9fa453bde7634d7b27c82394730',
 'src/rebased_natural_control_runtime_v0_6D1_R3_4.py':'087d05f532d84f53f8c99d08ae0099657792526eb3aa97bab7cb9e64cb342e45',
 'src/rebased_natural_control_runtime_v0_6D1_R3_5.py':'634237eb15383000e88180b890ead9b6facc281c0a77eb5ce00efe32f3d0bc95',
 'src/arcana_worldsim/scientific_engines/segregation_aware_admixture.py':'c08f206c3866f030c71b3d6cb08e6f5859a8ed1fe38fc6b34ff27bb4813c56ce',
 'src/arcana_worldsim/scientific_engines/segregation_potential_lifecycle.py':'efa5dd19a0db881f0f16f42613365aa65960309b0451d0126afc9c6d0da1d045',
}
for rel,h in expected.items():
    q=ROOT/rel
    check('parent_hash_'+Path(rel).name,q.is_file() and sha(q)==h)

for fn in [
 'NEUTRAL_REDUCED_GENETIC_LIFECYCLE_CONTRACT_v0_6D1_R3_7B.md',
 'NEMO_B2_NEUTRAL_LIFECYCLE_EVIDENCE_AUDIT_v0_6D1_R3_7B.md',
 'R3_7B_SHADOW_RUNTIME_BINDING_CONTRACT_v0_6D1_R3_7B.md',
 'SELECTION_PARTICIPATION_CALIBRATION_GATE_v0_6D1_R3_7B.md',
 'V0_6D1_R3_7B_STATUS.md','NEXT_STAGE_HANDOFF_v0_6D1_R3_7B.md','README_R3_7B.md']:
    check('document_'+fn,(ROOT/fn).is_file())

check('no_production_r37b_runtime_replacement',not (ROOT/'src/rebased_natural_control_runtime_v0_6D1_R3_7B.py').exists())
check('neutral_lifecycle_source_present',(ROOT/'src/arcana_worldsim/scientific_engines/neutral_reduced_lifecycle.py').is_file())
check('shadow_binding_source_present',(ROOT/'src/arcana_worldsim/scientific_engines/r37b_shadow_binding.py').is_file())

for i,(name,ok) in enumerate(checks,1): print(f'{i:02d} {"PASS" if ok else "FAIL"} {name}')
passed=sum(ok for _,ok in checks)
verdict='PASS_NEUTRAL_LIFECYCLE_NEMO_B2_CLOSURE__SHADOW_BINDING_READY__SELECTION_CALIBRATION_PENDING'
summary={'stage':'v0.6D1-R3.7B','passed':passed,'total':len(checks),'verdict':verdict,'checks':[{'name':n,'pass':ok} for n,ok in checks]}
out=ROOT/'outputs'/'v0_6D1_R3_7B'/'FORMAL_AUDIT_v0_6D1_R3_7B.json'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({k:summary[k] for k in ('stage','passed','total','verdict')},indent=2))
sys.exit(0 if passed==len(checks) else 2)
