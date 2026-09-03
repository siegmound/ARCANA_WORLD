from __future__ import annotations
import hashlib, json, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r37i_production_runtime import validate_promotion_seal, NOMINAL_K_REFERENCE
checks=[]
def check(name,cond,detail=None): checks.append({'name':name,'pass':bool(cond),'detail':detail})
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_path(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

seal_p=ROOT/'outputs/v0_6D1_R3_7I/PRODUCTION_PROMOTION_SEAL_v0_6D1_R3_7I.json'
review_p=ROOT/'outputs/v0_6D1_R3_7I/PRODUCTION_PROMOTION_REVIEW_v0_6D1_R3_7I.json'
smoke_p=ROOT/'local_runs/v0_6D1_R3_7I/210_to_209p0Ma_R3_7I_canonical.json'
hzip_p=ROOT/'reference_results/v0_6D1_R3_7H_REAL_PROMOTION_EVIDENCE/v0_6D1_R3_7H_uploaded_container.zip'
iout_p=ROOT/'reference_results/v0_6D1_R3_7H_REAL_PROMOTION_EVIDENCE/v0_6D1_R3_7I_post_seal_outputs.zip'
for p in [seal_p,review_p,smoke_p,hzip_p,iout_p]: check('exists_'+p.name,p.exists(),str(p))

try:
    seal=validate_promotion_seal(seal_p); seal_ok=True
except Exception as e:
    seal={}; seal_ok=False; seal_err=repr(e)
check('seal_validates',seal_ok,None if seal_ok else seal_err)
check('seal_sha_expected',seal_p.exists() and sha_path(seal_p)=='9fd95e1849b7df3d9a5021b457cda723daca760fc782eb0ea2a6199ba70e4c9d',sha_path(seal_p) if seal_p.exists() else None)
if review_p.exists():
    review=json.loads(review_p.read_text(encoding='utf-8'))
    check('review_38_of_38',review.get('checks_passed')==38 and review.get('check_count')==38,(review.get('checks_passed'),review.get('check_count')))
    check('review_promotion_eligible',review.get('promotion_eligible') is True,review.get('promotion_eligible'))
else: review={}

# Parent R3.7H package surface remains immutable.
parent=json.loads((ROOT/'PACKAGE_MANIFEST_v0_6D1_R3_7H.json').read_text(encoding='utf-8'))
bad=[]
for rec in parent['files']:
    p=ROOT/rec['path']; actual=sha_path(p) if p.exists() else None
    if actual!=rec['sha256']: bad.append({'path':rec['path'],'expected':rec['sha256'],'actual':actual})
check('parent_r37h_3405_files',len(parent['files'])==3405,len(parent['files']))
check('parent_r37h_all_unchanged',not bad,bad[:10])

# Repacked uploaded H evidence has different ZIP-container hash but exact sealed JSON content identity.
expected_json = seal.get('r37h_full_closed_loop_evidence',{}).get('json_sha256',{}) if seal_ok else {}
found={}
if hzip_p.exists():
    with zipfile.ZipFile(hzip_p) as z:
        for n in z.namelist():
            if not n.endswith('.json'): continue
            b=z.read(n); base=Path(n).name
            if base.endswith('summary.json'): found['summary']=sha_bytes(b)
            for lab in ('K_LOW','K_CENTER','K_HIGH'):
                if base.endswith(f'{lab}.json'): found[lab]=sha_bytes(b)
for key in ('summary','K_LOW','K_CENTER','K_HIGH'):
    check('sealed_json_identity_'+key,found.get(key)==expected_json.get(key),{'actual':found.get(key),'expected':expected_json.get(key)})
repacked_sha=sha_path(hzip_p) if hzip_p.exists() else None
sealed_source_zip=seal.get('r37h_full_closed_loop_evidence',{}).get('source_zip_sha256') if seal_ok else None
check('repacked_container_hash_recorded',repacked_sha=='3d223c68ae86a7e351f07a9b4e878c4509a836edb8188950e605d0be5c3dd2c3',repacked_sha)
check('sealed_original_container_hash_recorded',sealed_source_zip=='0a736ea6b1b35ecd92416c968b34a5830167890ad7bbae6efffc06778fcf2287',sealed_source_zip)
check('container_repack_is_not_false_byte_identity',repacked_sha!=sealed_source_zip,{'uploaded_repacked':repacked_sha,'sealed_source':sealed_source_zip})

if smoke_p.exists():
    smoke=json.loads(smoke_p.read_text(encoding='utf-8'))
    check('canonical_smoke_stage',smoke.get('stage')=='v0.6D1-R3.7I',smoke.get('stage'))
    check('canonical_smoke_binding_true',smoke.get('canonical_runtime_binding') is True,smoke.get('canonical_runtime_binding'))
    check('canonical_smoke_8_steps',smoke.get('biology_steps')==8,smoke.get('biology_steps'))
    check('canonical_smoke_zero_clipping',smoke.get('clipping_contacts')==0,smoke.get('clipping_contacts'))
    check('canonical_smoke_seal_hash_exact',smoke.get('promotion_seal_sha256')==sha_path(seal_p),smoke.get('promotion_seal_sha256'))
    check('canonical_smoke_nominal_k_exact',abs(float(smoke.get('nominal_reduced_order_reference',{}).get('K_eff'))-NOMINAL_K_REFERENCE)<=1e-12,smoke.get('nominal_reduced_order_reference'))
else: smoke={}

if seal_ok:
    auth=seal.get('authority',{})
    check('canonical_binding_authorized',auth.get('canonical_runtime_binding_authorized') is True,auth)
    check('gene_flow_variance_promoted',auth.get('segregation_aware_gene_flow_variance_authorized') is True,auth)
    check('coalescence_pooling_promoted',auth.get('segregation_aware_coalescence_pooling_authorized') is True,auth)
    check('scalar_k_still_not_physical_constant',auth.get('scalar_k_physical_constant_authorized') is False,auth)
    check('mu_b_ceiling_unchanged',auth.get('mu_b_or_ceiling_change_authorized') is False,auth)
    check('other_authorities_unchanged',auth.get('migration_selection_ri_speciation_paleogeography_authority_changed') is False,auth)
    sup=seal.get('supersession',{})
    check('legacy_gene_flow_variance_retired',sup.get('legacy_whole_trait_gene_flow_variance_production_authority')=='RETIRED_FOR_WORLD1_RUNTIME',sup)
    check('legacy_coalescence_variance_retired',sup.get('legacy_whole_trait_coalescence_variance_production_authority')=='RETIRED_FOR_WORLD1_RUNTIME',sup)

ok=all(c['pass'] for c in checks)
out={'schema':'ARCANA_R37I_SEALED_RELEASE_AUDIT_V1','stage':'v0.6D1-R3.7I','status':'PASS_R37I_CANONICAL_PRODUCTION_SEAL' if ok else 'FAIL_R37I_CANONICAL_PRODUCTION_SEAL','checks_passed':sum(c['pass'] for c in checks),'check_count':len(checks),'checks':checks,'sealed_state':'CANONICAL_SEGREGATION_AWARE_RUNTIME_PROMOTED','seal_sha256':sha_path(seal_p) if seal_p.exists() else None,'canonical_smoke_sha256':sha_path(smoke_p) if smoke_p.exists() else None}
outp=ROOT/'outputs/v0_6D1_R3_7I/FORMAL_AUDIT_v0_6D1_R3_7I_SEALED.json'; outp.write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'status':out['status'],'checks_passed':out['checks_passed'],'check_count':out['check_count'],'seal_sha256':out['seal_sha256']},indent=2))
raise SystemExit(0 if ok else 2)
