from pathlib import Path
import json, numpy as np, sys
ROOT=Path(__file__).resolve().parents[1]
O=ROOT/'outputs/v0_6D1_R2'
checks=[]
def ck(name,cond,detail=''):
    checks.append({'name':name,'pass':bool(cond),'detail':str(detail)})
raw=json.load(open(O/'H0_REBASED_210_180_250KYR_RAW_v0_6D1_R2.json'))
ep=json.load(open(O/'H0_REBASED_210_180_ENDPOINT_AUDIT_v0_6D1_R2.json'))
z=np.load(O/'H0_REBASED_210_180_250KYR_STATE_v0_6D1_R2.npz',allow_pickle=False)
ck('richness_120',len(set(z['component_species'].astype(str)))==120)
ck('HSG_025_absent','HSG_025' not in set(z['component_species'].astype(str)))
ck('population_matches_raw',abs(float(z['population'].sum())-raw['final_total_population'])<1e-9)
ck('A1_relative_error_below_1e_3',ep['global_relative_error_vs_A1']<1e-3,ep['global_relative_error_vs_A1'])
ck('speciation_ready_zero',ep['speciation_ready_pair_count']==0)
ck('max_trait_distance_below_gate',ep['max_trait_distance']<1.0,ep['max_trait_distance'])
ck('max_intrinsic_ri_below_gate',ep['max_intrinsic_ri']<0.65,ep['max_intrinsic_ri'])
ck('H0_deep_bio_off',json.load(open(ROOT/'configs/world1_rebased_natural_control_210_180_v0_6D1_R2.json'))['deep_biological_coupling'] is False)
source=(ROOT/'src/rebased_natural_control_runtime_v0_6D1_R2.py').read_text()
ck('no_random_speciation_rate','random_speciation' not in source and 'np.random' not in source)
ck('no_random_extinction_rate','random_extinction' not in source and 'np.random' not in source)
ck('birth_actuator_not_authorized','R2_SPECIATION_BIRTH_ACTUATOR_AUTHORIZED = False' in source)
conv=json.load(open(O/'RESOLUTION_CONVERGENCE_METRICS_v0_6D1_R2.json'))
ck('short_species_weighted_250_125_below_0p5pct',conv['short_210_205_250_vs_125_kyr']['species_total_abundance_weighted_l1']<0.005)
ck('micro_raster_explicitly_not_sealed',conv['interpretation']['micro_raster_status']=='NOT_SEALED')
topo=json.load(open(O/'TOPOLOGY_SWITCH_SENSITIVITY_v0_6D1_R2.json'))
ck('topology_sensitivity_weighted_below_0p5pct',max(topo['192.5']['species_weighted_l1_vs_195'],topo['197.5']['species_weighted_l1_vs_195'])<0.005)
res={'stage':'v0.6D1-R2','passed':sum(x['pass'] for x in checks),'total':len(checks),'verdict':'PASS' if all(x['pass'] for x in checks) else 'FAIL','checks':checks}
print(json.dumps(res,indent=2));sys.exit(0 if res['verdict']=='PASS' else 1)
