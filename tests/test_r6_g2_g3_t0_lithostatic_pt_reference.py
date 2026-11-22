"""No geological T1: gravity-weight PRE reference and strict source authority."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import pytest

from experiments.plate58_deforming_explore_v1 import g2_g3_t0_lithostatic_pt_reference as m
from experiments.plate58_deforming_explore_v1 import g2_g3_physical_source_packet as packet
from experiments.plate58_deforming_explore_v1 import g2_g3_source_to_coupled_handoff as handoff
from test_r6_g2_g3_physical_source_packet import fixture


def pre():
    return fixture()["pre_by_node"][100000]


def test_piecewise_lithostatic_increment_analytic_and_continuous():
    p=pre(); g=9.82; c=p["crust_thickness_m"]; mtl=p["mantle_lithosphere_thickness_m"]
    rho_c=p["crust_density_kg_m3"]; rho_m=p["mantle_density_kg_m3"]
    assert m.overburden_increment_pa(p,0.,g)==0.
    assert m.overburden_increment_pa(p,c/2,g)==pytest.approx(g*rho_c*c/2)
    assert m.overburden_increment_pa(p,c,g)==pytest.approx(g*rho_c*c)
    assert m.overburden_increment_pa(p,c+mtl/2,g)==pytest.approx(g*(rho_c*c+rho_m*mtl/2))
    assert m.overburden_increment_pa(p,c+mtl,g)==pytest.approx(g*(rho_c*c+rho_m*mtl))


def test_lithostatic_gradients_are_density_times_gravity_each_side():
    p=pre();c=p["crust_thickness_m"];g=9.82
    eps=.01
    deriv_crust=(m.overburden_increment_pa(p,c-eps,g)-m.overburden_increment_pa(p,c-2*eps,g))/eps
    deriv_mantle=(m.overburden_increment_pa(p,c+2*eps,g)-m.overburden_increment_pa(p,c+eps,g))/eps
    assert deriv_crust==pytest.approx(g*p["crust_density_kg_m3"],rel=1e-8)
    assert deriv_mantle==pytest.approx(g*p["mantle_density_kg_m3"],rel=1e-8)


def test_integrated_vertical_overburden_exact_piecewise_independent_formula():
    row=m.evaluate_node(pre(),gravity_m_s2=9.82,lab_temperature_k=(1173.15,1373.15))
    h=pre()["crust_thickness_m"]
    mantle=pre()["mantle_lithosphere_thickness_m"]
    moho=row["conditional_moho_delta_overburden_pa"]
    basal=row["conditional_base_delta_overburden_pa"]
    independent=.5*h*moho+.5*mantle*(moho+basal)
    assert row["integrated_delta_overburden_N_per_m"]==pytest.approx(independent)
    assert row["integrated_delta_overburden_N_per_m"]>0


def test_moho_temperature_jump_reported_without_assuming_continuity():
    p=pre();p["layer1_c1_k_m"]=.02
    row=m.evaluate_node(p,gravity_m_s2=9.82,lab_temperature_k=(100.,2000.))
    assert row["source_temperature_jump_at_moho_mantle_minus_crust_k"] == pytest.approx(900-(300+.02*6500))
    assert row["conditional_moho_delta_overburden_pa"]>0


def test_true_cubic_extrema_interior_not_just_five_samples():
    p=pre();c=p["crust_thickness_m"]
    p["layer1_c1_k_m"]=100./c
    p["layer1_c2_k_m2"]=-100./(c*c)
    result=m.evaluate_node(p,gravity_m_s2=9.82,lab_temperature_k=(320.,330.))
    bounds=result["exact_PRE_temperature_bounds_k"]["crust"]
    assert bounds==pytest.approx([300.,325.])
    assert result["terrestrial_GT95_lab_temperature_only_coverage"]["crust"]["temperature_only_some_overlap"] is True
    assert result["terrestrial_GT95_lab_temperature_only_coverage"]["crust"]["temperature_only_full_layer_covered"] is False


def test_lab_temperature_only_cannot_promote_rock_creep_or_fault_law():
    r=m.evaluate_node(pre(),gravity_m_s2=9.82,lab_temperature_k=(250.,1500.))
    for v in r["terrestrial_GT95_lab_temperature_only_coverage"].values():
        assert v["temperature_only_full_layer_covered"] is True
        assert v["P_rate_water_rock_identity_qualified"] is False
        assert v["mechanism_applicable_to_ARCANA"] is False
    assert r["fault_normal_pressure_pa"] is None
    assert r["pore_pressure_pa"] is None
    assert r["effective_pressure_pa"] is None
    assert r["actual_vertical_stress_pa"] is None
    assert r["mantle_traction_pa"] is None


def test_sampled_profile_retains_both_sides_of_moho_separately():
    r=m.evaluate_node(pre(),gravity_m_s2=9.82,lab_temperature_k=(1173.15,1373.15))
    xs=r["source_depth_pt_samples"]
    assert len(xs)==10
    assert xs[4]["source_depth_m"]==xs[5]["source_depth_m"]
    assert xs[4]["conditional_delta_vertical_overburden_pa"]==xs[5]["conditional_delta_vertical_overburden_pa"]
    assert xs[4]["layer"]=="crust" and xs[5]["layer"]=="mantle_lithosphere"
    assert all(x["source_depth_is_not_actual_fault_depth"] is True for x in xs)


@pytest.mark.parametrize("name,value",[
    ("crust_density_kg_m3",0.),("crust_density_kg_m3",-1.),
    ("mantle_density_kg_m3",float('nan')),
    ("crust_thickness_m",0.),("mantle_lithosphere_thickness_m",float('inf')),
    ("layer1_z0_m",1.),("layer2_z1_m",-1.),
    ("layer1_c0_k",-10.),("layer2_c1_k_m",float('nan')),
])
def test_numerical_input_invalid_fails_closed(name,value):
    p=pre();p[name]=value
    with pytest.raises((m.OverburdenInputError,ValueError)):
        m.evaluate_node(p,gravity_m_s2=9.82,lab_temperature_k=(1173.15,1373.15))


@pytest.mark.parametrize("depth",[-1.,106501.,float('nan'),float('inf')])
def test_outside_source_model_depth_rejected(depth):
    with pytest.raises(m.OverburdenInputError,match="DEPTH_OUTSIDE"):
        m.overburden_increment_pa(pre(),depth,9.82)


@pytest.mark.parametrize("gravity",[-9.82,0.,float('nan'),float('inf'),None,True])
def test_invalid_gravity_rejected(gravity):
    with pytest.raises(m.OverburdenInputError):
        m.overburden_increment_pa(pre(),0,gravity)


def test_unselected_exact_source_region_emits_physical_number_not_a_stress():
    data=fixture(8,parent_34587_in_8=True)
    idx,pro=packet.create_packet(**data)
    receipt={"evidence_manifest_sha256":"a"*64,"source_index_sha256":"b"*64}
    out=m.compute_region(idx,pro,receipt,extent=8,gravity_m_s2=9.82,
                         lab_temperature_k=(1173.15,1373.15))
    assert out["source_node_count"]==81
    assert len(out["original_T0_source_nodes"])==81
    assert out["summary"]["GT95_arcana_rock_assignments"]==0
    assert out["summary"]["qualified_basal_traction_facets"]==0
    assert out["pressure_reference_is_delta_from_model_surface_not_absolute"]
    assert out["conditional_overburden_not_mechanical_vertical_traction"]
    assert out["physical_T1"] is None and out["D_024"]=="ACTIVE"
    assert 34587 in out["original_parent_node_order"]
    assert json.loads(json.dumps(out,allow_nan=False))==out


def test_16x16_is_domain_extent_not_claimed_mesh_convergence():
    data=fixture(16)
    idx,pro=packet.create_packet(**data)
    out=m.compute_region(idx,pro,{"evidence_manifest_sha256":"a"*64,
        "source_index_sha256":"b"*64},extent=16,
        gravity_m_s2=9.82,lab_temperature_k=(1173.15,1373.15))
    assert out["source_node_count"]==289
    assert out["source_full_basal_facet_count"]==512
    assert out["source_external_cut_edge_count"]==64
    assert out["mechanical_solve_authorized"] is False


def test_missing_original_thermal_parent_not_imputed():
    idx,pro=packet.create_packet(**fixture())
    idx["source_original_PRE_model_T0_thermal_profiles_by_parent_node"].pop(str(idx["original_parent_node_order"][0]))
    with pytest.raises(m.OverburdenInputError,match="COVERAGE_INVALID"):
        m.compute_region(idx,pro,{"evidence_manifest_sha256":"a"*64,
            "source_index_sha256":"b"*64},extent=8,
            gravity_m_s2=9.82,lab_temperature_k=(1173.15,1373.15))


def make_synthetic_fair_evidence(tmp_path):
    root=tmp_path/"repo"; root.mkdir()
    packets={}
    for extent in (8,16):
        idx,pro=packet.create_packet(**fixture(extent,parent_34587_in_8=(extent==8)))
        path=tmp_path/f"packet_{extent}"
        packet.write_once(root,path,idx,pro)
        packets[extent]=path
    a,b,audit=handoff.compile_pair(packets[8],packets[16])
    handoff_dir=tmp_path/"handoff"
    handoff.write_once(root,handoff_dir,{
        "SCENARIO_8X8_UNSELECTED.json":a,
        "SCENARIO_16X16_UNSELECTED.json":b,
        "AUDIT.json":audit,
    })
    return root,packets,handoff_dir


def test_full_synthetic_sha_chain_build_reports_pressure_without_physics(tmp_path,monkeypatch):
    root,packets,hand=make_synthetic_fair_evidence(tmp_path)
    monkeypatch.setattr(m,"source_gravity_and_lab",lambda root:(9.82,(1173.15,1373.15),
        {"scenario_git_blob":"synthetic_test_only","gravity_m_s2":9.82}))
    a,b,audit=m.build(root,packets[8],packets[16],hand)
    assert (a["source_node_count"],b["source_node_count"])==(81,289)
    assert audit["original_shared_parent_node_count"]>=1
    assert audit["region_extent_comparison_is_not_grid_convergence"] is True
    assert audit["physical_T1"] is None
    assert not audit["G3_external_basal_GPE_loads_derived"]
    assert all(v["absolute_surface_pressure_pa"] is None for v in b["original_T0_source_nodes"].values())
    assert not audit["physical_G2_material_law_or_rock_selected"]


@pytest.mark.parametrize("attack",["handoff_sha","handoff_material","source_index_sha","handoff_audit"])
def test_upstream_sha_or_authority_mutation_fails_closed(tmp_path,monkeypatch,attack):
    root,packets,hand=make_synthetic_fair_evidence(tmp_path)
    monkeypatch.setattr(m,"source_gravity_and_lab",lambda root:(9.82,(1173.15,1373.15),{"synthetic_fixture":True}))
    if attack=="handoff_sha":
        (hand/"SCENARIO_8X8_UNSELECTED.json").write_text("{}")
    elif attack=="handoff_material":
        path=hand/"SCENARIO_8X8_UNSELECTED.json"
        v=json.loads(path.read_text())
        key=next(iter(v["candidate_material_by_parent_node"]))
        v["candidate_material_by_parent_node"][key]={"rock":"invented"}
        path.write_text(json.dumps(v))
    elif attack=="source_index_sha":
        (packets[8]/"SOURCE_INDEX.json").write_text("{}")
    else:
        path=hand/"AUDIT.json"
        v=json.loads(path.read_text());v["material_assignments"]=1
        path.write_text(json.dumps(v))
    with pytest.raises((m.OverburdenInputError,ValueError,KeyError)):
        m.build(root,packets[8],packets[16],hand)


def test_write_once_hashes_and_never_overwrites(tmp_path):
    idx,pro=packet.create_packet(**fixture())
    a=m.compute_region(idx,pro,{"evidence_manifest_sha256":"a"*64,
            "source_index_sha256":"b"*64},extent=8,
            gravity_m_s2=9.82,lab_temperature_k=(1173.15,1373.15))
    root=tmp_path/"repository";root.mkdir()
    out=tmp_path/"evidence"
    payload={"REGION_8X8_SOURCE_PT.json":a,
             "REGION_16X16_SOURCE_PT.json":copy.deepcopy(a),
             "AUDIT.json":{"mechanical_solve_authorized":False,"physical_T1":None,"HistoryStore_modified":False,"D_024":"ACTIVE"}}
    man=m.write_once(root,out,payload)
    for name,digest in man["files"].items():
        assert m.sha256(out/name)==digest
    with pytest.raises(m.OverburdenInputError,match="EVIDENCE_ALREADY_EXISTS"):
        m.write_once(root,out,payload)
    with pytest.raises(m.OverburdenInputError,match="EVIDENCE_INSIDE_REPOSITORY"):
        m.write_once(root,root/"bad",payload)


def test_terrestrial_source_gravity_pinned_authority_fixture(tmp_path,monkeypatch):
    p=tmp_path/m.SCENARIO_PATH;p.parent.mkdir(parents=True)
    body={"schema":"ARCANA_R6_G2_G3_REGIONAL_PAIRED_PHYSICAL_SCENARIO_V1",
          "selected_model":{"physical_execution_authorized":False},
          "g3":{"gpe":{"gravity_authority":"CANONICAL_PARAMETER","gravity_m_s2":9.82}},
          "g2":{"literature_references":{"quartzite_GT95":{
          "authority":"LITERATURE_ANALOGUE_EXPERIMENT",
          "arcana_rock_identity_ratified":False,"valid_temperature_k":[1173.15,1373.15],
          "doi":"10.1016/0040-1951(95)00011-B"}}}}
    raw=(json.dumps(body)+"\n").encode();p.write_bytes(raw)
    monkeypatch.setattr(m,"SCENARIO_BLOB",m.gitblob(raw))
    g,interval,meta=m.source_gravity_and_lab(tmp_path)
    assert g==pytest.approx(9.82) and interval==(1173.15,1373.15)
    assert meta["lab_rock_is_not_ARCANA_rock_identity"]
    body["g3"]["gpe"]["gravity_m_s2"]=True
    changed=(json.dumps(body)+"\n").encode();p.write_bytes(changed)
    monkeypatch.setattr(m,"SCENARIO_BLOB",m.gitblob(changed))
    with pytest.raises(m.OverburdenInputError,match="INVALID_POSITIVE"):
        m.source_gravity_and_lab(tmp_path)
    # A valid value with wrong blob is never accepted.
    p.write_bytes(raw)
    with pytest.raises(m.OverburdenInputError,match="BLOB_DRIFT"):
        m.source_gravity_and_lab(tmp_path)
