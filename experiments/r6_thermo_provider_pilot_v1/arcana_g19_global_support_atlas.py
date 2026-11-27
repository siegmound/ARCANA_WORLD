#!/usr/bin/env python3
"""G19 global source/support atlas. Read-only authority and incidence audit.
No new material assignment, ridge initialization, boundary choice, solve or T1.
G18R3 regional error is retained separately and cannot suppress this audit.
"""
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import subprocess
import traceback
import numpy as np
import arcana_c11a_assembly as a
import arcana_c11c_sensitivity as c

R3_PIN='f294108dc146f3507cd23a919ce28fd303e97b523ccafa0c7ab5e4a9f4e213f9'
R3_STATUS='G18R3_ADJUDICATION_OR_GLOBAL_PREFLIGHT_BLOCKED'
CLASSES=('CONTINENTAL_COLD_STABLE','CONTINENTAL_NORMAL','CONTINENTAL_HOT_EXTENDED',
         'OCEAN_POSITIVE_AGE_ADMITTED','UNRESOLVED_POSITIVE_AGE_OCEAN','ZERO_AGE_RIDGE')
EXPECTED=(7834,5143,1281,49362,1072,108)
ADMIT='ADMITTED_INITIALIZER_SUPPORT'

def cell_id(r,col):
    return f'R6G1D-R{int(r):03d}-C{int(col):03d}'

def csvfile(path,header,rows):
    with path.open('x',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(header); w.writerows(rows)

def atlas(root,out,c06,c09case,global_report):
    from arcana_worldsim.r6 import geological_source_t0_adapter as geo
    from arcana_worldsim.r6.pre_orbdata_runtime_package import FIELDS
    from experiments.shellset_regional_explore_v1 import build_case
    d12=c06.d12
    fields,part,mesh,members=c06.load_native(root)
    pins=geo.verify_manifests(root)
    raw=(root/d12.BOUNDARY_FILE).read_bytes()
    a.need(geo.gitblob(raw)==d12.BOUNDARY_BLOB,'BOUNDARY_SOURCE')
    boundary=json.loads(raw)
    selected=set(pins['field']['derived_fields']['oceanic_age']['selected_source_boundary_ids'])
    segments=boundary['segments']
    a.need(len(selected)==79 and len(segments)==1983 and
        boundary['parent_vector_partition_sha256']==c06.provider.PLATE_SHA,'BOUNDARY_LINEAGE')
    masks,ba=d12.classify(fields,segments,selected)
    d12.verified_membership(masks,c06.provider.source_index(root))
    shape=fields['physical_crust_domain_id'].shape
    a.need(shape==(180,360) and len(members)==64800,'CELL_GRID')
    dom=fields['physical_crust_domain_id']; age=fields['oceanic_lithosphere_age_ma']
    thermal=fields['continental_thermal_domain_id']
    grid=geo.reconstruct_plates(part,pins['plate_ids'])
    a.need(grid.shape==shape,'PLATE_GRID')
    cls=np.full(shape,-1,dtype=int)
    for i,k in enumerate(CLASSES):
        a.need(int(masks[k].sum())==EXPECTED[i] and np.all(cls[masks[k]]==-1),'CLASS_PARTITION')
        cls[masks[k]]=i
    a.need(np.all(cls>=0) and np.array_equal(masks[ADMIT],cls<4),'ADMISSION_PARTITION')
    for r,col in np.ndindex(shape):
        k=cell_id(r,col)
        a.need(set(members[k])==({CLASSES[cls[r,col]],ADMIT} if cls[r,col]<4 else {CLASSES[cls[r,col]]}),'CELL_MEMBERSHIP')
    # Boundary incidence uses the original D12 adjacency convention verbatim.
    incident=defaultdict(list); unresolved=defaultdict(list); ridge=defaultdict(list)
    boundary_rows=[]
    for seg in segments:
        x,y=d12.adjacent(seg['parent_grid_edge'],shape)
        bid=seg['boundary_id']; v=float(seg['relative_normal_velocity_m_per_year'])
        reason='OTHER'
        if bid in selected: reason='SELECTED_AGE_SOURCE'
        elif v>0 and dom[x]==dom[y]==1: reason='UNSELECTED_POSITIVE_NORMAL_OCEAN_OCEAN'
        for rc in (x,y):
            incident[rc].append(bid)
            if reason=='UNSELECTED_POSITIVE_NORMAL_OCEAN_OCEAN': unresolved[rc].append(bid)
            if reason=='SELECTED_AGE_SOURCE': ridge[rc].append(bid)
        boundary_rows.append((bid,cell_id(*x),cell_id(*y),int(grid[x]),int(grid[y]),v,reason))
    a.need(len(unresolved)==ba['unique_adjacent_ocean_cells']==1075 and
        sum(cls[rc]==5 for rc in unresolved)==ba['overlap_selected_ridge']==3 and
        sum(cls[rc]==4 for rc in unresolved)==1072,'BOUNDARY_EXCLUSION_REPLAY')
    csvfile(out/'BOUNDARY_CLASSIFICATION.csv',
        ('boundary_id','cell_a','cell_b','plate_a','plate_b','relative_normal_m_per_year','source_role'),boundary_rows)
    # Native parent face and canonical node IDs are exactly those used by C06.
    tri=np.asarray(mesh.triangles,dtype=int)
    parent=np.asarray(mesh.triangle_parent_face,dtype=int)
    fr=np.asarray(part['face_row'],dtype=int); fc=np.asarray(part['face_col'],dtype=int)
    fp=np.asarray(part['face_plate_id'],dtype=int)
    a.need(tri.shape==(128880,3) and parent.shape==(len(tri),) and
        parent.min()>=0 and parent.max()<len(fr)==len(fc)==len(fp)==64800,'PARENT_FACE_INVENTORY')
    a.need(len(set(zip(fr.tolist(),fc.tolist())))==64800 and
        np.all(grid[fr,fc]==fp) and np.array_equal(fp[parent],np.asarray(mesh.triangle_plate_id)),'FACE_PLATE_BINDING')
    N=len(mesh.vertices_lat_lon)
    a.need(N==64442 and tri.min()==1 and tri.max()==N,'NODE_INDEX')
    cells_for_node=[set() for _ in range(N)]
    triangles_for_cell=defaultdict(list)
    node_ids_for_cell=defaultdict(set)
    trows=[]
    for i,(nodes,face) in enumerate(zip(tri,parent,strict=True),1):
        r,col=int(fr[face]),int(fc[face]); k=cell_id(r,col); cl=int(cls[r,col])
        triangles_for_cell[k].append(i)
        for n in nodes:
            cells_for_node[n-1].add((r,col))
            if cl>=4: node_ids_for_cell[k].add(int(n))
        trows.append((i,k,int(fp[face]),int(dom[r,col]),CLASSES[cl],int(cl<4)))
    a.need(len(triangles_for_cell)==64800,'FACE_COVERAGE')
    csvfile(out/'GLOBAL_TRIANGLE_SUPPORT.csv',
        ('triangle_id','parent_cell_id','plate_id','crust_domain_id','D12_class','D12_admitted'),trows)
    excluded=[]
    for r,col in np.argwhere(cls>=4):
        rc=(int(r),int(col)); k=cell_id(*rc); cl=int(cls[rc])
        a.need(cl==5 or unresolved[rc],'UNRESOLVED_CAUSE_BINDING')
        excluded.append({'cell_id':k,'row':rc[0],'column':rc[1],'plate_id':int(grid[rc]),
            'crust_domain_id':int(dom[rc]),'physical_ocean_age_Ma':float(age[rc]),
            'D12_class':CLASSES[cl],'boundary_ids':sorted(incident[rc]),
            'unselected_positive_normal_boundary_ids':sorted(unresolved[rc]),
            'selected_age_source_boundary_ids':sorted(ridge[rc]),
            'triangle_ids':triangles_for_cell[k],'node_ids':sorted(node_ids_for_cell[k]),
            'material_assignment':None,'physical_admission':False})
    a.need(len(excluded)==1180,'EXCLUDED_INVENTORY')
    a.write(out/'EXCLUDED_CELL_ATLAS.json',excluded)
    # Read numerical PRE independently. Never use PRE presence as admission.
    pre=root/(build_case.PRE+'.dat')
    a.need(a.sha(pre)==global_report['source_PRE_sha256'],'PRE_PIN')
    with pre.open() as f:
        head=f.readline().split()
        a.need(int(head[-1])==N,'PRE_HEADER')
        rows=np.loadtxt(f)
    a.need(rows.shape==(N,len(FIELDS)) and np.isfinite(rows).all() and
        np.array_equal(rows[:,0],np.arange(1,N+1)),'PRE_INVENTORY')
    idx={v:i for i,v in enumerate(FIELDS)}
    counts=Counter(); support_counts=Counter(); branch_counts=Counter(); domain_counts=Counter()
    mixed=0; nrows=[]; by_domain=defaultdict(Counter)
    for j,rcs in enumerate(cells_for_node,1):
        a.need(bool(rcs),'NODE_NO_SOURCE')
        row=rows[j-1]
        owner=(int(row[idx['owner_row']]),int(row[idx['owner_column']]))
        owner_domain=int(row[idx['owner_domain_id']])
        a.need(owner in rcs and int(dom[owner])==owner_domain,'PRE_OWNER_BINDING:'+str(j))
        ds={int(dom[rc]) for rc in rcs}; ps={int(grid[rc]) for rc in rcs}
        a.need(int(row[idx['incident_domain_mask']])==sum(1<<(x-1) for x in ds)
            and bool(row[idx['mixed_support']])==(len(ds)>1),'PRE_DOMAIN_BINDING:'+str(j))
        bad=[rc for rc in rcs if cls[rc]>=4]
        support='ALL_ADMITTED' if not bad else 'ALL_EXCLUDED' if len(bad)==len(rcs) else 'PARTIAL_EXCLUDED'
        if len(ds)>1 or len(ps)>1: conditional='MIXED_OR_CONFLICTING_SUPPORT'
        elif bad: conditional='UNKNOWN'
        else: conditional='SOURCE_DERIVED_CONDITIONAL'
        counts[support]+=1; support_counts[conditional]+=1
        branch=int(row[idx['runtime_branch_code']]); branch_counts[branch]+=1; domain_counts[owner_domain]+=1
        mixed+=int(len(ds)>1)
        by_domain[owner_domain][support]+=1
        nrows.append((j,cell_id(*owner),owner_domain,branch,len(rcs),len(ds),len(ps),len(bad),
            int(cls[owner]<4),support,conditional,'UNASSIGNED',
            ';'.join(cell_id(*rc) for rc in sorted(bad))))
    a.need(dict(branch_counts)=={int(k):v for k,v in global_report['PRE_branch_counts'].items()}
        and dict(domain_counts)=={int(k):v for k,v in global_report['owner_domain_counts'].items()}
        and mixed==global_report['mixed_PRE_owner_records'],'PRE_COUNTS_REPLAY')
    csvfile(out/'GLOBAL_NODAL_SUPPORT.csv',
        ('node_id','PRE_owner_cell','PRE_owner_domain','PRE_branch','incident_cells','incident_domains',
         'incident_plates','excluded_incident_cells','PRE_owner_admitted','D12_incident_support',
         'conditional_support_status','constitutive_assignment','excluded_cell_ids'),nrows)
    # Distinguish domain topology from actually authorized material constants.
    domains=[]
    for d in range(1,7):
        m=dom==d
        domains.append({'domain_id':d,'name':geo.DOMAINS[d],'cells':int(m.sum()),
            'admitted_cells':int((m&masks[ADMIT]).sum()),'excluded_cells':int((m&~masks[ADMIT]).sum()),
            'PRE_owner_nodes':domain_counts[d],'node_incident_support':dict(by_domain[d]),
            'material_assignment':None,'global_rheology_admitted':False})
    return {'screen_pass':True,'D12_classes':dict(zip(CLASSES,EXPECTED)),
        'boundary_audit':ba,'excluded_cells':len(excluded),'excluded_parent_triangles':sum(len(x['triangle_ids']) for x in excluded),
        'nodes_incident_to_excluded_cells':N-counts['ALL_ADMITTED'],
        'node_D12_support_counts':dict(counts),'node_conditional_support_counts':dict(support_counts),
        'domains':domains,'material_assignments':0,'global_assembly_authorized':False,
        'global_solve_authorized':False,'global_constitutive_authority_complete':False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-global-support-audit',choices=[a.SCENARIO],required=True)
    args=ap.parse_args()
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c09_mechanical_case as c09case
    c06=c10.c09.c08.c07.c06
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    p=c10.OUT.with_name('R6_THERMO_G18R3_REFERENCE_AUDIT_NEW01')
    pm=c.verified(p,R3_PIN,R3_STATUS); prior=a.read(p/'G18R3_REPORT.json')
    a.need(pm['source_sha']==a.SHA and all(pm[k]==v for k,v in c.SCOPE.items()) and
        pm['C09_manifest_sha256']==c10.PIN and prior['global_preflight_pass'] and
        not prior['screen_pass'],'R3_SOURCE')
    files=c10.verify_c09(c10.c09.OUT)
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(q) for q in (root,p,c10.OUT,c10.c09.OUT,c06.d12.OUT)),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'runner_sha256':a.sha(Path(__file__)),'G18R3_manifest':R3_PIN,
        'scope':'Exact native cell and mesh incidence inventory only; no closure or permission change.',**c.SCOPE})
    report={'screen_pass':False,'additional_native_solves':0,'additional_builds':0,
        'additional_time_advance_years':0,'physical_acceptance':False,'material_assignments':0,**c.SCOPE}
    try:
        report['regional_adjudication_retained']={'accepted':prior['regional_engineering_acceptance'],
            'regional_error':prior.get('regional_error'),'source_manifest':R3_PIN}
        diagnostic=p/'G17_REFERENCE_DIAGNOSTIC.json'
        if diagnostic.exists():
            d=a.read(diagnostic); report['regional_adjudication_retained']['G17_checks']=d['strict_coverage']['checks']
            a.write(out/'G17_REFERENCE_DIAGNOSTIC_RETAINED.json',d)
            m=d['embedded_marker_diagnostic']
            report['regional_adjudication_retained']['G17_marker_summary']={
                'literal_count':m['literal_count'],'token_count':m['token_count'],
                'parsed_marker_count':len(m['parsed_ids']),
                'nonstandalone_lines_count':len(m['nonstandalone_lines']),
                'screen_pass':m['screen_pass']}
        a.write(out/'REGIONAL_BLOCKER_RECEIPT.json',report['regional_adjudication_retained'])
        print('G19_REGIONAL_BLOCKER',json.dumps(report['regional_adjudication_retained']),flush=True)
        global_report=c09case.global_route(root)
        a.need(json.loads(json.dumps(global_report,allow_nan=False))==a.read(p/'GLOBAL_INPUT_PREFLIGHT.json')
            ==a.read(c10.c09.OUT/'REGIONAL_GLOBAL_ROUTE_COMPARISON.json')['global'],'GLOBAL_PREFLIGHT_REPLAY')
        print('G19_SOURCE_SUPPORT_ATLAS',flush=True)
        report['atlas']=atlas(root,out,c06,c09case,global_report)
        catalog=a.read(c10.c09.OUT/'PUBLISHED_CONSTITUTIVE_MODELS.json')
        keys=('native_legacy','native_diorite2','layered_yu_initial','source_records')
        a.need(all(k in catalog for k in keys),'CONSTITUTIVE_CATALOG')
        a.write(out/'RETAINED_CONSTITUTIVE_CANDIDATES.json',{k:catalog[k] for k in keys})
        a.write(out/'CLOSURE_REQUIREMENTS.json',{
            'ZERO_AGE_RIDGE':{'cells':108,'required':'Finite-age or explicit nascent lithosphere boundary/initialization law, with mass and enthalpy transfer; no age floor promoted.'},
            'UNRESOLVED_POSITIVE_AGE_OCEAN':{'cells':1072,'required':'Resolve source boundary kinematics and contact classification; preserve ages and memberships pending decision.'},
            'GLOBAL_RHEOLOGY':{'required':'Domain-specific conditional laws and source validity/sensitivity; do not extend R8 Diorite2 by default.'},
            'GLOBAL_MECHANICS':{'required':'Admit driving loads, basal policy, sided contacts and actual gauge/nullspace; then qualify sparse assembly.'},
            'authorized_new_assignments':0,**c.SCOPE})
        report['screen_pass']=True
    except Exception as exc:
        report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    a.need(c.inventory(p)==pm['files'] and a.sha(p/'MANIFEST.json')==R3_PIN and
        c10.verify_c09(c10.c09.OUT)==files,'PARENT_MUTATION')
    status='G19_GLOBAL_SUPPORT_ATLAS_PASS__MATERIAL_AND_BOUNDARY_CLOSURE_REQUIRED' if report['screen_pass'] else 'G19_GLOBAL_SUPPORT_ATLAS_BLOCKED'
    report.update(status=status,limitations=['Source incidence and D12 masks only, no new material or rheology authority.',
        'PRE owner is a numerical representation, not a unique constitutive assignment.',
        'R3 regional status remains independent and unchanged; no global assembly or physical T1.'])
    a.write(out/'G19_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G18R3_manifest_sha256':R3_PIN,
        'C09_manifest_sha256':c10.PIN,'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G19_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True); print(status,flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
