"""Mock original provider SOURCE INPUTS only; never a physical solve.

The synthetic fixtures are deliberately full-sized (81/289) so the exact
source adapter shape and plate-incident node classification are covered.
"""
from types import SimpleNamespace
import pytest

import experiments.plate58_deforming_explore_v1.g2_g3_source_coupled_runner as m
from experiments.plate58_deforming_explore_v1.g2_g3_coupled_weak_form import (
    CoupledAssemblyError,
)


def synthetic_provider_fixture(monkeypatch, extent):
    ids = [100000+i for i in range((extent+1)**2)]
    ids[len(ids)//2] = 34587
    extids = ids[:-1]
    nt = 2*extent*extent
    tids = list(range(5000,5000+nt))
    ext_tri = tids[:nt-8]
    triples = {str(t):{"parent_node_ids": [
        extids[i%len(extids)],
        extids[(i+1)%len(extids)],
        extids[(i+2)%len(extids)]]}
        for i,t in enumerate(ext_tri)}
    incidence = ([] if extent==8 else [
        {"parent_node_id":34587,"incident_plates":[5,8,11]}])
    manifest_shas = {k:k[0]*64 for k in ("multiscale","interface","nodal","force")}
    # 'multiscale' starts with m; 'interface' i; 'nodal' n; 'force' f.
    region={"cell_extent_per_side":extent, "parent_node_ids":ids,
            "parent_triangle_ids":tids,
            "output_FEG_sha256":"a"*64,"output_PRE_sha256":"b"*64}
    itf={"extent_cells_per_side":extent,
         "source_exterior_triangles":ext_tri,
         "mechanical_node_order_interface_first":extids,
         "actual_3plus_plate_junctions":incidence,
         "triple_plate_junction_exists":bool(incidence)}
    nod={"extent_cells":extent,"source_regional_PRE_sha256":"b"*64,
         "source_PRE_by_parent_node":{str(i):{"node_id":i} for i in ids},
         "exterior_triangles":triples}
    cuts=[{"source_parent_node_ids":[ids[i],ids[i+1]],
           "source_edge_id": ":".join(map(str,sorted((ids[i],ids[i+1])))),
           "side":"SYNTHETIC_ONLY","adjacent_plate_id":5}
          for i in range(4*extent)]
    force={"extent_cells":extent,"source_external_cut_edges":cuts}
    providers={
        "multiscale":{"topological_comparative_extents":[]},
        "interface":{"scales":[],
                     "source_multiscale_manifest_sha256":manifest_shas["multiscale"]},
        "nodal":{"scales":[],
                 "source_multiscale_manifest_sha256":manifest_shas["multiscale"],
                 "source_interface_manifest_sha256":manifest_shas["interface"]},
        "force":{"scales":[],
                 "parent_multiscale_manifest_sha256":manifest_shas["multiscale"],
                 "parent_interface_manifest_sha256":manifest_shas["interface"],
                 "parent_G2_binding_manifest_sha256":manifest_shas["nodal"]},
    }
    for scope in (8,16):
        # Both scales must exist in original provider reports, per contract.
        if scope==extent:
            r,it,nd,fc = region,itf,nod,force
        else:
            r={"cell_extent_per_side":scope}
            it={"extent_cells_per_side":scope}
            nd={"extent_cells":scope}
            fc={"extent_cells":scope}
        providers["multiscale"]["topological_comparative_extents"].append(r)
        providers["interface"]["scales"].append(it)
        providers["nodal"]["scales"].append(nd)
        providers["force"]["scales"].append(fc)
    monkeypatch.setattr(m,"read_pinned",lambda name,path:
                        (providers[name],manifest_shas[name]))
    monkeypatch.setattr(m,"sha",lambda path: "b"*64
                        if "PRE_T0_PASSIVE" in str(path) else "a"*64)
    fake_mesh=SimpleNamespace(
        nodes=[SimpleNamespace(latitude_deg=float(i%90),
                               longitude_deg=float(i%180))
               for i in range(len(ids))],
        elements=[None]*len(tids))
    monkeypatch.setattr(m,"parse_feg",lambda data,mode:fake_mesh)
    from pathlib import Path
    # Actual root read uses pathlib paths but no real FEG/PRE bytes after stub.
    scenario={
        "schema":m.INPUT_SCHEMA,
        "authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
        "physical_source_authority_ratified":False,
        "mechanical_solve_authorized":False,
        "scope_extent_cells":extent,
        "source_manifest_sha256":manifest_shas,
        "candidate_material_by_parent_node":{str(i):{"fixture":True} for i in extids},
        "velocity_en_by_parent_node":{str(i):[0.,0.] for i in extids},
        "line_tractions_by_edge":{c["source_edge_id"]:None for c in cuts},
        "basal_tractions_by_triangle":{str(t):None for t in ext_tri},
        "external_gpe":{"fixture":True},
    }
    return providers, scenario


@pytest.mark.parametrize("extent",(8,16))
def test_old_source_coupled_runner_uses_local_source_junction_incidences(monkeypatch,tmp_path,extent):
    providers, scenario=synthetic_provider_fixture(monkeypatch,extent)
    (tmp_path / f"OUTER_A_{extent:02d}x{extent:02d}.feg").write_text("SYNTHETIC_TEST_ONLY")
    (tmp_path / f"OUTER_A_{extent:02d}x{extent:02d}_PRE_T0_PASSIVE.dat").write_text("SYNTHETIC_TEST_ONLY")
    input_, _=m.source_inputs(tmp_path,tmp_path,tmp_path,tmp_path,extent,scenario)
    j=input_["scope"]
    assert j["source_parent_34587_present_in_footprint"] is True
    assert j["source_triple_parent_node_id"] == (None if extent==8 else 34587)
    assert j["source_actual_3plus_plate_junctions"] == (
        [] if extent==8 else [{"parent_node_id":34587,"incident_plates":[5,8,11]}])
    assert j["junction_source_is_not_a_fault_slip_law"] is True
    assert input_["scope"]["mechanical_solve_authorized"] is False


@pytest.mark.parametrize("extent",(8,16))
def test_old_source_coupled_runner_rejects_fake_junction_incidences(monkeypatch,tmp_path,extent):
    providers, scenario=synthetic_provider_fixture(monkeypatch,extent)
    it=next(r for r in providers["interface"]["scales"]
            if r["extent_cells_per_side"]==extent)
    if extent==8:
        it["actual_3plus_plate_junctions"]=[{
            "parent_node_id":34587,"incident_plates":[5,8,11]}]
        it["triple_plate_junction_exists"]=True
    else:
        it["actual_3plus_plate_junctions"]=[]
        it["triple_plate_junction_exists"]=False
    (tmp_path / f"OUTER_A_{extent:02d}x{extent:02d}.feg").write_text("SYNTHETIC_TEST_ONLY")
    (tmp_path / f"OUTER_A_{extent:02d}x{extent:02d}_PRE_T0_PASSIVE.dat").write_text("SYNTHETIC_TEST_ONLY")
    with pytest.raises(CoupledAssemblyError,match="SOURCE_JUNCTION_TOPOLOGY_INVALID"):
        m.source_inputs(tmp_path,tmp_path,tmp_path,tmp_path,extent,scenario)


def test_coupled_source_runner_rejects_source_authoring_template_before_provider_io(tmp_path):
    from experiments.plate58_deforming_explore_v1.g2_g3_source_to_coupled_handoff import (
        compile_pair,
    )
    from test_r6_g2_g3_source_to_coupled_handoff import packets
    _, p8, p16 = packets(tmp_path)
    candidate8, _, _ = compile_pair(p8, p16)
    with pytest.raises(CoupledAssemblyError,match="UNSELECTED_AUTHORING_TEMPLATE"):
        m.source_inputs(tmp_path / "not_real", tmp_path / "not_real",
                        tmp_path / "not_real", tmp_path / "not_real",
                        8, candidate8)


def test_core_source_runner_rejects_source_authoring_template_without_solve(tmp_path):
    from experiments.plate58_deforming_explore_v1.g2_g3_source_to_coupled_handoff import (
        compile_pair,
    )
    from experiments.plate58_deforming_explore_v1.g2_g3_core_exterior_source_runner import (
        validate_full_scenario,
    )
    from experiments.plate58_deforming_explore_v1.g2_g3_source_core_exterior_stitch import (
        StitchedCandidateError,
    )
    from test_r6_g2_g3_source_to_coupled_handoff import packets
    _, p8, p16 = packets(tmp_path)
    candidate8, _, _ = compile_pair(p8, p16)
    with pytest.raises(StitchedCandidateError,match="UNSELECTED_AUTHORING_TEMPLATE"):
        validate_full_scenario(candidate8,
                               candidate8["source_original_full_parent_node_order"],8)
