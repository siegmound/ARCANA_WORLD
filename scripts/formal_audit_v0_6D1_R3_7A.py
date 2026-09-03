from pathlib import Path
import hashlib, json, sys
import numpy as np
from arcana_worldsim.scientific_engines.r37a_validation import analyze_r37a_parent_reference
from arcana_worldsim.scientific_engines.segregation_potential_lifecycle import (
    initialize_minimum_information_state, reproductive_pair_authority_mask,
    mutation_supply_effect_on_segregation_potential, fission_clone_state,
    speciation_identity_transition, remap_identity_transition,
)
from arcana_worldsim.scientific_engines.nemo242_r37a import canonical_r37a_b2_phases, b2_nemo_transition

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'reference_results'/'v0_6D1_R3_6D_RAW_RESULTS.zip'
REF=analyze_r37a_parent_reference(RAW)
checks=[]
def check(name,cond): checks.append((name,bool(cond)))

check('raw_r36d_reference_present',RAW.is_file())
check('parent_nemo_reference_pass',REF['verdict'].startswith('PASS_PARENT_NEMO_DRIFT_REFERENCE'))
check('drift_reference_has_8_rows',REF['drift_reference']['row_count']==8)
check('drift_median_ratio_reasonable',0.7 < REF['drift_reference']['median_observed_over_prediction'] < 1.3)
check('drift_max_deviation_lt_30pct',REF['drift_reference']['max_abs_fractional_deviation'] < 0.30)
check('keff_reference_nontrivial',REF['polygenic_participation_reference']['minimum']>1)
check('keff_reference_below_or_near_literal_loci',REF['polygenic_participation_reference']['maximum']<=64.000001)
check('keff_not_auto_promoted',not REF['production_selection_mapping_authorized'])

v=np.full((3,2),0.045)
sid=np.array(['A','A','B'])
st,meta=initialize_minimum_information_state(v,sid)
check('minimum_information_initial_S_zero',np.max(np.abs(st.total_segregation_potential))==0)
check('hidden_genomics_not_invented',not meta['hidden_genomic_divergence_invented'])
mask=reproductive_pair_authority_mask(sid)
check('same_species_pair_authoritative',mask[0,1])
check('cross_species_pair_non_authoritative',not mask[0,2])
_,mutmeta=mutation_supply_effect_on_segregation_potential(st.neutral_segregation_potential)
check('mutation_has_no_invented_directional_S',mutmeta['deterministic_segregation_increment']==0.0)

fst,fmeta=fission_clone_state(st,0)
check('fission_adds_exact_clone',fst.deme_count==4 and np.max(np.abs(fst.total_segregation_potential[0,3]))==0)
check('fission_semantics_clone',fmeta['semantic_status']=='EXACT_CLONAL_LATENT_STATE_AT_FISSION_INSTANT')
_,sp,spmeta=speciation_identity_transition(st,['A','A','B'],[1],'A2')
check('speciation_changes_identity_only',sp==['A','A2','B'] and spmeta['genetic_state_reset'] is False)
_,rmeta=remap_identity_transition(st)
check('pure_remap_preserves_genetics',rmeta['genetic_state_changed'] is False)

ph=canonical_r37a_b2_phases()
check('b2_has_three_phases',[x.name for x in ph]==['CONNECTED_BURNIN','FRAGMENTED','RECONNECTED'])
check('b2_phase_generations',[x.transitions for x in ph]==[250,400,550])
for i,x in enumerate(ph):
    p=b2_nemo_transition(x.exchange_matrix)
    check(f'b2_phase_{i}_row_stochastic',np.allclose(p.sum(axis=1),1.0,atol=1e-12))
    check(f'b2_phase_{i}_symmetric',np.allclose(p,p.T,atol=1e-12))

for fn in ['SEGREGATION_POTENTIAL_LIFECYCLE_CONTRACT_v0_6D1_R3_7A.md','NEMO_B2_ISOLATION_RECONNECTION_PROTOCOL_v0_6D1_R3_7A.md','R3_7A_PARENT_NEMO_DRIFT_AND_POLYGENIC_SCALE_AUDIT.md','V0_6D1_R3_7A_STATUS.md','NEXT_STAGE_HANDOFF_v0_6D1_R3_7A.md']:
    check('document_'+fn,(ROOT/fn).is_file())
check('b2_runner_present',(ROOT/'run_v0_6D1_R3_7A_nemo_b2_wsl.ps1').is_file())
check('production_runtime_not_bound',not (ROOT/'src/rebased_natural_control_runtime_v0_6D1_R3_7A.py').exists())

expected={
 'src/d3_additive_variance_v0_6_3D3_3A.py':'3b235b186e234f66a77443bec3a46c80ef699ecd715737be7d36103db01b4c21',
 'src/d3_paleogeographic_history_v0_6_3D3_2C.py':'5831f41ba9cd7bc05be0cd25f8cd84e895c6c9fa453bde7634d7b27c82394730',
 'src/rebased_natural_control_runtime_v0_6D1_R3_4.py':'087d05f532d84f53f8c99d08ae0099657792526eb3aa97bab7cb9e64cb342e45',
 'src/rebased_natural_control_runtime_v0_6D1_R3_5.py':'634237eb15383000e88180b890ead9b6facc281c0a77eb5ce00efe32f3d0bc95',
}
for path,sha in expected.items():
    p=ROOT/path
    check('parent_hash_'+Path(path).name,p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==sha)

for i,(n,ok) in enumerate(checks,1): print(f'{i:02d} {"PASS" if ok else "FAIL"} {n}')
passed=sum(ok for _,ok in checks)
verdict='PASS_LIFECYCLE_ANALYTIC_AND_PARENT_NEMO_DRIFT_CLOSURE__NEMO_B2_CHAIN_CALIBRATION_PENDING'
print(json.dumps({'stage':'v0.6D1-R3.7A','passed':passed,'total':len(checks),'verdict':verdict},indent=2))
sys.exit(0 if passed==len(checks) else 2)
