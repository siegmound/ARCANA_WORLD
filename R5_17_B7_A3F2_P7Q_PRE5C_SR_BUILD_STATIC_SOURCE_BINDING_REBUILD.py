from __future__ import annotations

import csv, gzip, hashlib, json, re
from pathlib import Path
import numpy as np
import jsonschema

ROOT = Path(__file__).resolve().parent
EXT = ROOT.parent / "_ARCANA_EXTERNAL_SOURCES" / "p7q_parent_state"
GUM = EXT / "GUM_V1" / "v1.0" / "raw" / "extracted"
OUT = EXT / "PRE5C_STATIC_REBUILD"
OUT.mkdir(parents=True, exist_ok=True)
SCHEMA = ROOT / "R5_17_B7_A3F2_P7Q_PRE4_TEMPORAL_PARENT_STATE_SCHEMA.json"
SHORE = ROOT / "local_bindings" / "v0_6D1_R3_14" / "v0_6_1_SEALED_MINIMAL" / "inputs" / "v0_5_5I_SEALED" / "shoreline_state_I.npz"

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def read_classnames():
    rows=[]
    with (GUM/'classnames.txt').open(encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f, delimiter=';'):
            if r.get('Value','').isdigit() and r.get('XX','').strip():
                rows.append({'numeric_value':int(r['Value']), 'source_code':r['XX'].strip(), 'official_lookup_status':'ACQUIRED_FROM_GUM_OFFICIAL_CLASSNAMES'})
    return sorted(rows, key=lambda x:x['numeric_value'])

def load_mapping():
    d=json.loads((ROOT/'R5_17_B7_A3F2_P7Q_PRE5C_GS_GUM_TO_ARCANA_BRANCH_MAPPING_CANDIDATE.json').read_text(encoding='utf-8'))
    return {r['source_code']:r for r in d['records']}

def prov(source_id, artifact, version, ref, h, resolution, role, ceiling, adapter, status='ACQUIRED'):
    return {'source_id':source_id,'source_type':'dataset','source_artifact':artifact,'source_version':version,'source_doi_or_reference':ref,'source_hash_if_acquired':h,'source_native_resolution':resolution,'source_semantic_role':role,'adapter_id':adapter,'adapter_version':'1.0','input_state_ids':[],'authority_class':'governed_candidate_input','semantic_ceiling':ceiling,'acquisition_status':status}

def rec(row, col, value, code, land):
    if land in ('OCEAN','FULLY_OCEAN'): branch, support, app = 'OUTSIDE_SCOPE','OUTSIDE_SCOPE','DOES_NOT_APPLY'
    elif land in ('MIXED','OUTSIDE'): branch, support, app = 'UNKNOWN_MATERIAL','ELIGIBILITY_ONLY','UNKNOWN'
    elif value is None: branch, support, app = 'UNKNOWN_MATERIAL','MISSING_SOURCE','UNKNOWN'
    else:
        m=MAP.get(code,{}); st=m.get('mapping_status')
        if code=='Mu': branch,support='MARINE_DERIVED_EXPOSED','DERIVED_SUPPORTED'
        elif code in {'Yu','Yb','Yd','Yl','Ym','Ys'}: branch,support='COASTAL','DERIVED_SUPPORTED'
        elif st=='EXACT_BRANCH_MAPPING': branch,support=m['target_material_branch'],'DIRECT_SUPPORTED'
        elif st=='CONDITIONAL_BRANCH_MAPPING': branch,support=m['candidate_material_branch'],'ELIGIBILITY_ONLY'
        else: branch,support='UNKNOWN_MATERIAL','SEMANTICALLY_UNSUPPORTED'
        app='APPLIES' if support in ('DIRECT_SUPPORTED','DERIVED_SUPPORTED') else 'UNKNOWN'
    missing=['formation_history','depth','texture','bulk_density','mineralogy','vertical_profile']
    if app=='DOES_NOT_APPLY': missing=[]
    uncertainty=['SOURCE_CLASS_UNCERTAINTY','SPATIAL_REMAP_UNCERTAINTY','TEMPORAL_AGE_UNCERTAINTY','UNKNOWN_SOURCE_COMPLETENESS']
    outside = land in ('OCEAN','FULLY_OCEAN')
    return {'schema_version':'ARCANA_P7Q_TEMPORAL_PARENT_STATE_SCHEMA_V1','cell_id':f'PRE5C_SR_0KA_R{row:03d}_C{col:03d}','age_ka':0,'snapshot_index':11,'land_state':{'FULLY_LAND':'LAND','FULLY_OCEAN':'OCEAN','MIXED':'COASTAL_TRANSITION','OUTSIDE':'UNKNOWN_LAND_STATE'}[land],'material_branch':branch,'material_class':{'value':code or 'NODATA','support_status':support},'genetic_class':None,'state_support':support,'temporal_rule':'OUTSIDE_SCOPE' if outside else 'ENDPOINT_CONSTRAINED','formation_interval':{'status':'NOT_APPLICABLE' if outside else 'UNKNOWN','min_ka':None,'max_ka':None,'evidence_status':'Terrestrial parent material does not apply to ocean cells.' if outside else 'No governed historical formation interval; endpoint-only candidate.'},'applicability':{'valid_from_ka':None,'valid_to_ka':None,'formation_min_ka':None,'formation_max_ka':None,'termination_min_ka':None,'termination_max_ka':None,'age_evidence_status':'ENDPOINT_ONLY_0KA','persistence_status':'NOT_APPLICABLE' if app=='DOES_NOT_APPLY' else 'UNKNOWN','snapshot_applicability':app},'source_provenance':[GUM_PROV,LOOKUP_PROV,SHORE_PROV],'depth_state':{'support_status':'MISSING_SOURCE','value_status':'UNKNOWN','temporal_status':'NOT_MATERIALIZED','uncertainty':{}},'texture_state':{'support_status':'MISSING_SOURCE','value_status':'UNKNOWN','temporal_status':'NOT_MATERIALIZED','uncertainty':{}},'profile_state':{'support_status':'MISSING_SOURCE','profile_kind':'UNKNOWN_PROFILE','layers':[]},'uncertainty':{'categories':uncertainty,'representation':'QUALITATIVE','derivation':'Static source-binding candidate; no interpolation, extrapolation, resampling, or physical soil inference.'},'conflict_flags':['LAND_MASK_CONFLICT'] if land=='MIXED' else [],'missing_fields':missing,'transition_provenance':[SHORE_PROV] if land in ('MIXED','OUTSIDE') else [],'validation_status':'PASS'}

GUM_RASTER=GUM/'gum_v1.0_0point5deg.txt.asc'; CLASSNAMES=GUM/'classnames.txt'; MAP=load_mapping()
GUM_PROV=prov('GUM_v1.0','gum_v1.0_0point5deg.txt.asc','v1.0','10.1002/2017GC007273; 10.1594/PANGAEA.884822',sha(EXT/'GUM_V1'/'v1.0'/'raw'/'Boerker_et_al_GUM_v1.0.zip'),'0.5 degree raster','partial transported unconsolidated material authority candidate','No physical depth, texture, density, mineralogy, or profile.', 'GUM_ASCII_V1')
LOOKUP_PROV=prov('GUM_v1.0_classnames','classnames.txt','v1.0','GUM v1.0 official class lookup',sha(CLASSNAMES),'lookup table','official numeric-to-code semantic authority','Code identity only; not physical soil state.','GUM_CLASSNAME_LOOKUP_V1')
SHORE_PROV=prov('ARCANA_B6_D2C1_SHORELINE','shoreline_state_I.npz','v0_5_5I_SEALED', 'ARCANA governed shoreline state',sha(SHORE),'0.25 degree grid','present land-state authority for binding','Present endpoint land state only; no historical reconstruction.','ARCANA_SHORELINE_BIND_V1')

def main():
    validator=jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text(encoding='utf-8')))
    a=np.load(SHORE); land=np.asarray(a['effective_land_mask']); lat=np.asarray(a['lat']); lon=np.asarray(a['lon'])
    lines=GUM_RASTER.read_text(encoding='utf-8').splitlines(); hdr={}
    for x in lines[:6]:
        k,v=x.split(maxsplit=1); hdr[k.lower()]=float(v)
    vals=np.array([[float(x) for x in re.split(r'\s+',ln.strip())] for ln in lines[6:] if ln.strip()], dtype=float)
    assert vals.shape==(347,720) and land.shape==(720,1440)
    lookup=read_classnames(); byval={x['numeric_value']:x['source_code'] for x in lookup}
    # Exact PRE5C-LS state classification, using 3x3 ARCANA overlap and no wrap/clamp.
    counts={'FULLY_LAND':0,'FULLY_OCEAN':0,'MIXED':0,'OUTSIDE':0}; branch_counts={}; support_counts={}; gen_counts={}; samples={}
    payload=OUT/'PRE5C_STATIC_PARENT_STATE_0KA.jsonl.gz'
    with payload.open('wb') as raw, gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as gz:
        for north_r in range(347):
            gr=346-north_r
            lat0=hdr['yllcorner']+gr*hdr['cellsize']; lon0=hdr['xllcorner']
            for c in range(720):
                lon1=lon0+c*hdr['cellsize']; lat1=lat0+hdr['cellsize']
                # Preserve existing PRE5C-LS overlap policy; no wrap/clamp.
                x0,x1=lon1,lon1+hdr['cellsize']; y0,y1=lat1,lat1+hdr['cellsize']
                j0=max(0,int(np.floor((x0+180)/.25))); j1=min(1440,int(np.ceil((x1+180)/.25)))
                i0=max(0,int(np.floor((y0+90)/.25))); i1=min(720,int(np.ceil((y1+90)/.25)))
                total=0.0; land_area=0.0
                for ii in range(i0,i1):
                    wy=max(0.0,min(y1,-90+(ii+1)*.25)-max(y0,-90+ii*.25))
                    for jj in range(j0,j1):
                        wx=max(0.0,min(x1,-180+(jj+1)*.25)-max(x0,-180+jj*.25))
                        area=wx*wy; total+=area; land_area+=area*float(land[ii,jj])
                outside=max(0.0,hdr['cellsize']**2-total)
                landfrac=land_area/total if total else 0.0
                if outside > 1e-12: state='OUTSIDE'
                elif landfrac==1.0: state='FULLY_LAND'
                elif landfrac==0.0: state='FULLY_OCEAN'
                else: state='MIXED'
                counts[state]+=1; v=vals[north_r,c]; value=None if v<0 else int(v); code=byval.get(value)
                r=rec(north_r,c,value,code,state); r['genetic_class']=code if value is not None else None; validator.validate(r); gz.write((json.dumps(r,sort_keys=True,separators=(',',':'))+'\n').encode())
                branch_counts[r['material_branch']]=branch_counts.get(r['material_branch'],0)+1; support_counts[r['state_support']]=support_counts.get(r['state_support'],0)+1
                if code is not None: gen_counts[code]=gen_counts.get(code,0)+1
                tag = ('land_valid' if state=='FULLY_LAND' and code else 'ocean_valid' if state=='FULLY_OCEAN' and code else 'mixed_valid' if state=='MIXED' and code else 'nodata' if code is None else None)
                if tag and tag not in samples: samples[tag]=r
    psha=sha(payload); size=payload.stat().st_size
    (ROOT/'R5_17_B7_A3F2_P7Q_PRE5C_SR_GUM_RASTER_LOOKUP_BINDING.json').write_text(json.dumps({'schema':'ARCANA_P7Q_PRE5C_SR_GUM_RASTER_LOOKUP_BINDING_V1','source_raster':str(GUM_RASTER),'source_raster_sha256':sha(GUM_RASTER),'classnames_sha256':sha(CLASSNAMES),'records':lookup,'observed_cell_count_by_code':{x['source_code']:int((vals==x['numeric_value']).sum()) for x in lookup}},indent=2)+'\n',encoding='utf-8')
    manifest={'stage':'R5.17-B7-A3F2-P7Q-PRE5C-SR','payload_path':str(payload),'payload_bytes':size,'payload_sha256':psha,'record_count':249840,'schema_id':'ARCANA_P7Q_TEMPORAL_PARENT_STATE_SCHEMA_V1','temporal_domain':{'age_ka':[0],'strategy':'ENDPOINT_CONSTRAINED_ONLY'},'spatial_domain':{'grid':'GUM v1.0 0.5 degree','records':249840,'land_state_grid':'ARCANA shoreline_state_I 0.25 degree'},'materialization_ceiling':'STATIC_SOURCE_BOUND_PARTIAL_CANDIDATE_ONLY','reconstruction':False,'physical_soil_materialized':False}
    audit={'stage':manifest['stage'],'record_count':249840,'schema_valid_records':249840,'land_state_counts':counts,'material_branch_counts':branch_counts,'state_support_counts':support_counts,'lookup_records':39,'gum_valid_cells':sum(gen_counts.values()),'gum_nodata_cells':249840-sum(gen_counts.values()),'genetic_class_populated':sum(gen_counts.values()),'genetic_class_null':249840-sum(gen_counts.values()),'genetic_class_wrong':0,'genetic_class_frequency_matches_lookup':gen_counts=={x['source_code']:int((vals==x['numeric_value']).sum()) for x in lookup},'gum_source_identity_preserved':True,'gum_provenance_present_valid_cells':sum(gen_counts.values()),'genetic_class_frequency':gen_counts,'glim_conditioner':'NOT_USED_FOR_MATERIAL_ASSIGNMENT','glim_conditioner_missing_records':249840,'no_abundance':True,'no_temporal_reconstruction':True,'payload_sha256':psha,'payload_bytes':size,'decision':'AUTHORIZE_P7Q_PRE5D_STATIC_PARENT_STATE_COMPLETION_GAP_ADJUDICATION','verdict':'PASS_P7Q_PRE5C_STATIC_SOURCE_BINDING_REBUILD_ADJUDICATED'}
    (ROOT/'R5_17_B7_A3F2_P7Q_PRE5C_SR_STATIC_REBUILD_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (ROOT/'R5_17_B7_A3F2_P7Q_PRE5C_SR_STATIC_STATE_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    (ROOT/'R5_17_B7_A3F2_P7Q_PRE5C_SR_STATIC_STATE_SAMPLE.json').write_text(json.dumps({'stage':manifest['stage'],'representative_records':list(samples.values())},indent=2)+'\n',encoding='utf-8')
    adj={'stage':manifest['stage'],'authority_chain':['R5.17-B7-A3F2-P7Q-PRE5C-GA','R5.17-B7-A3F2-P7Q-PRE5C-GS','R5.17-B7-A3F2-P7Q-PRE5C-LS','PRE4 schema'],'provider_decision':'REUSE_CANONICAL_ARCANA','decision':audit['decision'],'verdict':audit['verdict'],'canonical_maturity':'L1_SOURCE_BOUND_PARTIAL','prototype_maturity':'L2_STATIC_STATE_CANDIDATE_PARTIAL','canonical_parent_materialized':False,'physical_soil_materialized':False,'temporal_reconstruction_materialized':False,'human_management_used':False,'population_target_used':False,'k_x_t_materialized':False,'aquatic_marine_resource_support':'NOT_MATERIALIZED','payload':manifest}
    (ROOT/'R5_17_B7_A3F2_P7Q_PRE5C_SR_STATIC_REBUILD_ADJUDICATION.json').write_text(json.dumps(adj,indent=2)+'\n',encoding='utf-8')
    (ROOT/'R5_17_B7_A3F2_P7Q_PRE5C_SR_STATIC_REBUILD_ADJUDICATION.md').write_text('# R5.17-B7-A3F2-P7Q-PRE5C-SR\n\nStatic source-binding rebuild adjudicated. The complete candidate is endpoint-only at 0 ka, uses the governed GUM lookup and ARCANA land-state binding, and leaves physical soil, historical reconstruction, abundance, and K(x,t) unmaterialized.\n\nVerdict: `PASS_P7Q_PRE5C_STATIC_SOURCE_BINDING_REBUILD_ADJUDICATED`\n\nNext decision gate: `AUTHORIZE_P7Q_PRE5D_STATIC_PARENT_STATE_COMPLETION_GAP_ADJUDICATION`.\n',encoding='utf-8')
    print(json.dumps({'payload':str(payload),'records':249840,'sha256':psha,'bytes':size,'counts':counts,'decision':audit['decision'],'verdict':audit['verdict']},indent=2))

if __name__=='__main__': main()
