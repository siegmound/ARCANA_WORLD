"""Source-original T0 cold-crust brittle/plastic *applicability* diagnostics.

A contextual terrestrial quartz-rich brittle-plastic temperature window is
intersected with the exact original T0 PRE cubic temperature profiles.
Depths and incremental vertical overburden within the window are derived,
not fault stresses or physically calibrated transition boundaries.

Byerlee's friction is provided only as a separate Earth lab analogue operator
requiring an EXPLICIT effective normal stress; it is never evaluated on the
original ARCANA data (real pressure, fault orientation and gouge are unknown).
No authorial rock assignment, constitutive law selection or T1 is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

SCHEMA = 'ARCANA_R6_T0_COLD_CRUST_SOURCE_RELEVANCE_AUDIT_V1'
STATUS = 'SOURCE_T0_COLD_CRUST_THERMAL_CONTEXT__NO_CONSTITUTIVE_LAW_SELECTED'
BPT_WINDOW_K = (523.15, 623.15)  # Earth quartz-rich continental crust, context NOT law validity
BPT_DOI = '10.1029/2024GC011446'
BYERLEE_DOI = '10.1007/BF00876528'
GT95_K = (1173.15, 1373.15)
FILES = ('REGION_8X8_COLD_CRUST.json', 'REGION_16X16_COLD_CRUST.json', 'AUDIT.json')
SOURCE_PT_FILES = ('REGION_8X8_SOURCE_PT.json','REGION_16X16_SOURCE_PT.json','AUDIT.json')

class ColdCrustInputError(ValueError):
    pass


def need(value: bool, code: str):
    if not value:
        raise ColdCrustInputError(code)


def positive(value, code):
    need(type(value) in (int,float) and math.isfinite(value) and value > 0,
         'COLD_CRUST_INVALID_POSITIVE_'+code)
    return float(value)


def _poly(pre):
    """T(t)=a*t^3+b*t^2+c*t+d, t=depth/H; exact cubic source T0."""
    names=('layer1_z0_m','layer1_z1_m','layer1_c0_k','layer1_c1_k_m',
           'layer1_c2_k_m2','layer1_c3_k_m3')
    need(type(pre) is dict and all(k in pre for k in names),
         'COLD_CRUST_ORIGINAL_PRE_MISSING')
    vals=[pre[k] for k in names]
    need(all(type(v) in (int,float) and math.isfinite(v) for v in vals),
         'COLD_CRUST_ORIGINAL_PRE_NONFINITE')
    z0,z1,c0,c1,c2,c3=map(float,vals)
    H=z1-z0
    positive(pre.get('crust_density_kg_m3'),'DENSITY')
    need(abs(z0)<1e-6 and H>0 and c0>0 and math.isclose(
         H,positive(pre.get('crust_thickness_m'),'THICKNESS'),rel_tol=0,abs_tol=1e-5),
         'COLD_CRUST_SOURCE_DEPTH_OR_THICKNESS_MISMATCH')
    a,b,c,d=c3*H**3,c2*H**2,c1*H,c0
    need(all(math.isfinite(v) for v in (a,b,c,d)),
         'COLD_CRUST_POLYNOMIAL_OVERFLOW')
    return (a,b,c,d,H)


def _at(coeff,t):
    a,b,c,d,_=coeff
    return ((a*t+b)*t+c)*t+d


def _unique(values, tolerance=2e-11):
    out=[]
    for v in sorted(values):
        if not out or abs(v-out[-1])>tolerance:
            out.append(v)
    return out


def _stationary(coeff):
    a,b,c,_,_=coeff
    scale=max(abs(a),abs(b),abs(c),1e-30)
    roots=[]
    if abs(a)<=1e-14*scale:
        if abs(b)>1e-14*scale:
            roots.append(-c/(2*b))
    else:
        discriminant=(2*b)**2-12*a*c
        if discriminant>=0:
            q=math.sqrt(discriminant)
            roots.extend(((-2*b-q)/(6*a),(-2*b+q)/(6*a)))
    return _unique([t for t in roots if 0<t<1])


def _crossings(coeff,target):
    """All roots of T(t)=target, split at extrema, bisection on monotone arcs."""
    knots=[0.,*_stationary(coeff),1.]
    roots=[]
    for left,right in zip(knots,knots[1:]):
        fl=_at(coeff,left)-target;fr=_at(coeff,right)-target
        if abs(fl)<1e-9:roots.append(left)
        if abs(fr)<1e-9:roots.append(right)
        if fl*fr<0:
            lo,hi=left,right
            for _ in range(70):
                mid=(lo+hi)/2
                fm=_at(coeff,mid)-target
                if (fl<0 and fm<0) or (fl>0 and fm>0):
                    lo=mid;fl=fm
                else:hi=mid
            roots.append((lo+hi)/2)
    return _unique(roots)


def temperature_window_segments(pre,window_k=BPT_WINDOW_K):
    """Find all positive-width continuous crust intervals with T within window.

    Handles nonmonotone cubic PRE, multiple disjoint crossings and constant
    polynomials. Touching a boundary at one point yields no finite interval.
    """
    need(type(window_k) in (tuple,list) and len(window_k)==2,
         'COLD_CRUST_CONTEXT_WINDOW_INVALID')
    lo=positive(window_k[0],'WINDOW_LO');hi=positive(window_k[1],'WINDOW_HI')
    need(lo<hi,'COLD_CRUST_CONTEXT_WINDOW_REVERSED')
    coeff=_poly(pre)
    cuts=_unique([0.,1.,*_crossings(coeff,lo),*_crossings(coeff,hi)])
    segments=[]
    for left,right in zip(cuts,cuts[1:]):
        if right-left<2e-11:continue
        t=_at(coeff,(left+right)*.5)
        if lo-1e-7<=t<=hi+1e-7:
            if segments and abs(segments[-1][1]-left)<1e-10:
                segments[-1][1]=right
            else:segments.append([left,right])
    return [[a*coeff[4],b*coeff[4]] for a,b in segments]


def byerlee_reference_shear_pa(effective_normal_stress_pa, *, earth_analogue_only):
    """Byerlee 1978 common-rock friction benchmark, not Arcana fault physics.

    Effective normal stress must be supplied independently; neither the T0
    conditional vertical overburden nor an assumed zero pore-pressure counts.
    Not valid for clay/serpentine rich fault material or arbitrary slip rates.
    """
    need(earth_analogue_only is True,
         'COLD_CRUST_BYERLEE_NEVER_AUTHORITATIVE')
    p=positive(effective_normal_stress_pa,'EFFECTIVE_NORMAL_STRESS')
    need(p<=1.7e9,'COLD_CRUST_BYERLEE_OUTSIDE_REFERENCE_STRESS')
    return 0.85*p if p<=2e8 else 5e7+0.6*p


def evaluate_column(pre,source_pt_node, *, gravity_m_s2):
    """Actual original PRE column, only thermal relevance and delta pressure."""
    g=positive(gravity_m_s2,'GRAVITY')
    coeff=_poly(pre)
    rho=positive(pre.get('crust_density_kg_m3'),'DENSITY')
    need(type(source_pt_node) is dict
         and source_pt_node.get('constitutive_law_assigned') is False
         and source_pt_node.get('actual_vertical_stress_pa') is None
         and source_pt_node.get('effective_pressure_pa') is None
         and source_pt_node.get('pore_pressure_pa') is None
         and source_pt_node.get('fault_normal_pressure_pa') is None,
         'COLD_CRUST_PT_PHYSICAL_AUTHORITY_ALREADY_SELECTED')
    source_moho=source_pt_node['conditional_moho_delta_overburden_pa']
    need(type(source_moho) in (float,int) and math.isclose(
         source_moho,rho*g*coeff[4],rel_tol=2e-12),
         'COLD_CRUST_PT_ORIGINAL_OVERBURDEN_MISMATCH')
    intervals=temperature_window_segments(pre)
    rows=[{'depth_interval_m':bounds,
           'conditional_delta_sigma_v_pa_interval': [rho*g*z for z in bounds],
           'real_effective_fault_normal_stress_pa':None,
           'rock_phase_identity':None,
           'physical_brittle_ductile_transition':None}
          for bounds in intervals]
    need(all(0<=a<b<=coeff[4] for a,b in intervals),
         'COLD_CRUST_INTERVAL_INVALID')
    return {
        'original_crust_PRE_exact_temperature_range_k':
            source_pt_node['exact_PRE_temperature_bounds_k']['crust'],
        'original_crust_thickness_m':coeff[4],
        'earth_quartz_rich_BPT_temperature_only_intervals':rows,
        'earth_quartz_rich_BPT_temperature_window_k':list(BPT_WINDOW_K),
        'earth_BPT_temperature_intersects_crust_by_positive_width':bool(rows),
        'earth_BPT_qualitative_context_not_lab_law':True,
        'byerlee_Earth_analogue_available_only_if_effective_fault_normal_known':True,
        'GT95_laboratory_crust_temperature_coverage':
            source_pt_node['terrestrial_GT95_lab_temperature_only_coverage']['crust'],
        'source_node_lithology':None,
        'source_water_fugacity_pa':None,
        'source_pore_pressure_pa':None,
        'source_effective_fault_normal_stress_pa':None,
        'selected_brittle_law':None,
        'selected_ductile_law':None,
        'verified_P_T_rate_stress_domain':None,
        'computed_real_brittle_ductile_transition_depth_m':None,
        'model_regime_assignment':'UNDETERMINED',
    }


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_original_pt(folder):
    folder=Path(folder)
    m=json.loads((folder/'MANIFEST.json').read_text())
    need(m.get('schema')=='ARCANA_R6_G2_G3_CONDITIONAL_PT_REFERENCE_MANIFEST_V1'
         and m.get('no_solver_run') is True
         and m.get('physical_T1') is None
         and m.get('HistoryStore_modified') is False
         and m.get('D_024')=='ACTIVE'
         and m.get('WORLD_HISTORY_PRODUCTION_AUTHORIZED') is False
         and set(m.get('files',{}))==set(SOURCE_PT_FILES),
         'COLD_CRUST_PT_MANIFEST_NOT_FAIR_SCOPE')
    for filename,digest in m['files'].items():
        need(type(digest) is str and len(digest)==64
             and sha256(folder/filename)==digest,
             'COLD_CRUST_PT_SOURCE_HASH_DRIFT:'+filename)
    reports=[json.loads((folder/f'REGION_{n}X{n}_SOURCE_PT.json').read_text())
             for n in (8,16)]
    audit=json.loads((folder/'AUDIT.json').read_text())
    need(audit.get('mechanical_solve_authorized') is False
         and audit.get('physical_T1') is None
         and audit.get('D_024')=='ACTIVE'
         and audit.get('physical_G2_material_law_or_rock_selected') is False,
         'COLD_CRUST_PT_AUDIT_AUTHORITY_INVALID')
    return m,reports,audit


def build(*,repo_root,packet8,packet16,handoff,pt_folder):
    """Reopen SHA-verified original source packets AND already FAIR original PT."""
    from experiments.plate58_deforming_explore_v1.g2_g3_t0_lithostatic_pt_reference import (
        build as rebuild_pt, source_gravity_and_lab,
    )
    from experiments.plate58_deforming_explore_v1.g2_g3_source_to_coupled_handoff import (
        load_packet,
    )
    from experiments.plate58_deforming_explore_v1.g2_g3_physical_source_packet import (
        verify_cross_extent_provider_chain,
    )
    gravity,_,_=source_gravity_and_lab(repo_root)
    idx8,_,r8=load_packet(packet8,8)
    idx16,_,r16=load_packet(packet16,16)
    verify_cross_extent_provider_chain(idx8,idx16)
    manifest,reports,audit=_load_original_pt(pt_folder)
    # Independent recomputation of BOTH source pressure reports, including
    # complete original nodal P/T fields, rejects stale/substituted reports.
    expected8,expected16,expected_audit=rebuild_pt(
        repo_root,packet8,packet16,handoff)
    need((reports[0]==expected8 and reports[1]==expected16
          and audit==expected_audit),
         'COLD_CRUST_PT_SOURCE_ORIGINAL_RECOMPUTATION_MISMATCH')
    out=[]
    for n,index,record,receipt in ((8,idx8,reports[0],r8),
                                    (16,idx16,reports[1],r16)):
        source_nodes=index['source_original_PRE_model_T0_thermal_profiles_by_parent_node']
        ids=index['original_parent_node_order']
        need(record.get('source_packet_manifest_sha256')==receipt['evidence_manifest_sha256']
             and record.get('source_node_count')==len(ids)
             and set(source_nodes)==set(map(str,ids))
             and set(record['original_T0_source_nodes'])==set(source_nodes)
             and record.get('mechanical_solve_authorized') is False
             and record.get('physical_T1') is None,
             'COLD_CRUST_REGION_CROSS_SOURCE_DRIFT')
        rows={str(i):evaluate_column(source_nodes[str(i)],
             record['original_T0_source_nodes'][str(i)],gravity_m_s2=gravity)
             for i in ids}
        count=sum(r['earth_BPT_temperature_intersects_crust_by_positive_width']
                  for r in rows.values())
        total_intervals=sum(len(r['earth_quartz_rich_BPT_temperature_only_intervals'])
                            for r in rows.values())
        no_gt95=all(not r['GT95_laboratory_crust_temperature_coverage']['temperature_only_some_overlap']
                    for r in rows.values())
        need(no_gt95,'COLD_CRUST_GT95_PREVIOUS_FAIR_ZERO_OVERLAP_DRIFT')
        out.append({
            'schema':SCHEMA,'decision':STATUS,'epoch':'T0_210_Ma',
            'extent_cells':n,'source_node_count':len(ids),
            'source_parent_ids':ids,
            'original_T0_source_nodes':rows,
            'source_PT_manifest_sha256':sha256(Path(pt_folder)/'MANIFEST.json'),
            'source_region_PT_sha256':sha256(Path(pt_folder)/f'REGION_{n}X{n}_SOURCE_PT.json'),
            'source_original_packet_sha256':receipt['evidence_manifest_sha256'],
            'source_original_FEG_sha256':index['source_hashes']['original_FEG_sha256'],
            'source_original_PRE_sha256':index['source_hashes']['original_PRE_sha256'],
            'earth_references':{
                'contextual_quartz_rich_BPT_DOI':BPT_DOI,
                'contextual_BPT_interval_K':list(BPT_WINDOW_K),
                'lab_friction_analogue_DOI':BYERLEE_DOI,
                'GT95_rejected_by_prior_FAIR_PT':True,
                'context_is_not_calibrated_T_P_rate_law':True,
            },
            'summary':{
                'earth_BPT_temperature_window_nodes':count,
                'earth_BPT_temperature_intersection_intervals':total_intervals,
                'source_nodes_with_GT95_T_overlap':0,
                'source_selected_rocks':0,
                'source_fault_normal_effective_pressure_assignments':0,
                'source_constitutive_laws_selected':0,
            },
            'source_actual_local_triple_plate_junctions':index['source_actual_3plus_plate_junctions'],
            'all_potential_mechanisms_are_conditional':True,
            'fault_geometry_not_equivalent_to_slip_DOF':True,
            'no_actual_brittle_plastic_transition_claim':True,
            'no_P_T_rate_material_qualification':True,
            'unresolved_physical_groups':list(record['remaining_physical_groups']),
            'mechanical_solve_authorized':False,'physical_T1':None,
            'HistoryStore_modified':False,'D_024':'ACTIVE',
            'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False,
        })
    return out[0],out[1],{
        'schema':'ARCANA_R6_T0_COLD_CRUST_REGIME_AUDIT_V1',
        'decision':STATUS,'source_pt_manifest_sha256':sha256(Path(pt_folder)/'MANIFEST.json'),
        'source_8_original_T0_nodes':len(out[0]['original_T0_source_nodes']),
        'source_16_original_T0_nodes':len(out[1]['original_T0_source_nodes']),
        'source_pt_moho_original_recomputed':True,
        'earth_quartz_rich_BPT_250_350C_CONTEXT_ONLY':True,
        'BPT_window_is_not_universal_transition_temperature':True,
        'Byerlee_requires_independent_effective_normal_stress_and_fault_material':True,
        'GT95_actual_crust_scope_rejected':True,
        'material_rock_selected':False,'water_pore_pressure_selected':False,
        'mechanical_fault_or_traction_assigned':False,
        'physical_T1':None,'mechanical_solve_authorized':False,
        'HistoryStore_modified':False,'D_024':'ACTIVE',
        'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False,
    }


def write_once(repo_root,output,objects):
    output=Path(output).resolve(); root=Path(repo_root).resolve()
    need(not output.is_relative_to(root) and not output.exists(),
         'COLD_CRUST_EVIDENCE_OUTPUT_INSIDE_REPO_OR_EXISTS')
    need(set(objects)==set(FILES) and all(
        x.get('physical_T1') is None and x.get('mechanical_solve_authorized') is False
        and x.get('HistoryStore_modified') is False
        and x.get('D_024')=='ACTIVE'
        for x in objects.values()),'COLD_CRUST_UNAUTHORIZED_OUTPUT')
    texts={k:json.dumps(v,allow_nan=False,indent=2)+'\n' for k,v in objects.items()}
    output.mkdir(parents=True,exist_ok=False)
    for name,text in texts.items():(output/name).write_text(text,encoding='utf-8')
    m={'schema':'ARCANA_R6_T0_COLD_CRUST_REGIME_MANIFEST_V1',
       'decision':STATUS,'files':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in texts.items()},
       'source_PT_manifest_sha256':objects['AUDIT.json']['source_pt_manifest_sha256'],
       'no_solver_run':True,'physical_T1':None,'HistoryStore_modified':False,
       'D_024':'ACTIVE','WORLD_HISTORY_PRODUCTION_AUTHORIZED':False}
    (output/'MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
    return m


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo-root',type=Path,required=True)
    p.add_argument('--packet-8',type=Path,required=True)
    p.add_argument('--packet-16',type=Path,required=True)
    p.add_argument('--handoff',type=Path,required=True)
    p.add_argument('--pt-reference',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    inputs=[(d/f) for d,fs in ((a.packet_8,('MANIFEST.json','SOURCE_INDEX.json','UNSELECTED_PHYSICAL_PROPOSAL.json')),
                               (a.packet_16,('MANIFEST.json','SOURCE_INDEX.json','UNSELECTED_PHYSICAL_PROPOSAL.json')),
                               (a.handoff,('MANIFEST.json','SCENARIO_8X8_UNSELECTED.json','SCENARIO_16X16_UNSELECTED.json','AUDIT.json')),
                               (a.pt_reference,('MANIFEST.json',*SOURCE_PT_FILES))) for f in fs]
    before=[sha256(path) for path in inputs]
    x,y,audit=build(repo_root=a.repo_root,packet8=a.packet_8,packet16=a.packet_16,
                     handoff=a.handoff,pt_folder=a.pt_reference)
    need([sha256(path) for path in inputs]==before,
         'COLD_CRUST_SOURCE_EVIDENCE_CHANGED_DURING_COMPILE')
    write_once(a.repo_root,a.output,dict(zip(FILES,(x,y,audit))))
    print(json.dumps({'decision':STATUS,
        'original_8x8_source_nodes':x['source_node_count'],
        'original_16x16_source_nodes':y['source_node_count'],
        'earth_analogue_BPT_temperature_only_nodes_8x8':x['summary']['earth_BPT_temperature_window_nodes'],
        'earth_analogue_BPT_temperature_only_nodes_16x16':y['summary']['earth_BPT_temperature_window_nodes'],
        'GT95_T_only_nodes_8x8':0,'GT95_T_only_nodes_16x16':0,
        'source_materials_assigned':0,'source_fault_stresses_assigned':0,
        'physical_T1':None,'mechanical_solve_authorized':False,'D_024':'ACTIVE'},allow_nan=False))

if __name__=='__main__':main()
