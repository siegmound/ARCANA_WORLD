from __future__ import annotations
import hashlib, io, json, sys, zipfile
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

def sha(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()
checks=[]
def ck(name,cond,detail=''):
    checks.append({'name':name,'pass':bool(cond),'detail':str(detail)})

parent=json.loads((ROOT/'PACKAGE_MANIFEST_v0_6D1_R3_7I.json').read_text())
mis=[]
for r in parent['files']:
    p=ROOT/r['path']
    if not p.exists() or sha(p)!=r['sha256']: mis.append(r['path'])
ck('parent_r37i_manifest_all_files_unchanged',not mis,f'{len(parent["files"])-len(mis)}/{len(parent["files"])}; mismatches={mis[:5]}')
ck('parent_r37i_release_state_sealed',parent.get('release_state')=='SEALED')
sealp=ROOT/'outputs/v0_6D1_R3_7I/PRODUCTION_PROMOTION_SEAL_v0_6D1_R3_7I.json'; seal=json.loads(sealp.read_text())
ck('promotion_seal_pass',seal.get('status')=='PASS_PRODUCTION_PROMOTION_SEAL')
ck('canonical_binding_authorized',seal['authority'].get('canonical_runtime_binding_authorized') is True)

run=ROOT/'local_runs/v0_6D1_R3_8'
sp=run/'R3_8_CHECKPOINT_VALIDATION_SUMMARY.json'
jp=run/'WORLD1_150Ma_CANONICAL_CONTINUATION_CHECKPOINT_v0_6D1_R3_8.json'
npzp=run/'WORLD1_150Ma_CANONICAL_CONTINUATION_CHECKPOINT_v0_6D1_R3_8.npz'
ck('full_summary_present',sp.exists()); ck('checkpoint_json_present',jp.exists()); ck('checkpoint_npz_present',npzp.exists())
summary=json.loads(sp.read_text()) if sp.exists() else {}
cp=json.loads(jp.read_text()) if jp.exists() else {}
ck('full_validation_verdict_pass',summary.get('verdict')=='PASS_CANONICAL_150MA_CHECKPOINT__R37I_EQUIVALENT__150_TO_149_RESTART_EXACT__POST_PROMOTION_CONTINUATION_READY',summary.get('verdict'))
ck('steps_210_150_exact',summary.get('biology_steps_210_to_150')==480)
ck('steps_direct_restart_exact',summary.get('biology_steps_150_to_149_direct')==8 and summary.get('biology_steps_150_to_149_restart')==8)
ck('r37i_equivalence_pass',summary.get('r37i_150ma_exposed_state_equivalence',{}).get('equivalent') is True)
ck('serialization_identity_pass',summary.get('checkpoint_serialization_identity',{}).get('equivalent') is True)
ck('restart_identity_pass',summary.get('restart_150_to_149_identity',{}).get('equivalent') is True)
ck('checkpoint_authorized_by_run',summary.get('governance',{}).get('canonical_150ma_checkpoint_authorized') is True)
ck('post150_authorized_by_run',summary.get('governance',{}).get('post_150_continuation_authorized') is True)
ck('deep_coupling_off',summary.get('governance',{}).get('deep_biological_coupling') is False)
ck('scalar_k_not_physical_constant',summary.get('governance',{}).get('scalar_k_physical_constant_authorized') is False)
ck('mu_b_ceiling_unchanged',summary.get('governance',{}).get('mu_b_or_ceiling_change_authorized') is False)
ck('checkpoint_json_hash_matches_summary',sha(jp)==summary.get('checkpoint',{}).get('json_sha256'),sha(jp))
ck('checkpoint_npz_hash_matches_summary',sha(npzp)==summary.get('checkpoint',{}).get('npz_sha256'),sha(npzp))
ck('checkpoint_age_exact_150',abs(float(cp.get('age_ma',-1))-150.0)<1e-12)
ck('checkpoint_parent_r37i',cp.get('parent_stage')=='v0.6D1-R3.7I')
ck('checkpoint_seal_hash_exact',cp.get('canonical_runtime_seal_sha256')==sha(sealp),cp.get('canonical_runtime_seal_sha256'))
ck('checkpoint_nominal_reference_center',cp.get('nominal_reduced_order_reference',{}).get('label')=='K_CENTER')

if npzp.exists():
    with np.load(npzp,allow_pickle=False) as a:
        required=['guild','population','trait','va','generation_time','current_accessible','reduced_va_within','reduced_ancestry_covariance','reduced_neutral_segregation_potential','reduced_adaptive_coordinate','lat','lon']
        ck('npz_required_arrays_complete',all(k in a.files for k in required),a.files)
        if all(k in a.files for k in required):
            n=a['population'].shape[0]
            ck('component_axis_consistent',n==len(cp.get('component_ids',[]))==454,(n,len(cp.get('component_ids',[]))))
            ck('spatial_tensor_shape',a['population'].shape==(454,90,180),a['population'].shape)
            ck('trait_va_gen_shapes',a['trait'].shape==(454,3) and a['va'].shape==(454,3) and a['generation_time'].shape==(454,), (a['trait'].shape,a['va'].shape,a['generation_time'].shape))
            ck('reduced_va_shape',a['reduced_va_within'].shape==(454,3),a['reduced_va_within'].shape)
            ck('ancestry_shape',a['reduced_ancestry_covariance'].shape==(454,3),a['reduced_ancestry_covariance'].shape)
            ck('S_shape',a['reduced_neutral_segregation_potential'].shape==(454,454,3),a['reduced_neutral_segregation_potential'].shape)
            ck('h_shape',a['reduced_adaptive_coordinate'].shape==(454,3),a['reduced_adaptive_coordinate'].shape)
            ck('all_numeric_arrays_finite',all(np.all(np.isfinite(a[k])) for k in required if a[k].dtype.kind in 'fc'))

# exact hidden state fields must be present in checkpoint metadata
for field in ['registry','child_counters','baselines','ri_state','clock_state','ext_state','founder_state','vicariance_state','reconnection_state','events','snapshots','founder_stats_last','gene_flow_closure']:
    ck('checkpoint_field_'+field,field in cp)

s150=summary.get('state_150_projection',{})
ck('state150_species_count',s150.get('species_count')==133,s150.get('species_count'))
ck('state150_component_count',s150.get('component_count')==454,s150.get('component_count'))
ck('state150_population_matches_sealed_center',abs(float(s150.get('final_total_population',0))-1940.1122015319092)<=2e-11,s150.get('final_total_population'))
ck('state150_zero_ceiling_issue',float(s150.get('q_max',1.0))<0.08,s150.get('q_max'))

passed=sum(x['pass'] for x in checks)
out={'stage':'v0.6D1-R3.8','release_state':'SEALED','verdict':'PASS_R38_CANONICAL_150MA_RESTART_BOUNDARY_SEALED__POST_150_CONTINUATION_AUTHORIZED' if passed==len(checks) else 'FAIL_R38_SEALED_AUDIT','checks_passed':passed,'check_count':len(checks),'checkpoint_json_sha256':sha(jp) if jp.exists() else None,'checkpoint_npz_sha256':sha(npzp) if npzp.exists() else None,'summary_sha256':sha(sp) if sp.exists() else None,'checks':checks}
op=ROOT/'outputs/v0_6D1_R3_8/FORMAL_AUDIT_SEALED_v0_6D1_R3_8.json'; op.parent.mkdir(parents=True,exist_ok=True); op.write_text(json.dumps(out,indent=2))
print(json.dumps({k:out[k] for k in ('stage','release_state','verdict','checks_passed','check_count','checkpoint_json_sha256','checkpoint_npz_sha256','summary_sha256')},indent=2))
if passed!=len(checks):
    for x in checks:
        if not x['pass']: print('FAIL',x['name'],x['detail'])
    raise SystemExit(2)
