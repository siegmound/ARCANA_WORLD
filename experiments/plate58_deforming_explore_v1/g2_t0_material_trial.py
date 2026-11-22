"""ARCANA R6: source-keyed T0 G2 material/fluid exploratory law screening.

Numerically evaluates a fully EXPLICIT noncanonical pair of continuum brittle
and triaxial creep candidate laws ONLY within stated T/P/rate lab envelopes.
It cannot assign natural rock, water, fault normal stress or physical T1.
The source PRE and lithostatic P/T data are read and independently replayed
by existing FAIR-qualified source modules before templates are emitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

SCHEMA = 'ARCANA_R6_G2_T0_SOURCE_KEYED_MATERIAL_FLUID_TRIAL_V1'
STATUS = 'G2_T0_EXPLICIT_MATERIAL_TRIAL_ENGINE__SOURCE_LITHOLOGY_UNSELECTED'
AUTHORITY = 'NONCANONICAL_EXPLICIT_AUTHORIAL_TRIAL_ONLY'
R = 8.31446261815324
FILES = ('MATERIAL_8X8_UNSELECTED.json', 'MATERIAL_16X16_UNSELECTED.json', 'AUDIT.json')
COLD_FILES = ('REGION_8X8_COLD_CRUST.json', 'REGION_16X16_COLD_CRUST.json', 'AUDIT.json')
PT_FILES = ('REGION_8X8_SOURCE_PT.json', 'REGION_16X16_SOURCE_PT.json', 'AUDIT.json')


class MaterialTrialError(ValueError):
    pass


def require(ok, code):
    if not ok:
        raise MaterialTrialError(code)


def real(value, code, *, positive=False, lower=None, upper=None):
    require(type(value) in (int,float) and math.isfinite(value), 'MATERIAL_NONFINITE_'+code)
    x=float(value)
    require((not positive or x>0) and (lower is None or x>=lower)
            and (upper is None or x<=upper), 'MATERIAL_VALUE_OUTSIDE_'+code)
    return x


def band(obj,key,*, strictly_positive=False):
    x=obj.get(key)
    require(type(x) is list and len(x)==2, 'MATERIAL_BAND_MISSING_'+key)
    a,b=(real(v,key,positive=strictly_positive) for v in x)
    require(a<b, 'MATERIAL_BAND_ORDER_'+key)
    return a,b


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest(folder, schema, filenames):
    folder=Path(folder)
    m=json.loads((folder/'MANIFEST.json').read_text())
    require(m.get('schema')==schema and m.get('physical_T1') is None
            and m.get('D_024')=='ACTIVE' and m.get('HistoryStore_modified') is False
            and m.get('WORLD_HISTORY_PRODUCTION_AUTHORIZED') is False
            and set(m.get('files',{}))==set(filenames),
            'MATERIAL_EVIDENCE_MANIFEST_AUTHORITY_INVALID')
    for f,h in m['files'].items():
        require(type(h) is str and len(h)==64 and sha(folder/f)==h,
                'MATERIAL_EVIDENCE_SHA_INVALID:'+f)
    return m


def review_brittle_law(law):
    """Candidate Drucker-Prager stress convention, NOT fault-plane Coulomb."""
    require(type(law) is dict and law.get('kind')=='CONTINUUM_3D_DRUCKER_PRAGER'
            and law.get('pressure_convention')=='ASPECT_RHEOLOGY_DP_3D_6P'
            and law.get('stress_output')=='ASPECT_CONTINUUM_J2_EQUIVALENT_PA'
            and law.get('authority')==AUTHORITY,
            'MATERIAL_BRITTLE_CONVENTION_INVALID')
    require(type(law.get('source')) is dict
            and law['source'].get('authority')=='EXTERNAL_CANDIDATE_NOT_ORIGINAL_T0'
            and type(law['source'].get('reference')) is str
            and len(law['source']['reference'])>=12,
            'MATERIAL_BRITTLE_LAB_PROVENANCE_REQUIRED')
    c=real(law.get('cohesion_pa'),'COHESION',lower=0)
    phi=math.radians(real(law.get('friction_angle_deg'),'ANGLE',lower=0,upper=80))
    t=band(law,'valid_temperature_k',strictly_positive=True)
    p=band(law,'valid_effective_pressure_pa')
    rate=band(law,'valid_strain_rate_s_inv',strictly_positive=True)
    require(p[0]>=0,'MATERIAL_BRITTLE_P_NEGATIVE')
    return c,phi,t,p,rate


def continuum_dp_strength_pa(effective_pressure_pa,law,*,temperature_k,strain_rate_s_inv):
    c,phi,temps,pressures,rates=review_brittle_law(law)
    p=real(effective_pressure_pa,'EFFECTIVE_PRESSURE',lower=0)
    T=real(temperature_k,'BRITTLE_T',positive=True)
    rate=real(strain_rate_s_inv,'BRITTLE_RATE',positive=True)
    require(pressures[0]<=p<=pressures[1] and temps[0]<=T<=temps[1]
            and rates[0]<=rate<=rates[1], 'MATERIAL_BRITTLE_OUTSIDE_LAB_DOMAIN')
    v=(6*c*math.cos(phi)+6*p*math.sin(phi))/(math.sqrt(3)*(3+math.sin(phi)))
    require(math.isfinite(v) and v>0,'MATERIAL_BRITTLE_STRENGTH_INVALID')
    return v


def review_creep_law(law):
    """Triaxial differential-stress Arrhenius power law, no J2 conversion."""
    require(type(law) is dict and law.get('kind')=='DISLOCATION_CREEP_POWER_LAW'
            and law.get('stress_convention')=='TRIAXIAL_DIFFERENTIAL_STRESS_PA'
            and law.get('authority')==AUTHORITY,
            'MATERIAL_CREEP_STRESS_CONVENTION_INVALID')
    src=law.get('source')
    require(type(src) is dict
            and src.get('authority')=='EXTERNAL_LAB_CALIBRATION_CANDIDATE_UNVERIFIED'
            and type(src.get('source_sha256')) is str
            and len(src['source_sha256'])==64
            and all(c in '0123456789abcdef' for c in src['source_sha256'])
            and type(src.get('reference')) is str and len(src['reference'])>=12,
            'MATERIAL_CREEP_INDEPENDENT_MEASURED_DATA_PROVENANCE_REQUIRED')
    A=real(law.get('A_pa_minus_n_s_inv'),'A',positive=True)
    n=real(law.get('n'),'N',lower=1,upper=15)
    E=real(law.get('E_j_mol'),'E',lower=0)
    V=real(law.get('V_m3_mol'),'V',lower=0)
    r=real(law.get('water_exponent'),'WATER_EXPONENT',lower=0)
    if r>0:
        f=real(law.get('water_fugacity_pa'),'WATER_FUGACITY',positive=True)
        f_ref=real(law.get('reference_fugacity_pa'),'FUGACITY_REFERENCE',positive=True)
    else:
        require(law.get('water_fugacity_pa') is None
                and law.get('reference_fugacity_pa') is None,
                'MATERIAL_WATER_FUGACITY_AMBIGUOUS')
        f,f_ref=1.,1.
    t=band(law,'valid_temperature_k',strictly_positive=True)
    p=band(law,'valid_confining_pressure_pa')
    rate=band(law,'valid_strain_rate_s_inv',strictly_positive=True)
    require(p[0]>=0,'MATERIAL_CREEP_PRESSURE_NEGATIVE')
    return A,n,E,V,r,f,f_ref,t,p,rate


def creep_differential_stress_pa(law,*,T_k,pressure_pa,rate_s_inv):
    """Numerical inversion; ONLY triaxial stress for a declared lab analogue."""
    A,n,E,V,r,f,f_ref,t,p,rates=review_creep_law(law)
    T=real(T_k,'CREEP_T',positive=True)
    P=real(pressure_pa,'CREEP_PRESSURE',lower=0)
    edot=real(rate_s_inv,'CREEP_RATE',positive=True)
    require(t[0]<=T<=t[1] and p[0]<=P<=p[1]
            and rates[0]<=edot<=rates[1], 'MATERIAL_CREEP_OUTSIDE_LAB_DOMAIN')
    logstress=(math.log(edot)-math.log(A)-r*math.log(f/f_ref)
               +(E+P*V)/(R*T))/n
    require(math.isfinite(logstress) and -700<logstress<700,
            'MATERIAL_CREEP_NUMERIC_OVERFLOW')
    return math.exp(logstress)


def evaluate_candidate_node(pt_node, cold_node, candidate):
    """Candidate-only full-crust thermal and pressure applicability check.

    All pore and surface pressure values MUST be supplied explicitly; the
    source overburden is only an increment. No mapping to fault stresses.
    """
    require(type(pt_node) is dict and type(cold_node) is dict
            and pt_node.get('pore_pressure_pa') is None
            and pt_node.get('fault_normal_pressure_pa') is None
            and pt_node.get('constitutive_law_assigned') is False
            and cold_node.get('source_node_lithology') is None
            and cold_node.get('model_regime_assignment')=='UNDETERMINED',
            'MATERIAL_SOURCE_ALREADY_HAS_UNVERIFIED_AUTHORITY')
    require(type(candidate) is dict and candidate.get('authority')==AUTHORITY
            and candidate.get('authorial_exploration_selected') is True
            and candidate.get('physical_rock_identity_ratified') is False
            and type(candidate.get('authorial_record')) is str
            and len(candidate['authorial_record'])>=10
            and type(candidate.get('bulk_oxide_hypothesis_id')) is str
            and len(candidate['bulk_oxide_hypothesis_id'])>=3
            and type(candidate.get('phase_assemblage_hypothesis')) is str
            and len(candidate['phase_assemblage_hypothesis'])>=5
            and type(candidate.get('hydration_hypothesis')) is str
            and len(candidate['hydration_hypothesis'])>=5,
            'MATERIAL_EXPLICIT_NONCANONICAL_ROCK_FLUID_SELECTION_REQUIRED')
    conditions=candidate.get('conditions')
    require(type(conditions) is dict
            and conditions.get('authority')=='AUTHORIAL_CONDITIONAL_UNOBSERVED'
            and conditions.get('surface_pressure_is_observed') is False
            and conditions.get('pore_pressure_is_observed') is False
            and conditions.get('independently_qualified_fault_normal') is False,
            'MATERIAL_UNQUALIFIED_PHYSICAL_PRESSURE_PROMOTION')
    # Treat as *hypothetical* total model pressure envelope, not a fact.
    P0=real(conditions.get('surface_total_pressure_pa'),'EXPLICIT_SURFACE_P',lower=0)
    pp0=real(conditions.get('surface_pore_pressure_pa'),'EXPLICIT_SURFACE_PORE',lower=0)
    pp1=real(conditions.get('moho_pore_pressure_pa'),'EXPLICIT_MOHO_PORE',lower=0)
    alpha=real(conditions.get('biot_coefficient'),'EXPLICIT_BIOT',lower=0,upper=1)
    rate=real(conditions.get('strain_rate_s_inv'),'EXPLICIT_STRAIN_RATE',positive=True)
    dP=real(pt_node.get('conditional_moho_delta_overburden_pa'),'SOURCE_MOHO_DP',positive=True)
    P1=P0+dP
    require(pp0<=P0 and pp1<=P1,'MATERIAL_PORE_EXCEEDS_CONDITIONAL_PRESSURE')
    # The linear pore-pressure profile is an explicit EXPLORATORY hypothesis.
    eff0=P0-alpha*pp0
    eff1=P1-alpha*pp1
    require(eff0>=0 and eff1>=0,'MATERIAL_NEGATIVE_CONDITIONAL_EFFECTIVE_PRESSURE')
    temps=pt_node['exact_PRE_temperature_bounds_k']['crust']
    require(type(temps) is list and len(temps)==2,'MATERIAL_SOURCE_CRUST_T_BOUNDS_INVALID')
    T0,T1=(real(v,'SOURCE_T',positive=True) for v in temps)
    require(T0<=T1,'MATERIAL_SOURCE_T_BOUNDS_REVERSED')
    brittle=candidate.get('continuum_brittle')
    creep=candidate.get('triaxial_ductile')
    _,_,bt,bp,br=review_brittle_law(brittle)
    _,_,_,_,_,_,_,ct,cp,cr=review_creep_law(creep)
    require(bt[0]<=T0 and T1<=bt[1] and ct[0]<=T0 and T1<=ct[1],
            'MATERIAL_FULL_COLD_CRUST_LAB_T_NOT_COVERED')
    require(bp[0]<=min(eff0,eff1) and max(eff0,eff1)<=bp[1]
            and cp[0]<=P0 and P1<=cp[1],
            'MATERIAL_FULL_COLD_CRUST_LAB_P_NOT_COVERED')
    require(br[0]<=rate<=br[1] and cr[0]<=rate<=cr[1],
            'MATERIAL_FULL_COLD_CRUST_LAB_RATE_NOT_COVERED')
    # Values at extrema are separate, unconvertible stress conventions.
    brittle_range=[continuum_dp_strength_pa(v,brittle,temperature_k=T0,
                                             strain_rate_s_inv=rate)
                   for v in (min(eff0,eff1),max(eff0,eff1))]
    creep_range=[creep_differential_stress_pa(creep,T_k=T,pressure_pa=P,rate_s_inv=rate)
                 for T in (T0,T1) for P in (P0,P1)]
    return {
        'authority':'CONDITIONAL_NONCANONICAL_MATERIAL_TRIAL_NOT_SOURCE_ROCK',
        'candidate_phase_assemblage':candidate['phase_assemblage_hypothesis'],
        'source_temperature_exact_k':[T0,T1],
        'conditional_total_confining_pressure_pa':[P0,P1],
        'conditional_continuum_effective_pressure_pa':[eff0,eff1],
        'candidate_continuum_dp_equivalent_strength_pa_min_max':
            [min(brittle_range),max(brittle_range)],
        'candidate_triaxial_diff_creep_strength_pa_min_max':
            [min(creep_range),max(creep_range)],
        'all_three_lab_T_P_rate_ranges_cover_conditional_column':True,
        'no_comparison_between_distinct_stress_invariants':True,
        'natural_material_identity_verified':False,
        'actual_pore_pressure_verified':False,
        'physical_fault_slip_law':None,
        'actual_brittle_ductile_transition_depth_m':None,
        'mechanical_solve_authorized':False,
        'physical_T1':None,
    }



def verified_bulk_oxide_candidate(folder, hypothesis_id):
    """SHA-bind a prior candidate composition; never convert oxide to phase."""
    path=Path(folder)
    m=json.loads((path/'MANIFEST.json').read_text())
    require(m.get('schema')=='ARCANA_R6_T0_BULK_COMPOSITION_HYPOTHESIS_MANIFEST_V1'
            and m.get('no_canonical_promotion') is True
            and m.get('no_physical_materialization') is True
            and m.get('no_mechanical_solve') is True
            and m.get('no_T1') is True
            and m.get('no_world_history') is True
            and set(m.get('files',{}))=={'REPORT.json'}
            and sha(path/'REPORT.json')==m['files']['REPORT.json'],
            'MATERIAL_BULK_OXIDE_SOURCE_SHA_OR_AUTHORITY_INVALID')
    report=json.loads((path/'REPORT.json').read_text())
    require(report.get('schema')=='ARCANA_R6_T0_BULK_COMPOSITION_CANDIDATE_REPORT_V1'
            and report.get('physically_ratified_T0_composition_cell_count')==0
            and report.get('physical_T0_bulk_chemistry') is None
            and report.get('physical_T0_mineral_phases') is None
            and report.get('mechanical_solve_authorized') is False
            and report.get('physical_T1') is None
            and report.get('D_024')=='ACTIVE',
            'MATERIAL_BULK_OXIDE_SOURCE_PHYSICS_PROMOTION')
    candidates=(report.get('experimental_recipe_records',[])
                +report.get('experimental_mass_mixture_records',[]))
    require(type(hypothesis_id) is str and
            sum(1 for r in candidates if r.get('id')==hypothesis_id)==1,
            'MATERIAL_BULK_OXIDE_HYPOTHESIS_ID_MISSING_OR_DUPLICATED')
    row=next(r for r in candidates if r['id']==hypothesis_id)
    require(type(row.get('oxide_mass_wt_percent')) is dict
            and row['oxide_mass_wt_percent'],
            'MATERIAL_BULK_OXIDE_CHEMISTRY_INVALID')
    return {'candidate_oxide_record_id':hypothesis_id,
            'source_report_sha256':sha(path/'REPORT.json'),
            'oxide_subset_wt_percent':row['oxide_mass_wt_percent'],
            'physical_phase_assemblage_from_oxides':None,
            'original_T0_region_placement_proven':False}


def evaluate_authored_region_trial(template,pt,cold,material_by_parent,*,
                                   oxide_folder,record_id):
    """Full original-parent candidate strength calculation, still NONCANON.

    This optional operation requires author-provided candidate for EVERY
    original T0 parent; no default rock, fluid, stress or strain rate.
    Triaxial stress and DP continuum invariant are returned separately.
    """
    require(type(template) is dict and template.get('extent_cells')==8,
            'MATERIAL_TRIAL_FIRST_EXPLICIT_REGION_MUST_BE_8X8')
    validate_unselected_report(template,8)
    ids=template['source_parent_ids']
    require(type(material_by_parent) is dict
            and set(material_by_parent)==set(map(str,ids))
            and type(record_id) is str and len(record_id)>=12,
            'MATERIAL_TRIAL_EXPLICIT_COMPLETE_SOURCE_MAP_REQUIRED')
    require(pt.get('original_parent_node_order')==ids
            and cold.get('source_parent_ids')==ids,
            'MATERIAL_TRIAL_SOURCE_NODE_PROVENANCE_DRIFT')
    out={};oxide_sources={}
    for n in ids:
        key=str(n);candidate=material_by_parent[key]
        require(type(candidate) is dict and candidate.get('authorial_record')==record_id,
                'MATERIAL_TRIAL_AUTHOR_SELECTION_RECORD_DRIFT')
        oxide_id=candidate.get('bulk_oxide_hypothesis_id')
        require(type(oxide_id) is str and len(oxide_id)>=3,
                'MATERIAL_TRIAL_OXIDE_ID_INVALID')
        if oxide_id not in oxide_sources:
            oxide_sources[oxide_id]=verified_bulk_oxide_candidate(oxide_folder,oxide_id)
        out[key]=evaluate_candidate_node(
            pt['original_T0_source_nodes'][key],
            cold['original_T0_source_nodes'][key],candidate)
    return {'schema':'ARCANA_R6_G2_T0_8X8_AUTHORED_MATERIAL_EXPLORE_TRIAL_V1',
            'authority':AUTHORITY,
            'authorial_exploration_record_id':record_id,
            'original_source_parent_node_count':len(ids),
            'hypothetical_material_strength_by_original_parent':out,
            'verified_bulk_oxide_candidates_not_mineral_phases':oxide_sources,
            'source_original_FEG_sha256':template['source_original_FEG_sha256'],
            'source_original_PRE_sha256':template['source_original_PRE_sha256'],
        'material_column_source_parent_is_NOT_independent_fault_side':True,
        'source_fault_side_materials_qualified':False,
            'source_cold_report_sha256':template['source_cold_report_sha256'],
            'source_PT_report_sha256':template['source_PT_report_sha256'],
            'validated_laboratory_dataset_bytes_independently_inspected':False,
            'natural_ARCANA_mineralogy_or_fluid_state_ratified':False,
            'cannot_compare_J2_continuum_to_triaxial_strength_directly':True,
            'mechanical_solve_authorized':False,'physical_T1':None,
            'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False,'D_024':'ACTIVE'}


def template_for_source(cold,pt):
    """Authoring template retaining precise original IDs, not materialization."""
    extent=cold.get('extent_cells')
    ids=cold.get('source_parent_ids')
    require(extent in (8,16) and type(ids) is list and len(ids)==(extent+1)**2
            and ids==pt.get('original_parent_node_order')
            and set(cold.get('original_T0_source_nodes',{}))==set(map(str,ids))
            and set(pt.get('original_T0_source_nodes',{}))==set(map(str,ids)),
            'MATERIAL_COLD_PT_EXACT_SOURCE_IDS_MISMATCH')
    junction=cold.get('source_actual_local_triple_plate_junctions')
    require(junction==([] if extent==8 else [
                {'parent_node_id':34587,'incident_plates':[5,8,11]}]),
            'MATERIAL_SOURCE_LOCAL_JUNCTION_INCIDENCE_DRIFT')
    return {
        'schema':SCHEMA,'epoch':'T0_210_Ma','extent_cells':extent,
        'source_parent_ids':ids,
        'source_cold_report_sha256':None,  # filled by source replay caller
        'source_PT_report_sha256':None,
        'source_original_FEG_sha256':cold['source_original_FEG_sha256'],
        'source_original_PRE_sha256':cold['source_original_PRE_sha256'],
        'source_actual_local_triple_plate_junctions':junction,
        'shared_parent_nodes_not_side_resolved_rock_materials':True,
        'authorial_selection_confirmed':False,
        'hypothetical_material_classes':[],
        'hypothetical_fluid_state_classes':[],
        'hypothetical_lab_law_registry':[],
        'material_assignment_by_original_parent':{str(i):None for i in ids},
        'nodewise_conditional_PT_reference':{
            str(i):{'source_crust_temperature_k':
                       pt['original_T0_source_nodes'][str(i)]['exact_PRE_temperature_bounds_k']['crust'],
                    'source_moho_conditional_delta_overburden_pa':
                       pt['original_T0_source_nodes'][str(i)]['conditional_moho_delta_overburden_pa'],
                    'actual_rock_phase':None,'actual_pore_pressure_pa':None}
            for i in ids},
        'real_rock_chemistry_mapping_qualified':False,
        'unselected_source_template_not_executable':True,
        'physical_G2_material_assignments':0,
        'mechanical_solve_authorized':False,
        'physical_T1':None,'D_024':'ACTIVE','WORLD_HISTORY_PRODUCTION_AUTHORIZED':False,
    }


def build(*,repo_root,packet8,packet16,handoff,pt_folder,cold_folder):
    """Independently replay source and cold outputs before emitting candidate inputs."""
    from experiments.plate58_deforming_explore_v1 import g2_g3_t0_cold_crust_regime as cold_mod
    from experiments.plate58_deforming_explore_v1 import g2_g3_t0_lithostatic_pt_reference as pt_mod
    from experiments.plate58_deforming_explore_v1.g2_g3_source_to_coupled_handoff import load_packet
    m=manifest(cold_folder,'ARCANA_R6_T0_COLD_CRUST_REGIME_MANIFEST_V1',COLD_FILES)
    cold_reports=[json.loads((Path(cold_folder)/f).read_text()) for f in COLD_FILES[:2]]
    cold_audit=json.loads((Path(cold_folder)/COLD_FILES[2]).read_text())
    expected8,expected16,expected_audit=cold_mod.build(
        repo_root=repo_root,packet8=packet8,packet16=packet16,
        handoff=handoff,pt_folder=pt_folder)
    require(cold_reports==[expected8,expected16] and cold_audit==expected_audit,
            'MATERIAL_COLD_SOURCE_REPLAY_MISMATCH')
    pt_manifest,pt_reports,pt_audit=cold_mod._load_original_pt(pt_folder)
    # Recompute T0 P–T independently as well, not just a manifest hash check.
    r8,r16,ar=pt_mod.build(repo_root,packet8,packet16,handoff)
    require(pt_reports==[r8,r16] and pt_audit==ar,
            'MATERIAL_PT_SOURCE_REPLAY_MISMATCH')
    ix8,_,receipt8=load_packet(packet8,8)
    ix16,_,receipt16=load_packet(packet16,16)
    from experiments.plate58_deforming_explore_v1.g2_g3_physical_source_packet import verify_cross_extent_provider_chain
    verify_cross_extent_provider_chain(ix8,ix16)
    require(cold_reports[0]['source_original_packet_sha256']==receipt8['evidence_manifest_sha256']
            and cold_reports[1]['source_original_packet_sha256']==receipt16['evidence_manifest_sha256'],
            'MATERIAL_SOURCE_PROVENANCE_MISMATCH')
    out=[]
    for n,c,p in ((8,cold_reports[0],r8),(16,cold_reports[1],r16)):
        t=template_for_source(c,p)
        t['source_cold_report_sha256']=sha(Path(cold_folder)/f'REGION_{n}X{n}_COLD_CRUST.json')
        t['source_PT_report_sha256']=sha(Path(pt_folder)/f'REGION_{n}X{n}_SOURCE_PT.json')
        out.append(t)
    a={'schema':'ARCANA_R6_G2_T0_MATERIAL_TRIAL_SOURCE_AUDIT_V1',
       'decision':STATUS,'source_cold_manifest_sha256':sha(Path(cold_folder)/'MANIFEST.json'),
       'source_PT_manifest_sha256':sha(Path(pt_folder)/'MANIFEST.json'),
       'original_source_nodes_8x8':81,'original_source_nodes_16x16':289,
       'source_original_node_overlap_not_independent_count':True,
       'source_8x8_material_assignments':0,'source_16x16_material_assignments':0,
       'physical_mineral_phases_selected':0,  # preserve semantic distinction in report
       'source_pore_pressure_assignments':0,
       'qualified_cold_T_P_rate_constitutive_laws':0,
       'GT95_can_be_applied_to_source_cold_crust':False,
       'earth_2026_quartz_gouge_is_not_ARCANA_fault':True,
       'mechanical_solve_authorized':False,'physical_T1':None,
       'HistoryStore_modified':False,'D_024':'ACTIVE',
       'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False}
    return out[0],out[1],a


def validate_unselected_report(record, extent):
    require(type(record) is dict and record.get('schema')==SCHEMA
            and record.get('extent_cells')==extent
            and record.get('authorial_selection_confirmed') is False
            and record.get('unselected_source_template_not_executable') is True
            and record.get('real_rock_chemistry_mapping_qualified') is False
            and record.get('shared_parent_nodes_not_side_resolved_rock_materials') is True
            and record.get('source_actual_local_triple_plate_junctions')==(
                [] if extent==8 else [{'parent_node_id':34587,'incident_plates':[5,8,11]}])
            and record.get('physical_G2_material_assignments')==0
            and record.get('physical_T1') is None
            and record.get('mechanical_solve_authorized') is False
            and record.get('D_024')=='ACTIVE'
            and record.get('WORLD_HISTORY_PRODUCTION_AUTHORIZED') is False,
            'MATERIAL_UNSELECTED_TEMPLATE_AUTHORITY_TAMPERED')
    ids=record.get('source_parent_ids')
    material=record.get('material_assignment_by_original_parent')
    pt=record.get('nodewise_conditional_PT_reference')
    require(type(ids) is list and len(ids)==len(set(ids))==(extent+1)**2
            and type(material) is dict and type(pt) is dict
            and set(material)==set(pt)==set(map(str,ids))
            and all(v is None for v in material.values())
            and all(type(v) is dict and v.get('actual_rock_phase') is None
                    and v.get('actual_pore_pressure_pa') is None
                    for v in pt.values())
            and all(record.get(k)==[] for k in (
                'hypothetical_material_classes','hypothetical_fluid_state_classes',
                'hypothetical_lab_law_registry')),
            'MATERIAL_UNSELECTED_NODE_ASSIGNMENT_TAMPERED')


def write_once(repo_root,output,files):
    root=Path(repo_root).resolve(); out=Path(output).resolve()
    require(not out.is_relative_to(root) and not out.exists(),
            'MATERIAL_OUTPUT_INSIDE_REPOSITORY_OR_ALREADY_EXISTS')
    require(set(files)==set(FILES)
            and all(v.get('physical_T1') is None
                    and v.get('mechanical_solve_authorized') is False
                    and v.get('D_024')=='ACTIVE' for v in files.values()),
            'MATERIAL_OUTPUT_PHYSICAL_AUTHORITY_FORBIDDEN')
    for extent in (8,16):
        validate_unselected_report(files[f'MATERIAL_{extent}X{extent}_UNSELECTED.json'],extent)
    audit=files['AUDIT.json']
    require(audit.get('schema')=='ARCANA_R6_G2_T0_MATERIAL_TRIAL_SOURCE_AUDIT_V1'
            and audit.get('source_8x8_material_assignments')==0
            and audit.get('source_16x16_material_assignments')==0
            and audit.get('source_pore_pressure_assignments')==0
            and audit.get('qualified_cold_T_P_rate_constitutive_laws')==0
            and audit.get('physical_mineral_phases_selected')==0
            and audit.get('HistoryStore_modified') is False
            and audit.get('WORLD_HISTORY_PRODUCTION_AUTHORIZED') is False,
            'MATERIAL_SOURCE_AUDIT_AUTHORITY_TAMPERED')
    bodies={n:json.dumps(v,indent=2,allow_nan=False)+'\n' for n,v in files.items()}
    out.mkdir(parents=True,exist_ok=False)
    for name,data in bodies.items():
        (out/name).write_text(data,encoding='utf8')
    (out/'MANIFEST.json').write_text(json.dumps({
        'schema':'ARCANA_R6_G2_T0_MATERIAL_TRIAL_SOURCE_MANIFEST_V1',
        'files':{name:hashlib.sha256(data.encode()).hexdigest() for name,data in bodies.items()},
        'no_solver_run':True,'physical_T1':None,'HistoryStore_modified':False,
        'D_024':'ACTIVE','WORLD_HISTORY_PRODUCTION_AUTHORIZED':False,
    },indent=2)+'\n',encoding='utf8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('repo-root','packet-8','packet-16','handoff','pt-reference',
                 'cold-context','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args()
    source_paths=[(folder/f) for folder,files in (
        (a.packet_8,('MANIFEST.json','SOURCE_INDEX.json','UNSELECTED_PHYSICAL_PROPOSAL.json')),
        (a.packet_16,('MANIFEST.json','SOURCE_INDEX.json','UNSELECTED_PHYSICAL_PROPOSAL.json')),
        (a.handoff,('MANIFEST.json','SCENARIO_8X8_UNSELECTED.json','SCENARIO_16X16_UNSELECTED.json','AUDIT.json')),
        (a.pt_reference,('MANIFEST.json',*PT_FILES)),
        (a.cold_context,('MANIFEST.json',*COLD_FILES))) for f in files]
    before=[sha(x) for x in source_paths]
    reports=build(repo_root=a.repo_root,packet8=a.packet_8,packet16=a.packet_16,
                  handoff=a.handoff,pt_folder=a.pt_reference,cold_folder=a.cold_context)
    require(before==[sha(x) for x in source_paths],
            'MATERIAL_SOURCE_EVIDENCE_CHANGED_DURING_ASSEMBLY')
    write_once(a.repo_root,a.output,dict(zip(FILES,reports)))
    print(json.dumps({'decision':STATUS,'original_8x8_nodes':81,
                      'original_16x16_nodes':289,'selected_rock_phases':0,
                      'selected_fluid_pressures':0,'selected_constitutive_laws':0,
                      'independent_explicit_material_trial_engine':True,
                      'physical_T1':None,'mechanical_solve_authorized':False,
                      'D_024':'ACTIVE'}))


if __name__=='__main__':
    main()
