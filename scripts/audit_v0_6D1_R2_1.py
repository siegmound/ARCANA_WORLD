from pathlib import Path
import hashlib,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'outputs/v0_6D1_R2_1'
checks=[]
def ck(name,cond,detail=''):checks.append({'name':name,'pass':bool(cond),'detail':str(detail)})
source=(ROOT/'src/rebased_natural_control_runtime_v0_6D1_R2_1.py').read_text()
sgp=ROOT/'src/d3_speciation_gate_v0_6_3D3_0C.py'
ck('sealed_D3_0C_hash_exact',hashlib.sha256(sgp.read_bytes()).hexdigest()=='1927744f10e39c8c2af39b6e72799bef8b7b8466bea123d1aa28d38c812af028')
ck('parent_R2_source_unmodified',hashlib.sha256((ROOT/'src/rebased_natural_control_runtime_v0_6D1_R2.py').read_bytes()).hexdigest()=='2a56552a0121c9a66d42357887bc8ecf18bf90f0063a7e9face002a21b205cb0')
ck('scipy_sparse_components_used','scipy.sparse.csgraph' in source and 'connected_components' in source)
ck('scipy_ndimage_parent_reused','r2._components_wrap' in source)
ck('scipy_ckdtree_parent_reused','r2.remap_to_land' in source)
ck('no_networkx_dependency','networkx' not in source.lower())
ck('no_random_speciation_rate','R21_GLOBAL_SPECIATION_RATE = None' in source and 'np.random' not in source)
ck('no_random_extinction_rate','R21_GLOBAL_EXTINCTION_RATE = None' in source and 'np.random' not in source)
ck('deep_bio_off','R21_DEEP_BIOLOGICAL_COUPLING_ENABLED = False' in source)
ck('root_vs_current_species_separated','component_root_species' in source and 'component_species' in source)
ck('speciation_actuator_authorized','R21_SPECIATION_BIRTH_ACTUATOR_AUTHORIZED = True' in source)
ck('fission_default_fail_closed','persistent_vicariance_fission_enabled: bool = False' in source)

raw=json.load(open(O/'H0_REBASED_210_180_R21_RAW.json'));ep=json.load(open(O/'H0_REBASED_210_180_R21_ENDPOINT_AUDIT.json'));z=np.load(O/'H0_REBASED_210_180_R21_STATE.npz',allow_pickle=False)
ck('full_H0_210_180_completed',abs(ep['end_age_ma']-180.)<1e-12)
ck('full_H0_richness_120',ep['final_species_richness']==120)
ck('HSG025_absent','HSG_025' not in set(z['component_species'].astype(str)))
ck('A1_global_error_below_1e_3',ep['global_relative_error_vs_A1']<1e-3,ep['global_relative_error_vs_A1'])
ck('full_H0_no_forced_birth',ep['speciation_event_count']==0)
ck('full_H0_no_forced_extinction',ep['ordinary_extinction_event_count']==0)
ck('full_H0_no_production_fission',ep['deme_fission_event_count']==0)
ck('gene_flow_first_moment_closure',ep['gene_flow_closure']['first_moment_conservation_max_abs']<1e-8,ep['gene_flow_closure'])
ck('gene_flow_second_moment_closure',ep['gene_flow_closure']['second_moment_conservation_max_abs']<1e-7,ep['gene_flow_closure'])

cad=json.load(open(O/'CADENCE_CLOSURE_AUDIT_v0_6D1_R2_1.json'))
ck('external_macrostep_bit_exact',all(cad['external_macrostep_bit_exact'].values()),cad['external_macrostep_bit_exact'])
ck('transport_refinement_species_l1_below_1e_3',cad['transport_125_vs_62p5']['species_total_abundance_weighted_l1']<1e-3,cad['transport_125_vs_62p5'])
ck('biology_refinement_species_l1_below_1e_3',cad['biology_125_transport62p5_vs_biology62p5_transport31p25']['species_total_abundance_weighted_l1']<1e-3,cad['biology_125_transport62p5_vs_biology62p5_transport31p25'])
act=json.load(open(O/'ACTUATOR_SYNTHETIC_AUDIT_v0_6D1_R2_1.json'))
ck('synthetic_speciation_pass',act['speciation']['pass'])
ck('founder_persistence_not_instant',act['speciation']['timeline'][0]['birth_count']==0 and act['speciation']['timeline'][1]['birth_count']==0 and act['speciation']['timeline'][2]['birth_count']==1)
ck('synthetic_fission_is_demographic',act['fission']['pass'])
ck('synthetic_extinction_pass',act['extinction']['pass'])
fs=json.load(open(O/'FISSION_ACTIVATION_SENSITIVITY_v0_6D1_R2_1.json'))
ck('fission_sensitivity_detected_underresolved_fragmentation',fs['vicariance_fission_on']['fission_event_count']==47,fs['vicariance_fission_on'])
ck('fission_production_default_zero',fs['production_default_off']['fission_event_count']==0)
res={'stage':'v0.6D1-R2.1','passed':sum(x['pass'] for x in checks),'total':len(checks),'verdict':'PASS' if all(x['pass'] for x in checks) else 'FAIL','checks':checks}
(O/'FORMAL_AUDIT_v0_6D1_R2_1.json').write_text(json.dumps(res,indent=2,sort_keys=True));print(json.dumps(res,indent=2));sys.exit(0 if res['verdict']=='PASS' else 1)
