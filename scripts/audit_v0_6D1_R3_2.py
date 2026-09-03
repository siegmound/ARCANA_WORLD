from pathlib import Path
import hashlib, json, sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import rebased_natural_control_runtime_v0_6D1_R3_2 as r32
checks=[]
def ck(name, ok, detail=None): checks.append({'check':name,'pass':bool(ok),'detail':detail})

src=(ROOT/'src/rebased_natural_control_runtime_v0_6D1_R3_2.py').read_text()
d3=ROOT/'references/v0_6D1_R2_1/d3_sealed/diversification_adequacy_v0_6_3D3_2B.py'
ck('stage_id_r3_2', r32.R3_STAGE_ID=='v0.6D1-R3.2')
ck('deep_biological_off', r32.R3_DEEP_BIOLOGICAL_COUPLING_ENABLED is False)
ck('d3_2b_hash_exact', hashlib.sha256(d3.read_bytes()).hexdigest()=='9c2338cd8904bd6f9972c253be375384f6ec57193b4e3f5acf404f1ef2f344b2')
ck('d3_migration_reused', 'd3b._migration_with_permeability' in src)
ck('d3_pair_metrics_reused', 'd3b._pair_metrics_extended' in src)
ck('no_custom_vectorized_migration', '_migration_with_permeability_vectorized' not in src)
ck('same_permeability_for_migration_and_contact', src.count('connectivity_permeability') >= 2)
ck('d3_3a_gene_flow_reused', 'av.gene_flow_moment_mix' in src)
ck('d3_3a_homeostasis_final', src.find('av.gene_flow_moment_mix') < src.find('av.advance_nonflow_variance'))
ck('exchange_cap_45pct', 'maximum_total_exchange_fraction_per_deme=0.45' in src)
ck('vicariance_not_speciation', 'DEMOGRAPHIC_FRAGMENT_NOT_SPECIES' in src)
ck('global_speciation_rate_absent', 'global_speciation_rate": None' in src)
ck('global_extinction_rate_absent', 'global_extinction_rate": None' in src)

md=json.loads((ROOT/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text()); rows=md['species'] if isinstance(md,dict) and 'species' in md else md; M={r['species_id']:r for r in rows}
for tag,sp,comp,fiss in [('210_206',120,148,15),('210_205',120,151,18)]:
    sm=json.loads((ROOT/f'outputs/v0_6D1_R3_2/R3_2_{tag}_VALIDATION_SUMMARY.json').read_text())
    st=np.load(ROOT/f'outputs/v0_6D1_R3_2/R3_2_{tag}_VALIDATION_STATE.npz',allow_pickle=False)
    q=[]
    for i,s in enumerate(st['component_root_species'].astype(str)):
        m=M[s]; sc=np.array([m['thermal_niche_sigma_c'],max(m['aridity_niche_sigma']/1.55,1e-4),5.0]); q.extend((st['va'][i]/(sc*sc)).tolist())
    q=np.asarray(q)
    ck(f'{tag}_species',sm['species_count']==sp)
    ck(f'{tag}_components',sm['component_count']==comp)
    ck(f'{tag}_fissions',sm['event_counts'].get('deme_fission')==fiss)
    ck(f'{tag}_no_birth',sm['event_counts'].get('speciation',0)==0)
    ck(f'{tag}_no_extinction',sm['event_counts'].get('ordinary_background_extinction',0)==0)
    ck(f'{tag}_hard_va_ceiling',float(q.max())<=0.05+1e-12,float(q.max()))
    ck(f'{tag}_no_va_cap_saturation',int((q>=0.0495).sum())==0,int((q>=0.0495).sum()))
    c=sm['gene_flow_closure']
    ck(f'{tag}_gene_flow_first_moment',c['first_moment_conservation_max_abs']<1e-9,c['first_moment_conservation_max_abs'])
    ck(f'{tag}_gene_flow_second_moment',c['second_moment_conservation_max_abs']<1e-8,c['second_moment_conservation_max_abs'])

status='PASS' if all(x['pass'] for x in checks) else 'FAIL'
out={'stage':'v0.6D1-R3.2','status':status,'checks':checks,'passed':sum(x['pass'] for x in checks),'total':len(checks)}
p=ROOT/'outputs/v0_6D1_R3_2/FORMAL_AUDIT_v0_6D1_R3_2.json'; p.write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if status=='PASS' else 1)
