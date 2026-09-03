from pathlib import Path
import hashlib, json, sys, tempfile
import numpy as np

from arcana_worldsim.scientific_engines.nemo242_r37c import R37CSelectionProtocol, r37c_exchange_matrix
from arcana_worldsim.scientific_engines.nemo242_r37c_r1 import (
    R37C_R1_STAGE, render_r37c_r1_phase_ini, selection_efficacy_metrics,
)

ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(name,cond): checks.append((name,bool(cond)))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

check('stage_identity',R37C_R1_STAGE=='v0.6D1-R3.7C-R1')
p=R37CSelectionProtocol()
check('parent_protocol_strengths_unchanged',p.selection_variances==(1.0,4.0))
check('parent_protocol_lengths_unchanged',(p.burnin_transitions,p.selected_transitions,p.reconnect_transitions)==(200,300,400))
check('parent_optimum_unchanged',p.optimum_amplitude==0.6)
check('parent_mutation_unchanged',p.mutation_rate==0.0)
check('parent_recombination_unchanged',p.recombination_rate==0.5)

with tempfile.TemporaryDirectory() as td:
    eff=np.linspace(.005,.02,8); freq=np.full((4,8),.5)
    m=render_r37c_r1_phase_ini(
        phase='FRAGMENTED_DIVERGENT_SELECTION',transitions=20,effect_a=eff,allele_frequencies=freq,
        population_size=500,seed=7,output_dir=td,chain_id='audit',selection_enabled=True,
        selection_variance=1.0,optimum_amplitude=.6,exchange_matrix=r37c_exchange_matrix('FRAGMENTED_DIVERGENT_SELECTION'))
    txt=(Path(td)/'Nemo2_ARCANA_R37C_R1.ini').read_text()
    check('selected_composite_lce','breed_selection_disperse    2' in txt)
    check('selected_no_standalone_viability','viability_selection' not in txt)
    check('selected_inherited_breed_disperse_matrix','breed_disperse_matrix' in txt)
    check('selected_quant_trait','selection_trait         quant' in txt)
    check('selected_gaussian','selection_model         gaussian' in txt)
    check('selected_absolute','selection_fitness_model absolute' in txt)
    check('selected_variance','selection_variance      1' in txt)
    check('selected_local_optima','selection_local_optima' in txt)
    check('selected_manifest_stage',m['stage']=='v0.6D1-R3.7C-R1')
    check('selected_no_auto_calibration',m['automatic_calibration_allowed'] is False)
    check('selected_no_production_auth',m['production_selection_mapping_authorized'] is False)

with tempfile.TemporaryDirectory() as td:
    eff=np.linspace(.005,.02,8); freq=np.full((4,8),.5)
    m=render_r37c_r1_phase_ini(
        phase='FRAGMENTED_MATCHED_NEUTRAL',transitions=20,effect_a=eff,allele_frequencies=freq,
        population_size=500,seed=7,output_dir=td,chain_id='audit',selection_enabled=False,
        selection_variance=None,optimum_amplitude=.6,exchange_matrix=r37c_exchange_matrix('FRAGMENTED_MATCHED_NEUTRAL'))
    txt=(Path(td)/'Nemo2_ARCANA_R37C_R1.ini').read_text()
    check('neutral_plain_breed_disperse','breed_disperse              2' in txt)
    check('neutral_no_composite','breed_selection_disperse' not in txt)
    check('neutral_no_selection_model','selection_model' not in txt)
    check('neutral_no_viability','viability_selection' not in txt)

fx=np.linspace(.005,.02,8); base=np.full((4,8),.5)
zero=selection_efficacy_metrics(fx,base,base.copy())
check('efficacy_rejects_identity',zero['selection_efficacy_gate_pass'] is False)
check('efficacy_identity_detected',zero['selected_neutral_frequency_state_exactly_identical'] is True)
sel=base.copy(); sel[:2]-=.05; sel[2:]+=.05
live=selection_efficacy_metrics(fx,sel,base)
check('efficacy_accepts_live_directional_response',live['selection_efficacy_gate_pass'] is True)
check('efficacy_positive_dz',live['adaptive_trait_divergence']>0)
check('efficacy_positive_S',live['adaptive_cross_group_S']>0)
check('efficacy_not_effect_size_calibration',live['gate_semantics']=='NUMERICAL_LIVENESS_ONLY__NOT_EFFECT_SIZE_CALIBRATION')

# Parent R3.7C source and test were restored to the original candidate hashes.
parent_restore={
 'src/arcana_worldsim/scientific_engines/nemo242_r37c.py':'a08ab1082c9d98e0c9f23be3d79440601e266b54b7cb9bb99a73c3fd1a4f1f80',
 'tests/test_r37c_directional_selection_oracle.py':'96304a28f03feb96f80f353d2cfada0ffdfc0d5bc71f361e9fa1b7fdb160f836',
}
for rel,h in parent_restore.items():
    q=ROOT/rel; check('parent_r37c_restored_'+Path(rel).name,q.is_file() and sha(q)==h)

# Earlier production/scientific authority remains untouched.
expected={
 'src/d3_additive_variance_v0_6_3D3_3A.py':'3b235b186e234f66a77443bec3a46c80ef699ecd715737be7d36103db01b4c21',
 'src/d3_paleogeographic_history_v0_6_3D3_2C.py':'5831f41ba9cd7bc05be0cd25f8cd84e895c6c9fa453bde7634d7b27c82394730',
 'src/rebased_natural_control_runtime_v0_6D1_R3_4.py':'087d05f532d84f53f8c99d08ae0099657792526eb3aa97bab7cb9e64cb342e45',
 'src/rebased_natural_control_runtime_v0_6D1_R3_5.py':'634237eb15383000e88180b890ead9b6facc281c0a77eb5ce00efe32f3d0bc95',
 'src/arcana_worldsim/scientific_engines/segregation_aware_admixture.py':'c08f206c3866f030c71b3d6cb08e6f5859a8ed1fe38fc6b34ff27bb4813c56ce',
 'src/arcana_worldsim/scientific_engines/segregation_potential_lifecycle.py':'efa5dd19a0db881f0f16f42613365aa65960309b0451d0126afc9c6d0da1d045',
 'src/arcana_worldsim/scientific_engines/neutral_reduced_lifecycle.py':'42c36728db6878db5d3c630475e5119cfd4e029fd3dc033e63be4dbc10dfdf5a',
 'src/arcana_worldsim/scientific_engines/r37b_shadow_binding.py':'c67e6eccbd172df0fa7506327bcbc39b20c6ff570bd71dc48b81eefe63154b7c',
}
for rel,h in expected.items():
    q=ROOT/rel; check('authority_hash_'+Path(rel).name,q.is_file() and sha(q)==h)

required=[
 'NEMO_COMPOSITE_SELECTION_LIFECYCLE_REPAIR_v0_6D1_R3_7C_R1.md',
 'NEMO_SELECTION_SOURCE_BINDING_AUDIT_v0_6D1_R3_7C_R1.md',
 'R3_7C_INVALID_SELECTION_EVIDENCE_AUDIT_v0_6D1_R3_7C_R1.md',
 'README_R3_7C_R1.md','V0_6D1_R3_7C_R1_STATUS.md','NEXT_STAGE_HANDOFF_v0_6D1_R3_7C_R1.md',
 'run_v0_6D1_R3_7C_R1_nemo_selection_wsl.ps1',
 'scripts/run_nemo_r37c_r1_selection_chain.py',
 'tests/test_r37c_r1_composite_selection_repair.py',
 'configs/world1_nemo_directional_selection_oracle_v0_6D1_R3_7C_R1.json',
 'outputs/v0_6D1_R3_7C_R1/R3_7C_INVALID_SELECTION_EVIDENCE_AUDIT.json',
 'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_7C_R1.json',
]
for rel in required: check('present_'+Path(rel).name,(ROOT/rel).is_file())

invalid=json.loads((ROOT/'outputs/v0_6D1_R3_7C_R1/R3_7C_INVALID_SELECTION_EVIDENCE_AUDIT.json').read_text())
check('invalid_parent_chain_count_16',invalid['chain_count']==16)
check('invalid_parent_pair_count_32',invalid['qfreq_pair_count']==32)
check('invalid_parent_all_32_identical',invalid['byte_identical_pair_count']==32)
check('invalid_parent_keff_not_authorized',invalid['K_eff_calibration_authorized'] is False)

cfg=json.loads((ROOT/'configs/world1_nemo_directional_selection_oracle_v0_6D1_R3_7C_R1.json').read_text())
check('config_composite_selected',cfg['selected_lifecycle_event']=='breed_selection_disperse')
check('config_absolute_selection',cfg['selection_fitness_model']=='absolute')
check('config_scalar_keff_false',cfg['scalar_K_eff_authorized'] is False)
check('config_runtime_binding_false',cfg['production_runtime_binding_authorized'] is False)
check('config_canonical_write_false',cfg['canonical_write_allowed'] is False)
check('no_r37c_r1_production_runtime',not (ROOT/'src/rebased_natural_control_runtime_v0_6D1_R3_7C_R1.py').exists())
runner=(ROOT/'scripts/run_nemo_r37c_r1_selection_chain.py').read_text()
check('runner_fail_closed_efficacy_status','INVALID_SELECTION_ORACLE_SELECTION_EFFICACY_GATE_FAILED' in runner)
check('runner_reports_efficacy_count','selection_efficacy_pass_count' in runner)
check('runner_uses_r1_renderer','render_r37c_r1_phase_ini' in runner)

for i,(n,ok) in enumerate(checks,1): print(f'{i:02d} {"PASS" if ok else "FAIL"} {n}')
passed=sum(ok for _,ok in checks)
verdict='PASS_COMPOSITE_SELECTION_REPAIR_AND_FAIL_CLOSED_EFFICACY_GATE__EXTERNAL_NEMO_SMOKE_PENDING'
summary={'stage':'v0.6D1-R3.7C-R1','passed':passed,'total':len(checks),'verdict':verdict,'checks':[{'name':n,'pass':ok} for n,ok in checks]}
out=ROOT/'outputs/v0_6D1_R3_7C_R1/FORMAL_AUDIT_v0_6D1_R3_7C_R1.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:summary[k] for k in ('stage','passed','total','verdict')},indent=2))
sys.exit(0 if passed==len(checks) else 2)
