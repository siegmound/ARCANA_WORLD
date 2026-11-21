"""Source-facet T0 thermal intersection is NOT an ARCANA fault-law assignment."""
import json
from collections import defaultdict

import pytest
from experiments.plate58_deforming_explore_v1.g2_g3_t0_contact_material_applicability import (
    ApplicabilityInputError, isotherm_depths_m, survey_contact_face_source,
    _validate_lab_stability_report, discover_fair_sources, build, LAB_T_K,
)
from experiments.plate58_deforming_explore_v1.g2_g3_source_coupled_runner import sha


def pre(c0=280., grad=0.02):
    return {
        "node_id":1.,
        "crust_thickness_m":30000.,
        "mantle_lithosphere_thickness_m":60000.,
        "crust_density_kg_m3":2800.,
        "mantle_density_kg_m3":3300.,
        "layer1_z0_m":0.,"layer1_z1_m":30000.,
        "layer1_c0_k":c0,"layer1_c1_k_m":grad,
        "layer1_c2_k_m2":0.,"layer1_c3_k_m3":0.,
        "layer2_z0_m":30000.,"layer2_z1_m":90000.,
        "layer2_c0_k":1200.,"layer2_c1_k_m":0.01,
        "layer2_c2_k_m2":0.,"layer2_c3_k_m3":0.,
        "crust_material_code":3.,
        "mantle_material_code":4.,
        "material_configuration_code":17.,
        "mixed_support":0.,
    }


def _region8():
    """Artificial 8x8 P1 grid: 81 real-style parent IDs; 12 interplate edges."""
    W=8
    thresholds=[4,5,4,5,4,4,4,4]
    faces=[];plates=[]
    for i in range(W):
        for j in range(W):
            a=i*(W+1)+j+1
            b=a+1
            c=(i+1)*(W+1)+j+1
            d=c+1
            faces.extend([(a,b,d),(a,d,c)])
            plates.extend([5 if j<thresholds[i] else 8]*2)
    incidence=defaultdict(list)
    for f,plate in zip(faces,plates,strict=True):
        for e in ((f[0],f[1]),(f[1],f[2]),(f[2],f[0])):
            incidence[tuple(sorted(e))].append(plate)
    edges=[e for e,v in incidence.items()
           if len(v)==2 and len(set(v))==2]
    assert len(edges)==12
    source=[{"source_boundary_id":f"R6BND-T0-SYNTH-{k:03d}",
             "source_edge_node_ids":list(e),
             "plate_pair":[5,8]} for k,e in enumerate(edges)]
    region={"parent_node_ids":list(range(1,82)),
            "source_contact_edges":source,"source_contact_count":12}
    cols={n:{**pre(),"node_id":float(n)} for n in range(1,82)}
    return region,cols,faces,plates


def test_exact_isotherm_depth_from_original_polynomial():
    assert isotherm_depths_m(pre())==pytest.approx([657.5],abs=1e-8)


def test_isotherm_absent_if_cold_constant_column():
    assert isotherm_depths_m(pre(c0=280,grad=0.))==[]


def test_isotherm_whole_layer_ambiguity_does_not_invent_single_fault_depth():
    assert isotherm_depths_m(pre(c0=LAB_T_K,grad=0.)) is None


def test_isotherm_quadratic_with_two_distinct_crustal_crossings():
    row=pre(c0=280.,grad=200./30000.)
    row["layer1_c2_k_m2"]=-200./30000.**2
    val=isotherm_depths_m(row)
    assert len(val)==2 and 0<val[0]<val[1]<30000.
    for z in val:
        assert row["layer1_c0_k"]+z*(row["layer1_c1_k_m"]+
               z*row["layer1_c2_k_m2"])==pytest.approx(LAB_T_K,abs=1e-6)


@pytest.mark.parametrize("bad",["nan_coeff","invalid_target","zero_depth"])
def test_isotherm_fail_closed_input(bad):
    row=pre()
    if bad=="nan_coeff":row["layer1_c1_k_m"]=float("nan")
    if bad=="invalid_target":
        with pytest.raises(ApplicabilityInputError,match="TARGET_TEMPERATURE"):
            isotherm_depths_m(row,target_k=0.)
        return
    if bad=="zero_depth":row["layer1_z1_m"]=0.
    with pytest.raises(ApplicabilityInputError):
        isotherm_depths_m(row)


def test_original_source_two_owner_faces_preserved_no_mineralogy_inferred():
    r,p,faces,plates=_region8()
    out=survey_contact_face_source(r,p,faces,plates,width=8)
    assert out["source_original_nodes"]==81
    assert out["source_original_facets"]==128
    assert out["source_exact_contact_edges"]==12
    assert out["source_owner_face_sides"]==24
    assert out["contacts_with_both_side_nodewise_isotherm"]==12
    assert out["all_mathematically_crossed_isotherm_depths_min_max_m"]==pytest.approx([657.5,657.5])
    assert out["source_PRE_role_codes_cannot_identify_gouge_or_hydration"]
    assert out["arcana_friction_materials_assigned"]==0
    assert out["physical_T1"] is None
    for x in out["source_contacts"]:
        assert len(x["source_original_faces"])==2
        assert x["original_shared_nodes_not_split"]
        assert x["actual_fault_shear_traction_pa"] is None
        assert x["lab_rate_state_fitted_rows_assigned_to_contact"]==0
        for side in x["source_original_faces"]:
            assert len(side["source_face_vertex_records"])==3
            assert side["actual_gouge_mineralogy"] is None
            assert side["fault_effective_normal_stress_pa"] is None
            assert side["fault_depth_m"] is None


def test_source_plate_pair_tampering_rejected():
    r,p,faces,plates=_region8()
    r["source_contact_edges"][0]["plate_pair"]=[5,11]
    with pytest.raises(ValueError):
        survey_contact_face_source(r,p,faces,plates,width=8)


def test_missing_original_pre_column_rejected():
    r,p,faces,plates=_region8()
    del p[4]
    with pytest.raises(ApplicabilityInputError,match="NODE_TRIANGLE_PLATE_SCOPE"):
        survey_contact_face_source(r,p,faces,plates,width=8)


def test_source_thermal_outside_20c_stays_not_qualified():
    r,p,faces,plates=_region8()
    for node in p.values():
        node["layer1_c0_k"]=280.
        node["layer1_c1_k_m"]=0.
    out=survey_contact_face_source(r,p,faces,plates,width=8)
    assert out["contacts_with_both_side_nodewise_isotherm"]==0
    assert out["arcana_friction_materials_assigned"]==0


def _lab_fixture(tmp_path):
    d=tmp_path/"LAB";d.mkdir()
    from experiments.plate58_deforming_explore_v1.g2_g3_t0_contact_material_applicability import RSF_SOURCE_SHA
    report={
        "schema":"ARCANA_R6_G2_G3_PANGAEA921284_NORMALIZED_RSF_STABILITY_V1",
        "source_sha256":RSF_SOURCE_SHA,
        "mechanical_solve_authorized":False,"physical_T1":None,
        "rows":[{"source_line":n} for n in range(66)],
        "inventory":{"fitted_model_rows":66,
                     "pressure_values_assigned":0,
                     "arcana_faults_assigned":0,
                     "source_row_qualification_counts":{"LAB_TEST_ONLY":66}},
    }
    (d/"REPORT.json").write_text(json.dumps(report))
    (d/"MANIFEST.json").write_text(json.dumps({
        "schema":"ARCANA_R6_G2_G3_NORMALIZED_RSF_STABILITY_MANIFEST_V1",
        "files":{"REPORT.json":sha(d/"REPORT.json")},
        "source_sha256":RSF_SOURCE_SHA,
        "no_solver_run":True,"no_T1":True,"no_canonical_promotion":True
    }))
    return d


def test_previous_lab_report_hash_and_physics_authority_verified(tmp_path):
    d=_lab_fixture(tmp_path)
    report,rsha,msha=_validate_lab_stability_report(d)
    assert report["inventory"]["fitted_model_rows"]==66
    assert rsha==sha(d/"REPORT.json")
    assert msha==sha(d/"MANIFEST.json")


def test_previous_lab_report_tamper_fails_closed(tmp_path):
    d=_lab_fixture(tmp_path)
    report=json.loads((d/"REPORT.json").read_text())
    report["inventory"]["arcana_faults_assigned"]=1
    (d/"REPORT.json").write_text(json.dumps(report))
    with pytest.raises(ApplicabilityInputError,match="RSF_PUBLISHED_SOURCE_REPORT_INVALID"):
        _validate_lab_stability_report(d)


def test_previous_lab_pressure_promotion_fails_closed(tmp_path):
    d=_lab_fixture(tmp_path)
    report=json.loads((d/"REPORT.json").read_text())
    report["inventory"]["pressure_values_assigned"]=1
    (d/"REPORT.json").write_text(json.dumps(report))
    man=json.loads((d/"MANIFEST.json").read_text())
    man["files"]["REPORT.json"]=sha(d/"REPORT.json")
    (d/"MANIFEST.json").write_text(json.dumps(man))
    with pytest.raises(ApplicabilityInputError,match="RSF_SOURCE_AUTHORITY_PROMOTED"):
        _validate_lab_stability_report(d)


def test_preexisting_output_directory_is_never_overwritten(tmp_path):
    output=tmp_path/"EXISTING";output.mkdir()
    with pytest.raises(ApplicabilityInputError,match="OUTPUT_EXISTS_NO_OVERWRITE"):
        build(tmp_path/"MISSING",tmp_path/"MISSING",tmp_path/"MISSING",output)


def test_source_discovery_fails_closed_when_missing(tmp_path):
    with pytest.raises(ApplicabilityInputError,match="SOURCE_PROVIDER_MISSING_OR_AMBIGUOUS"):
        discover_fair_sources(tmp_path)


def test_source_discovery_requires_real_evidence_directory(tmp_path):
    with pytest.raises(ApplicabilityInputError,match="EVIDENCE_ROOT_MISSING"):
        discover_fair_sources(tmp_path/"absent")
