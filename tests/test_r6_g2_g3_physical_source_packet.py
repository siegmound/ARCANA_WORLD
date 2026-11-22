"""R6 source-keyed G2/G3 package; fixtures are NEVER physical ARCANA sources."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from experiments.plate58_deforming_explore_v1 import g2_g3_physical_source_packet as m

ROOT = Path(__file__).resolve().parents[1]


def matrix():
    return {
        "source_scopes": [
            {"extent_cells": 8, "original_parent_nodes": 81,
             "core_facets": 8, "exterior_facets": 120,
             "original_basal_facets_required": 128, "cut_edge_inputs_required": 32},
            {"extent_cells": 16, "original_parent_nodes": 289,
             "core_facets": 8, "exterior_facets": 504,
             "original_basal_facets_required": 512, "cut_edge_inputs_required": 64},
        ],
        "groups": [{"id": t, "required": [t]}
                   for t in ("g2_material_and_phases", "g2_pressure_water",
                             "g2_lab_law_and_coverage", "g3_outer_cut",
                             "g3_full_basal", "g3_gpe", "interface_fault",
                             "solver_compatibility")],
    }


def fixture(extent=8, *, parent_34587_in_8=False):
    size = extent+1
    ids = [100000+i for i in range(size*size)]
    if extent==16 or parent_34587_in_8:
        ids[len(ids)//2] = 34587
    tr = {}
    tid = 500000
    for row in range(extent):
        for col in range(extent):
            a,b,c,d = (ids[row*size+col], ids[row*size+col+1],
                       ids[(row+1)*size+col], ids[(row+1)*size+col+1])
            tr[tid]=(a,b,c)
            tr[tid+1]=(b,d,c)
            tid+=2
    core = dict(list(tr.items())[:8])
    ext = dict(list(tr.items())[8:])
    cut=[]
    pairs=[]
    for i in range(extent):
        pairs.extend([(ids[i],ids[i+1]),
                      (ids[extent*size+i],ids[extent*size+i+1]),
                      (ids[i*size],ids[(i+1)*size]),
                      (ids[i*size+extent],ids[(i+1)*size+extent])])
    for a,b in pairs:
        cut.append({"source_edge_id": ":".join(map(str, sorted((a,b)))),
                    "source_parent_node_ids": [a,b],
                    "side": "SYNTHETIC_FIXTURE", "adjacent_plate_id": 5})
    pre = {}
    for n in ids:
        row = {"node_id": n, "material_configuration_code": 1,
               "synthetic_PRE_fixture": True,
               "crust_thickness_m": 6500.,
               "mantle_lithosphere_thickness_m": 100000.,
               "crust_density_kg_m3": 2890., "mantle_density_kg_m3": 3300.,
               "layer1_z0_m": 0., "layer1_z1_m": 6500.,
               "layer2_z0_m": 6500., "layer2_z1_m": 106500.,
               "layer1_c0_k": 300., "layer2_c0_k": 900.}
        for layer in (1, 2):
            row.update({f"layer{layer}_c1_k_m": 0.,
                        f"layer{layer}_c2_k_m2": 0.,
                        f"layer{layer}_c3_k_m3": 0.})
        pre[n] = row
    hashes={key:"a"*64 for key in (
        "multiscale_manifest_sha256","interface_manifest_sha256",
        "nodal_manifest_sha256","force_manifest_sha256",
        "original_FEG_sha256","original_PRE_sha256")}
    if extent==16:
        hashes["original_FEG_sha256"]="b"*64
        hashes["original_PRE_sha256"]="c"*64
    return dict(extent=extent,parent_ids=ids,core_triangles=core,
                exterior_triangles=ext,source_cut_edges=cut,
                pre_by_node=pre,
                source_3plus_plate_junctions=(
                    [{"parent_node_id":34587,"incident_plates":[5,8,11]}]
                    if extent==16 else []),
                source_hashes=hashes,matrix=matrix())


@pytest.mark.parametrize("extent",[8,16])
def test_full_source_original_support_compiles_with_explicit_null_physics(extent):
    index, proposal=m.create_packet(**fixture(extent))
    expected=(81,128,8,120,32) if extent==8 else (289,512,8,504,64)
    c=index["counts"]
    assert tuple(c[key] for key in (
        "original_parent_nodes","source_original_full_basal_triangles",
        "source_core_basal_triangles","source_exterior_basal_triangles",
        "original_external_cut_edges"))==expected
    assert len(index["source_pre_record_sha256_by_parent_node"])==expected[0]
    assert len(index["source_original_PRE_model_T0_thermal_profiles_by_parent_node"])==expected[0]
    assert all(len(c)==16 for c in
               index["source_original_PRE_model_T0_thermal_profiles_by_parent_node"].values())
    assert len(proposal["full_basal_tangential_normal_load_Pa"])==expected[1]
    assert index["source_actual_3plus_plate_junctions"] == (
        [] if extent==8 else
        [{"parent_node_id":34587,"incident_plates":[5,8,11]}])
    assert index["source_parent_34587_present_in_footprint"] == (extent==16)
    assert all(v is None for v in proposal["outer_cut_physical_traction_N_per_m"].values())
    assert proposal["sided_fault_transmission_and_triple_junction"] is None
    assert proposal["physical_T1"] is None
    assert json.loads(json.dumps([index,proposal],allow_nan=False))==[index,proposal]
    m.verify_unselected(index,proposal)


def test_parent_34587_can_be_in_8x8_without_three_plate_junction():
    # Regresses the original FAIR NEW01 8x8 readback failure. A parent-node
    # identifier is not an assertion of local three-plate topology.
    index, proposal = m.create_packet(**fixture(8, parent_34587_in_8=True))
    assert index["source_parent_34587_present_in_footprint"] is True
    assert index["source_actual_3plus_plate_junctions"] == []
    assert len(index["original_parent_node_order"]) == 81
    assert proposal["sided_fault_transmission_and_triple_junction"] is None
    assert proposal["physical_T1"] is None
    m.verify_unselected(index, proposal)


def test_cross_extent_shared_manifests_and_distinct_regional_feg_pre():
    index8, _ = m.create_packet(**fixture(8, parent_34587_in_8=True))
    index16, _ = m.create_packet(**fixture(16))
    m.verify_cross_extent_provider_chain(index8, index16)
    assert index8["source_hashes"]["original_FEG_sha256"] != (
        index16["source_hashes"]["original_FEG_sha256"])
    assert index8["source_hashes"]["original_PRE_sha256"] != (
        index16["source_hashes"]["original_PRE_sha256"])
    # A mismatched upstream source chain cannot masquerade as a single T0.
    changed = copy.deepcopy(index16)
    changed["source_hashes"]["interface_manifest_sha256"] = "f"*64
    with pytest.raises(m.PhysicalSourcePacketError,
                       match="UPSTREAM_MANIFEST_DRIFT"):
        m.verify_cross_extent_provider_chain(index8, changed)
    # Likewise a reused geometry/PRE hash between distinct extents is not
    # acceptable; those artifacts have different source support sizes.
    changed = copy.deepcopy(index16)
    changed["source_hashes"]["original_PRE_sha256"] = (
        index8["source_hashes"]["original_PRE_sha256"])
    with pytest.raises(m.PhysicalSourcePacketError,
                       match="REGIONAL_FEG_PRE_NOT_DISTINCT"):
        m.verify_cross_extent_provider_chain(index8, changed)


def test_repeat_is_bitwise_deterministic():
    assert m.create_packet(**fixture()) == m.create_packet(**fixture())


def test_1000year_thermal_pilot_not_passed_as_natural_t0():
    index,proposal=m.create_packet(**fixture())
    assert index["thermal_reference_is_not_100y_or_1000y_synthetic_pilot_output"]
    assert index["source_PRE_is_authored_thermal_material_model_not_natural_mineralogy"]
    assert proposal["source_model_parameters_are_not_natural_properties"]
    assert proposal["input_gaps_are_UNKNOWN_not_zero"]


def test_source_matrix_pin_and_authority_from_real_repository():
    x=m.source_matrix(ROOT)
    assert x["schema"]=="ARCANA_R6_G2_G3_INTEGRATED_PHYSICAL_PROVIDER_MATRIX_V1"
    assert all(s["status"]=="SOURCE_AUTHORITY_GAP" for s in x["groups"])
    assert x["authority"]["physical_T1"] is None


@pytest.mark.parametrize("attack",[
    "node_count","duplicate_node","missing_basal","duplicate_triangle",
    "invalid_triangle_owner","triangle_repeated_vertex","missing_pre",
    "fake_pre_owner","cut_missing","cut_duplicate","cut_invented_id",
    "cut_outside_parent","source_sha_absent","source_sha_nonhex",
    "invented_three_plate_junction_8","missing_triple_junction_16",
    "malformed_junction_record","wrong_junction_plates",
    "extent_unsupported",
])
def test_source_integrity_fail_closed(attack):
    x=fixture(16 if attack in (
        "missing_triple_junction_16","wrong_junction_plates") else 8)
    if attack=="node_count":x["parent_ids"].pop()
    if attack=="duplicate_node":x["parent_ids"][0]=x["parent_ids"][1]
    if attack=="missing_basal":x["exterior_triangles"].pop(next(iter(x["exterior_triangles"])))
    if attack=="duplicate_triangle":
        i=next(iter(x["core_triangles"]))
        x["exterior_triangles"][i]=x["core_triangles"][i]
    if attack=="invalid_triangle_owner":
        t=next(iter(x["core_triangles"]))
        x["core_triangles"][t]=(9999999,*x["core_triangles"][t][1:])
    if attack=="triangle_repeated_vertex":
        t=next(iter(x["core_triangles"]))
        x["core_triangles"][t]=(x["parent_ids"][0],)*3
    if attack=="missing_pre": x["pre_by_node"].pop(next(iter(x["pre_by_node"])))
    if attack=="fake_pre_owner":
        k=next(iter(x["pre_by_node"]))
        x["pre_by_node"][k]["node_id"]=0
    if attack=="cut_missing":x["source_cut_edges"].pop()
    if attack=="cut_duplicate":
        x["source_cut_edges"][1]=copy.deepcopy(x["source_cut_edges"][0])
    if attack=="cut_invented_id": x["source_cut_edges"][0]["source_edge_id"]="1:2"
    if attack=="cut_outside_parent":x["source_cut_edges"][0]["source_parent_node_ids"]=[99999,100000]
    if attack=="source_sha_absent":x["source_hashes"].pop("original_FEG_sha256")
    if attack=="source_sha_nonhex":x["source_hashes"]["original_FEG_sha256"]="z"*64
    if attack=="invented_three_plate_junction_8":
        x["source_3plus_plate_junctions"]=[{
            "parent_node_id":x["parent_ids"][0],"incident_plates":[5,8,11]}]
    if attack=="missing_triple_junction_16":
        x["source_3plus_plate_junctions"]=[]
    if attack=="malformed_junction_record":
        x["source_3plus_plate_junctions"]=[{
            "parent_node_id":x["parent_ids"][0],"incident_plates":[5,8]}]
    if attack=="wrong_junction_plates":
        x["source_3plus_plate_junctions"][0]["incident_plates"]=[5,8,12]
    if attack=="extent_unsupported":x["extent"]=9
    with pytest.raises(m.PhysicalSourcePacketError):
        m.create_packet(**x)


@pytest.mark.parametrize("attack",[
    "fake_physical_t1","material_zero","fake_water_zero",
    "invented_cut_force","fake_sided_fault","fake_gpe",
    "declare_authorized","unmatched_source_hash","fake_status",
])
def test_unselected_scenario_cannot_fake_physical_inputs(attack):
    idx,pro=m.create_packet(**fixture())
    if attack=="fake_physical_t1":pro["physical_T1"]={"temperature_k":300}
    if attack=="material_zero":pro["material_rock_phase_by_parent_node"][str(idx["original_parent_node_order"][0])]=0
    if attack=="fake_water_zero":pro["water_effective_pressure_by_parent_node"][str(idx["original_parent_node_order"][0])] = {"pore_pressure_pa":0}
    if attack=="invented_cut_force":pro["outer_cut_physical_traction_N_per_m"][next(iter(pro["outer_cut_physical_traction_N_per_m"]))]=[0,0,0]
    if attack=="fake_sided_fault":pro["sided_fault_transmission_and_triple_junction"]="YES"
    if attack=="fake_gpe":pro["GPE_full_domain_vertical_and_pressure_support"]={"pressure_pa":0}
    if attack=="declare_authorized":pro["physical_solve_authorized"]=True
    if attack=="unmatched_source_hash":pro["source_index_sha256"]="f"*64
    if attack=="fake_status":pro["remaining_physical_groups"]["g3_full_basal"]["status"]="PASS"
    with pytest.raises(m.PhysicalSourcePacketError):
        m.verify_unselected(idx,pro)


def test_write_once_retains_exact_hashes_and_refuses_overwrite(tmp_path):
    idx,pro=m.create_packet(**fixture())
    repo=tmp_path/"repo"
    repo.mkdir()
    out=tmp_path/"FAIR_EVIDENCE"
    m.write_once(repo,out,idx,pro)
    man=json.loads((out/"MANIFEST.json").read_text())
    assert man["physical_T1"] is None
    assert man["HistoryStore_mutations"]==0
    assert man["physical_solve_authorized"] is False
    for f,sha in man["files"].items():
        assert hashlib.sha256((out/f).read_bytes()).hexdigest()==sha
    with pytest.raises(m.PhysicalSourcePacketError,match="EVIDENCE_EXISTS"):
        m.write_once(repo,out,idx,pro)


def test_output_inside_repo_is_not_allowed(tmp_path):
    idx,pro=m.create_packet(**fixture())
    with pytest.raises(m.PhysicalSourcePacketError,match="OUTSIDE_REPOSITORY"):
        m.write_once(tmp_path,tmp_path/"inside",idx,pro)


def test_authoritative_source_matrix_genuine_pin_failure(tmp_path):
    p=tmp_path/m.MATRIX
    p.parent.mkdir(parents=True)
    p.write_bytes((ROOT/m.MATRIX).read_bytes()+b"\n")
    with pytest.raises(m.PhysicalSourcePacketError,match="SOURCE_MATRIX_DRIFT"):
        m.source_matrix(tmp_path)


def chain_fixture(double=False, alias=False):
    def stage(a):
        return a*64
    records={
        "multiscale": [(stage("a"),Path("multiA"),{})],
        "interface": [(stage("b"),Path("interA"),{
            "source_multiscale_manifest_sha256":stage("a")})],
        "nodal": [(stage("c"),Path("nodA"),{
            "source_multiscale_manifest_sha256":stage("a"),
            "source_interface_manifest_sha256":stage("b")})],
        "force": [(stage("d"),Path("forceA"),{
            "parent_multiscale_manifest_sha256":stage("a"),
            "parent_interface_manifest_sha256":stage("b"),
            "parent_G2_binding_manifest_sha256":stage("c")})],
    }
    if double:
        for key,rows in list(records.items()):
            h,p,r=rows[0]
            replacer=dict(a="e",b="f",c="1",d="2")
            nr={k:replacer.get(v[0],v[0])*64 if len(v)==64 else v
                for k,v in r.items()}
            rows.append((replacer.get(h[0],h[0])*64,Path(str(p)+"_B"),nr))
    if alias:
        h,p,r=records["multiscale"][0]
        records["multiscale"].append((h,Path("multiB"),r))
    return records


def test_provider_discovery_selects_single_exact_sha_chain():
    p=m.select_unique_source_chain(chain_fixture())
    assert p=={"multiscale":Path("multiA"),
               "interface":Path("interA"),
               "nodal":Path("nodA"),"force":Path("forceA")}


def test_provider_discovery_accepts_identical_multiscale_alias_only():
    assert m.select_unique_source_chain(chain_fixture(alias=True))[
        "multiscale"]==Path("multiA")


def test_provider_discovery_rejects_ambiguous_distinct_valid_chains():
    with pytest.raises(m.PhysicalSourcePacketError,match="AMBIGUOUS"):
        m.select_unique_source_chain(chain_fixture(double=True))


def test_provider_discovery_rejects_broken_provenance_chain():
    x=chain_fixture()
    x["force"][0][2]["parent_G2_binding_manifest_sha256"]="0"*64
    with pytest.raises(m.PhysicalSourcePacketError,match="MISSING_OR_AMBIGUOUS"):
        m.select_unique_source_chain(x)
