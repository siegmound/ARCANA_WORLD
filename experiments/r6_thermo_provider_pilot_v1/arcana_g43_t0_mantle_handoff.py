#!/usr/bin/env python3
"""G43: source-bound T0 thermal/support packet, not a physical mantle initializer.
Retain exact PRE and masks, sample existing evaluator to 300 km only.
Never infer full-mantle state, EOS, absolute pressure, viscosity or forcing.
"""
import argparse
import csv
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import traceback
import numpy as np
import arcana_g25_fixed_load_decomposition as g25
import arcana_g23_conditional_global_csr as g23
import arcana_g26_basal_pressure_audit as g26
import arcana_g27_interface_torque_budget as g27
import arcana_g32_corrected_global_operator as g32
import arcana_g33_native_basal_coupling_audit as g33
import arcana_g34_basal_depth_support as g34
from arcana_worldsim.r6.pre_orbdata_runtime_package import FIELDS

PIN='f50077b527e8cabe8b4f294a07ec1221bbf6168a91809bb5607074d4bcf8494f'
STATUS='G42_SYNTHETIC_CBF_PARITY_PASS__MANTLE_STATE_AND_REAL_INTERFACE_REQUIRED'
AUTH='G43_T0_SOURCE_BOUND_THERMAL_HANDOFF_ONLY_V1'
need,sha,read,write,inventory=g25.need,g25.sha,g25.read,g25.write,g25.inventory
N,E,Q=g34.N,g34.E,g34.Q
REF='R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json'
M01='experiments/r6_thermo_provider_pilot_v1/m01_mantle_experimental_design_candidate_v1.json'
DOCS=(REF,M01,'R6_PRE_ORBDATA_TRANSIENT_THERMAL_COUPLING.json',
      'R6_GEODYNAMIC_LAW_AUTHORITY_MATRIX.json',
      'experiments/first_physical_geodynamics_v1/README.md',
      'external/ShellSet-v1.1.0/src/MOD_ArcanaRuntime.f90',
      'src/arcana_worldsim/r6/pre_orbdata_runtime_package.py')
DEPTHS=np.arange(0,300001,10000,dtype=np.float64)

def frozen(root):
    for name in DOCS:
        p=root/name
        need(p.read_bytes()==subprocess.check_output(['git','-C',str(root),'show',g25.SOURCE+':'+name]),'FROZEN_FILE:'+name)
    return {name:sha(root/name) for name in DOCS}

def support(p,pre,tri):
    with (p/'GLOBAL_NODAL_SUPPORT.csv').open() as f: rows=list(csv.DictReader(f))
    with (p/'GLOBAL_TRIANGLE_SUPPORT.csv').open() as f: faces=list(csv.DictReader(f))
    need(len(rows)==N and len(faces)==E,'ATLAS_COUNTS')
    need([int(r['node_id']) for r in rows]==list(range(1,N+1)),'ATLAS_NODE_IDS')
    need([int(r['triangle_id']) for r in faces]==list(range(1,E+1)),'ATLAS_TRI_IDS')
    cols={k:i for i,k in enumerate(FIELDS)}
    for i,r in enumerate(rows):
        z=pre[i]
        need(r['PRE_owner_cell']==f"R6G1D-R{int(z[cols['owner_row']]):03d}-C{int(z[cols['owner_column']]):03d}"
            and int(r['PRE_owner_domain'])==z[cols['owner_domain_id']]
            and int(r['PRE_branch'])==z[cols['runtime_branch_code']]
            and r['constitutive_assignment']=='UNASSIGNED','OWNER_JOIN:'+str(i+1))
    state=np.array([r['D12_incident_support'] for r in rows])
    conditional=np.array([r['conditional_support_status'] for r in rows])
    admitted=np.array([int(r['D12_admitted']) for r in faces],dtype=np.uint8)
    need(set(admitted)=={0,1} and np.count_nonzero(admitted==0)==2360,'TRI_EXCLUSIONS')
    hit=np.zeros(N,dtype=bool); hit[tri[admitted==0].ravel()]=True
    good=np.zeros(N,dtype=bool);good[tri[admitted==1].ravel()]=True
    need(np.array_equal(state=='ALL_ADMITTED',~hit & good)
         and np.array_equal(state=='ALL_EXCLUDED',hit & ~good)
         and np.array_equal(state=='PARTIAL_EXCLUDED',hit & good),'INCIDENCE_PARITY')
    need(Counter(state)=={'ALL_ADMITTED':62330,'PARTIAL_EXCLUDED':1795,'ALL_EXCLUDED':317},'D12_COUNTS')
    need(Counter(conditional)=={'SOURCE_DERIVED_CONDITIONAL':58916,'MIXED_OR_CONFLICTING_SUPPORT':4370,'UNKNOWN':1156},'CONDITIONAL_COUNTS')
    need(np.all(state[conditional=='SOURCE_DERIVED_CONDITIONAL']=='ALL_ADMITTED'),'CONDITIONAL_LEAK')
    return state,conditional,admitted,rows,faces

def eval_at(pre,z):
    # Per-column boundary depths (not a Cartesian FE volume).
    a=z-pre[:,39];b=z-pre[:,45]
    p1=((pre[:,41]*a+pre[:,42])*a+pre[:,43])*a+pre[:,44]
    p2=((pre[:,47]*b+pre[:,48])*b+pre[:,49])*b+pre[:,50]
    ad=pre[:,20]*np.exp(pre[:,34]*9.82*(z-pre[:,17])/pre[:,36])
    return np.where(z<pre[:,15],p1,np.where(z<=pre[:,17],p2,ad))

def audit(root,p19,p23,p26,p32,out):
    need(len(FIELDS)==51 and FIELDS[17]=='lab_depth_m' and FIELDS[20]=='lab_temperature_k'
         and FIELDS[34]=='mantle_expansivity_k_1' and FIELDS[36]=='mantle_cp_j_kg_k','PRE_SCHEMA')
    base=p23/'native_diorite2'
    pre=g34.read_pre(base/'regional_PRE.dat')
    need(sha(base/'regional_PRE.dat')==sha(p23/'native_legacy/regional_PRE.dat')
         ==sha(p32/'native_diorite2/regional_PRE.dat'),'PRE_LINEAGE')
    with np.load(p32/'native_diorite2/GLOBAL_PRE_BC_FIELDS.npz',allow_pickle=False) as d:xyz=d['native_xyz']
    need(xyz.shape==(N,3) and np.max(abs(np.linalg.norm(xyz,axis=1)-1))<1e-10,'GEOMETRY')
    R=float(read(p32/'native_diorite2/CONDITIONAL_CONTROLS.json')['radius'])
    need(R>300000,'REFERENCE_RADIUS')
    f=np.fromfile(p26/'pressure_audit/FB2_QUADRATURE.bin',dtype=g26.FD)
    need(len(f)==Q and np.array_equal(f['ids'][:,0],np.tile(np.arange(1,E+1),7))
         and np.array_equal(f['ids'][:,1],np.repeat(np.arange(1,8),E)),'QUADRATURE_IDS')
    tri=f['ids'][:E,2:].astype(np.int64)-1
    need(tri.min()==0 and tri.max()==N-1
         and np.array_equal(f['ids'][:,2:].reshape(7,E,3),np.broadcast_to(tri+1,(7,E,3))),'TRIANGLE_CONNECTIVITY')
    del f
    state,cond,tri_admitted,rows,faces=support(p19,pre,tri)
    auth=read(root/REF)
    mantle=auth['thermal_properties']['mantle']
    Tp=float(auth['reference_temperatures']['potential_temperature_K']['nominal'])
    grav=float(auth['gravity']['value'])
    alpha=float(mantle['alpha']['nominal']);cp=float(mantle['Cp']['nominal'])
    rho=float(auth['density']['asthenosphere']['nominal'])
    need(grav==9.82 and Tp>0 and alpha>0 and cp>0 and rho>0,'REFERENCE')
    need(np.max(abs(pre[:,34]-alpha))<1e-15 and np.max(abs(pre[:,36]-cp))<1e-10
         and np.max(abs(pre[:,37]-rho))<1e-10,'REFERENCE_PRE_BINDING')
    endpoint={}
    for label,z,target in (('surface',np.zeros(N),pre[:,13]),('moho',pre[:,15],pre[:,18]),('LAB',pre[:,17],pre[:,20])):
        err=float(np.max(abs(eval_at(pre,z)-target)))
        endpoint[label]=err
        need(err<2e-7,'THERMAL_ENDPOINT:'+label)
    T=g34.node_temperature(pre,DEPTHS)
    need(np.all(np.diff(T,axis=0)>=-2e-7),'THERMAL_MONOTONIC')
    for j,z in enumerate(DEPTHS):
        need(np.max(abs(T[j]-eval_at(pre,np.full(N,z))))<2e-7,'TEMPERATURE_REPLAY')
    ref=Tp*np.exp(alpha*grav*DEPTHS/cp)
    below=DEPTHS[:,None]>pre[None,:,17]
    # Eligibility for conditional thermal use is NOT mantle admission.
    candidate=cond=='SOURCE_DERIVED_CONDITIONAL'
    valid=below & candidate[None,:]
    thermal=np.where(valid,T,np.nan)
    need(np.array_equal(np.isfinite(thermal),valid),'MASK_LEAK')
    # Keep both the exact numerical column and a masked view. All model
    # fields not supported by the column remain absent, never zero-filled.
    np.savez_compressed(out/'T0_THERMAL_SOURCE_PACKET.npz',
        node_id=pre[:,0].astype(np.int64),unit_xyz=xyz,triangle_node_id=tri+1,
        depth_m=DEPTHS,reference_radius_m=np.array(R),pre_fields=np.array(FIELDS),pre_records=pre,
        D12_node_support=state,conditional_node_support=cond,triangle_D12_admitted=tri_admitted,
        triangle_parent_cell=np.array([r['parent_cell_id'] for r in faces]),
        owner_cell=np.array([r['PRE_owner_cell'] for r in rows]),
        numeric_column_temperature_K=T,reference_adiabat_K=ref,
        conditional_below_LAB_mask=valid,conditional_below_LAB_temperature_K=thermal,
        conditional_below_LAB_delta_T_K=np.where(valid,T-ref[:,None],np.nan),
        physical_mantle_admission=np.zeros(N,dtype=bool))
    summaries=[]
    for j,z in enumerate(DEPTHS):
        v=thermal[j,valid[j]]
        summaries.append({'depth_m':float(z),'conditional_nodes':int(valid[j].sum()),
            'numeric_below_LAB_nodes':int(below[j].sum()),
            'temperature_range_K':[float(v.min()),float(v.max())] if len(v) else None,
            'reference_adiabat_K':float(ref[j]),
            'delta_T_range_K':[float((v-ref[j]).min()),float((v-ref[j]).max())] if len(v) else None})
    write(out/'THERMAL_DEPTH_SUMMARY.json',summaries)
    m01=read(root/M01)
    need(m01['authorial_selection'] is None and m01['engine_executions_authorized']==0
         and m01['source_state']['absolute_pressure_pa'] is None,'M01_AUTHORITY')
    contract={'epoch':'T0_210_Ma','scope':'source-column diagnostic, not solver launch input',
        'geometry':{'surface_reference_radius_m':R,'LAB_depth':'exact PRE owner-bound local column coordinate',
            'physical_outer_mantle_mesh':None,'core_mantle_boundary_radius_m':None,
            'depth_coordinate':'local column depth; not silently mapped to geocentric radius under topography'},
        'thermal':{'potential_temperature_K':auth['reference_temperatures']['potential_temperature_K'],
            'mantle_alpha':mantle['alpha'],'mantle_cp':mantle['Cp'],'mantle_k':mantle['k'],
            'reference_density':auth['density']['asthenosphere'],'gravity':auth['gravity'],
            'reference_scope':'authorial specialist reference for PRE / asthenosphere; not deep mantle field',
            'sample_ceiling_m':300000,'ceiling_semantics':'G34 exploratory bound only',
            'deep_mantle_temperature_field':None,'CMB_heat_flux':None,'volumetric_heat_production_field':None},
        'unknown_or_unselected':{k:None for k in ('absolute_pressure','compressible_EOS','density_field',
            'composition_field','phase_field','water_field','viscosity_law','mantle_velocity',
            'initial_buoyancy_anomalies','initial_stress','core_boundary_condition','physical_interface_traction',
            'plate_mantle_kinematic_contract','unresolved_layer_depth','deep_to_mantle_coupling')},
        'M01':{'status':m01['status'],'authorial_selection':None,'engine_executions_authorized':0,
            'source_state':m01['source_state'],'proposed_cases':m01['proposed_distinct_cases'],
            'blockers':m01['blockers']},
        'D12':{'excluded_cells':1180,'excluded_triangles':2360,'conditional_nodes':int(candidate.sum()),
            'physical_mantle_admitted_nodes':0,'policy':'Do not turn PRE numerical coverage into admission.'},
        'next_required':['Adjudicate full mantle versus reduced upper-mantle shell, radial geometry and boundary authority.',
            'Bind depth/height convention and actual volume mesh to source geometry.',
            'Select explicit pressure/EOS, thermal and rheological scope with uncertainty; resolve D12/contact gaps.',
            'Qualify actual FE trace transfer and native CBF in the selected physical configuration.',
            'Corrected G15 regional trajectory remains an independent required regression.'],
        'ASPECT_launch_authorized':False,'material_assignments':0,**g25.SCOPE}
    write(out/'MANTLE_INITIALIZER_CONTRACT.json',contract)
    # Candidate discovery only, not a claim of absence or authority.
    paths=subprocess.check_output(['git','-C',str(root),'ls-tree','-r','--name-only',g25.SOURCE],text=True).splitlines()
    matches=[s for s in paths if re.search(r'mantle|asthenosphere|geochem|geodyn|planetary|interior|core.mantle|rheolog',s,re.I)]
    write(out/'SOURCE_DISCOVERY.json',{'filename_candidates':matches,'content_adjudication_complete':False,
        'absence_inferred':False})
    return {'nodes':N,'triangles':E,'sample_depths':len(DEPTHS),'numerical_temperature_samples':int(T.size),
        'conditional_below_LAB_samples':int(valid.sum()),'physical_mantle_admitted_nodes':0,
        'endpoint_max_error_K':endpoint,'D12_counts':dict(Counter(state)),
        'conditional_counts':dict(Counter(cond)),'source_candidate_paths':len(matches),
        'depth_250km':summaries[25],'depth_300km':summaries[30],
        'physical_initializer_complete':False}

def main():
    ap=argparse.ArgumentParser()
    for k in ('g19','g23','g26','g32','g42','output'):ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--authorize-t0-thermal-handoff-only',choices=[AUTH],required=True)
    a=ap.parse_args()
    p19,p23,p26,p32,p42,out=(x.resolve() for x in (a.g19,a.g23,a.g26,a.g32,a.g42,a.output))
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    def check():
        need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==g25.SOURCE
             and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    def parents():
        return [g23.c.verified(p19,g23.G19_PIN,g23.G19_STATUS),g25.verify(p23,0),g27.verify(p26),
                g32.verify(p32,g33.PIN,g33.STATUS),g32.verify(p42,PIN,STATUS)]
    check();before=parents();source_hash=frozen(root)
    need(before[1]['G19_manifest_sha256']==g23.G19_PIN,'G23_G19_LINEAGE')
    need(not out.exists() and not any(out.is_relative_to(x) or x.is_relative_to(out) for x in (root,p19,p23,p26,p32,p42)),'OUTPUT')
    out.mkdir()
    report={'source_sha':g25.SOURCE,'G19_manifest_sha256':g23.G19_PIN,'G23_manifest_sha256':g25.PINS[0],
        'G26_manifest_sha256':g27.PIN,'G32_manifest_sha256':g33.PIN,'G42_manifest_sha256':PIN,
        'additional_builds':0,'additional_global_solves':0,'additional_time_advance_years':0,'material_assignments':0,
        'physical_acceptance':False,'global_solve_authorized':False,'mantle_initial_state_admitted':False,
        'mantle_provider_qualified':False,**g25.SCOPE}
    try:
        write(out/'FROZEN_AUTHORITY_HASHES.json',source_hash)
        report['audit']=audit(root,p19,p23,p26,p32,out)
        report.update(screen_pass=True,status='G43_T0_THERMAL_HANDOFF_PASS__PHYSICAL_MANTLE_INITIALIZER_BLOCKED')
    except Exception as e:report.update(screen_pass=False,status='G43_T0_THERMAL_HANDOFF_BLOCKED',error=repr(e),traceback=traceback.format_exc())
    try:
        check();need(parents()==before and frozen(root)==source_hash,'PARENT_MUTATION')
        report['source_and_parents_unchanged']=True
    except Exception as e:report.update(screen_pass=False,status='G43_T0_THERMAL_HANDOFF_BLOCKED',postcheck_error=repr(e))
    write(out/'REPORT.json',report)
    write(out/'MANIFEST.json',{**report,'runner_sha256':sha(Path(__file__)),'files':inventory(out)})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G43_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
