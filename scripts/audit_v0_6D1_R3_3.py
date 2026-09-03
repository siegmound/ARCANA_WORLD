from pathlib import Path
import hashlib, json, sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import rebased_natural_control_runtime_v0_6D1_R3_3 as r33
checks=[]
def ck(name, ok, detail=None): checks.append({'check':name,'pass':bool(ok),'detail':detail})

src=(ROOT/'src/rebased_natural_control_runtime_v0_6D1_R3_3.py').read_text()
d3=ROOT/'references/v0_6D1_R2_1/d3_sealed/diversification_adequacy_v0_6_3D3_2B.py'
ck('stage_id_r3_3', r33.R3_STAGE_ID=='v0.6D1-R3.3')
ck('deep_biological_off', r33.R3_DEEP_BIOLOGICAL_COUPLING_ENABLED is False)
ck('d3_2b_hash_exact', hashlib.sha256(d3.read_bytes()).hexdigest()=='9c2338cd8904bd6f9972c253be375384f6ec57193b4e3f5acf404f1ef2f344b2')
ck('d3_migration_reused', 'd3b._migration_with_permeability' in src)
ck('d3_pair_metrics_reused', 'd3b._pair_metrics_extended' in src)
ck('d3_3a_gene_flow_reused', 'av.gene_flow_moment_mix' in src)
ck('d3_3a_homeostasis_final', src.find('av.gene_flow_moment_mix') < src.find('av.advance_nonflow_variance'))
ck('scipy_sparse_connected_components_reused', 'scipy.sparse.csgraph import connected_components' in src)
ck('no_global_merge_rate', 'merge_rate' not in src and 'coalescence_rate' not in src)
ck('same_species_gate_present', 'current_species[i]) != str(current_species[j])' in src)
ck('inverse_d3_exchange_gate_present', 'exchange > float(gate.maximum_effective_exchange_pressure)' in src)
ck('ri_reconnection_gate_present', 'ri[i, j]) < float(gate.minimum_intrinsic_RI)' in src)
ck('isolation_clock_reconnection_gate_present', 'clock[i, j]) < float(gate.minimum_effective_isolation_generations)' in src)
ck('coalescence_persistence_locked_to_vicariance', r33.R33Config().reconnection_persistence_min_years==r33.R33Config().vicariance_persistence_min_years)
ck('coalescence_check_locked_to_fission', r33.R33Config().reconnection_check_interval_years==r33.R33Config().deme_fission_check_interval_years)
ck('moment_pooling_second_moment_exact_formula', 'second_before = np.sum(masses[:, None] * (vars_ + means * means), axis=0)' in src)
ck('hard_va_ceiling_merge_gate', 'variance_ceiling_normalized' in src and 'max_normalized_va_after_pooling' in src)
ck('no_despeciation_semantics', 'NOT_DESPECIATION' in src)
ck('global_speciation_rate_absent', 'global_speciation_rate": None' in src)
ck('global_extinction_rate_absent', 'global_extinction_rate": None' in src)

rows=json.loads((ROOT/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text()); M={r['species_id']:r for r in rows}
cfg=r33.R33Config(end_age_ma=205.0)
for tag,sp,comp,fiss,coal in [('210_206',120,145,15,3),('210_205',120,147,18,4)]:
    dtag='validation_210_206' if tag=='210_206' else 'validation_210_205_final'
    stem='210_to_206p0Ma' if tag=='210_206' else '210_to_205p0Ma'
    sm=json.loads((ROOT/f'outputs/v0_6D1_R3_3/{dtag}/{stem}_summary.json').read_text())
    st=np.load(ROOT/f'outputs/v0_6D1_R3_3/{dtag}/{stem}_state.npz',allow_pickle=False)
    q=[]
    for i,s in enumerate(st['component_root_species'].astype(str)):
        m=M[s]; sc=np.array([m['thermal_niche_sigma_c'],max(m['aridity_niche_sigma']/1.55,1e-4),cfg.body_mass_scale]); q.extend((st['va'][i]/(sc*sc)).tolist())
    q=np.asarray(q)
    ck(f'{tag}_species',sm['species_count']==sp)
    ck(f'{tag}_components',sm['component_count']==comp)
    ck(f'{tag}_fissions',sm['event_counts'].get('deme_fission')==fiss)
    ck(f'{tag}_coalescences',sm['event_counts'].get('deme_coalescence')==coal)
    ck(f'{tag}_component_ledger',133+fiss-coal==comp)
    ck(f'{tag}_no_birth',sm['event_counts'].get('speciation',0)==0)
    ck(f'{tag}_no_extinction',sm['event_counts'].get('ordinary_background_extinction',0)==0)
    ck(f'{tag}_hard_va_ceiling',float(q.max())<=0.05+1e-12,float(q.max()))
    ck(f'{tag}_no_va_cap_saturation',int((q>=0.0495).sum())==0,int((q>=0.0495).sum()))
    coals=[e for e in sm['events'] if e['event']=='deme_coalescence']
    ck(f'{tag}_all_coalescences_same_species_semantics',all(e['semantic_status'].endswith('NOT_DESPECIATION') for e in coals))
    ck(f'{tag}_coalescence_population_closure',max([abs(e['population_conservation_error']) for e in coals] or [0.0])<1e-12)
    ck(f'{tag}_coalescence_first_moment_closure',max([abs(e['first_moment_conservation_max_abs']) for e in coals] or [0.0])<1e-10)
    ck(f'{tag}_coalescence_second_moment_closure',max([abs(e['second_moment_conservation_max_abs']) for e in coals] or [0.0])<1e-10)
    c=sm['gene_flow_closure']
    ck(f'{tag}_gene_flow_first_moment',c['first_moment_conservation_max_abs']<1e-9,c['first_moment_conservation_max_abs'])
    ck(f'{tag}_gene_flow_second_moment',c['second_moment_conservation_max_abs']<1e-8,c['second_moment_conservation_max_abs'])

status='PASS' if all(x['pass'] for x in checks) else 'FAIL'
out={'stage':'v0.6D1-R3.3','status':status,'checks':checks,'passed':sum(x['pass'] for x in checks),'total':len(checks)}
p=ROOT/'outputs/v0_6D1_R3_3/FORMAL_AUDIT_v0_6D1_R3_3.json'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if status=='PASS' else 1)
