from pathlib import Path
import hashlib,json,sys,tempfile
import numpy as np

from arcana_worldsim.scientific_engines.nemo242_r37c import (
    R37CSelectionProtocol,r37c_exchange_matrix,r37c_nemo_transition,r37c_local_optima,render_r37c_phase_ini,
)

ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(name,cond): checks.append((name,bool(cond)))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

p=R37CSelectionProtocol()
check('protocol_two_strengths',p.selection_variances==(1.0,4.0))
check('protocol_phase_lengths',(p.burnin_transitions,p.selected_transitions,p.reconnect_transitions)==(200,300,400))
check('optimum_amplitude_positive',p.optimum_amplitude==0.6)
check('mutation_disabled',p.mutation_rate==0.0)
check('free_recombination',p.recombination_rate==0.5)
for phase in ('COMMON_BURNIN','FRAGMENTED_DIVERGENT_SELECTION','FRAGMENTED_MATCHED_NEUTRAL','RECONNECTED_RELAXED'):
    t=r37c_nemo_transition(r37c_exchange_matrix(phase,p))
    check('transition_row_stochastic_'+phase,np.allclose(t.sum(axis=1),1,atol=1e-12,rtol=0))
    check('transition_column_stochastic_'+phase,np.allclose(t.sum(axis=0),1,atol=1e-12,rtol=0))
check('balanced_local_optima',np.allclose(r37c_local_optima(.6)[:,0],[-.6,-.6,.6,.6]))

with tempfile.TemporaryDirectory() as td:
    eff=np.linspace(.005,.02,8); freq=np.full((4,8),.5)
    m=render_r37c_phase_ini(phase='FRAGMENTED_DIVERGENT_SELECTION',transitions=20,effect_a=eff,allele_frequencies=freq,population_size=500,seed=7,output_dir=td,chain_id='audit',selection_enabled=True,selection_variance=1.0,optimum_amplitude=.6,exchange_matrix=r37c_exchange_matrix('FRAGMENTED_DIVERGENT_SELECTION'))
    txt=(Path(td)/'Nemo2_ARCANA_R37C.ini').read_text()
    check('renderer_viability_selection','viability_selection     2' in txt)
    check('renderer_quant_trait','selection_trait         quant' in txt)
    check('renderer_gaussian','selection_model         gaussian' in txt)
    check('renderer_relative_local','selection_fitness_model relative_local' in txt)
    check('renderer_selection_variance','selection_variance      1' in txt)
    check('renderer_local_optima','selection_local_optima' in txt)
    check('renderer_no_auto_calibration',m['automatic_calibration_allowed'] is False)
    check('renderer_no_production_auth',m['production_selection_mapping_authorized'] is False)

for fn in [
 'NEMO_DIRECTIONAL_SELECTION_ORACLE_PROTOCOL_v0_6D1_R3_7C.md',
 'SELECTION_PARTICIPATION_CALIBRATION_CONTRACT_v0_6D1_R3_7C.md',
 'NEMO_SELECTION_SOURCE_BINDING_AUDIT_v0_6D1_R3_7C.md',
 'V0_6D1_R3_7C_STATUS.md','NEXT_STAGE_HANDOFF_v0_6D1_R3_7C.md','README_R3_7C.md',
 'run_v0_6D1_R3_7C_nemo_selection_wsl.ps1','scripts/run_nemo_r37c_selection_chain.py',
 'scripts/analyze_nemo_r37c_selection_v0_6D1_R3_7C.py','src/arcana_worldsim/scientific_engines/r37c_validation.py',
 'configs/world1_nemo_directional_selection_oracle_v0_6D1_R3_7C.json']:
    check('present_'+fn,(ROOT/fn).is_file())

# Parent authority hashes from R3.7B candidate must remain unchanged.
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
    q=ROOT/rel; check('parent_hash_'+Path(rel).name,q.is_file() and sha(q)==h)

check('no_r37c_production_runtime',(ROOT/'src/rebased_natural_control_runtime_v0_6D1_R3_7C.py').exists() is False)
check('no_embedded_r37c_nemo_results',not (ROOT/'reference_results'/'v0_6D1_R3_7C_SELECTION').exists())
check('no_scalar_keff_config','effective_polygenic_dimension' not in (ROOT/'configs/world1_nemo_directional_selection_oracle_v0_6D1_R3_7C.json').read_text())

for i,(n,ok) in enumerate(checks,1): print(f'{i:02d} {"PASS" if ok else "FAIL"} {n}')
passed=sum(ok for _,ok in checks)
verdict='PASS_SELECTION_ORACLE_PROTOCOL_AND_BINDING__EXTERNAL_NEMO_SELECTION_EVIDENCE_PENDING'
summary={'stage':'v0.6D1-R3.7C','passed':passed,'total':len(checks),'verdict':verdict,'checks':[{'name':n,'pass':ok} for n,ok in checks]}
out=ROOT/'outputs'/'v0_6D1_R3_7C'/'FORMAL_AUDIT_v0_6D1_R3_7C.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:summary[k] for k in ('stage','passed','total','verdict')},indent=2))
sys.exit(0 if passed==len(checks) else 2)
