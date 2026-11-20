"""Source-full G2/G3 runner fail-closed contracts (synthetic provider fixtures)."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

import experiments.plate58_deforming_explore_v1.g2_g3_core_exterior_source_runner as mod
from experiments.plate58_deforming_explore_v1.g2_g3_source_core_exterior_stitch import (
    StitchedCandidateError,
)


def full_scenario(n=81):
    ids=list(range(1,n+1))
    return {
        "schema":mod.INPUT_FULL,
        "scope_extent_cells":8 if n==81 else 16,
        "authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
        "physical_source_authority_ratified":False,
        "mechanical_solve_authorized":False,
        "core_external_force_provider_qualified":False,
        "fault_interface_physics_authorized":False,
        "candidate_material_by_parent_node":{str(i):{"test":True} for i in ids},
        "velocity_en_by_parent_node":{str(i):[0.,0.] for i in ids},
        "line_tractions_by_edge":{"1:2":{"test":True}},
        "basal_tractions_by_triangle":{"100":{"test":True}},
        "external_gpe":{"test":True},
    }


def test_full_parent_scenario_demands_explicit_81_or_289_source_node_fields():
    mod.validate_full_scenario(full_scenario(),range(1,82),8)
    mod.validate_full_scenario(full_scenario(289),range(1,290),16)


@pytest.mark.parametrize("change",[
    "missing_core_only","missing_velocity","promote_solve",
    "claim_core_load","claim_fault_law","omit_gpe","missing_traction",
])
def test_source_full_explicit_scenario_fails_closed(change):
    s=full_scenario()
    if change=="missing_core_only":
        del s["candidate_material_by_parent_node"]["9"]
    elif change=="missing_velocity":
        del s["velocity_en_by_parent_node"]["9"]
    elif change=="promote_solve":
        s["mechanical_solve_authorized"]=True
    elif change=="claim_core_load":
        s["core_external_force_provider_qualified"]=True
    elif change=="claim_fault_law":
        s["fault_interface_physics_authorized"]=True
    elif change=="omit_gpe":
        s["external_gpe"]=None
    else:
        s["line_tractions_by_edge"]={}
    with pytest.raises(StitchedCandidateError):
        mod.validate_full_scenario(s,range(1,82),8)


def test_core_source_feg_exact_eight_original_triangles_extracted(monkeypatch,tmp_path):
    mdir=tmp_path/"multiscale"
    mdir.mkdir()
    f=mdir/"OUTER_A_08x08.feg"
    p=mdir/"OUTER_A_08x08_PRE_T0_PASSIVE.dat"
    f.write_text("source-feg-synthetic-only\n")
    p.write_text("source-pre-synthetic-only\n")
    ids=list(range(1,82))
    tids=list(range(100,228))
    core_tids=tids[:8]
    ext_tids=tids[8:]
    core_faces={100+i:(9,i+1,((i+1)%8)+1) for i in range(8)}
    source={
        "topological_comparative_extents":[{
            "cell_extent_per_side":8,
            "parent_node_ids":ids,
            "parent_triangle_ids":tids,
            "output_FEG_sha256":mod.sha(f),
            "output_PRE_sha256":mod.sha(p),
        }]
    }
    interface={
        "scales":[{
            "extent_cells_per_side":8,
            "source_exterior_triangles":ext_tids,
            "source_interface_node_ids":list(range(1,9)),
            "source_core_only_node_ids":[9],
        }]
    }
    nodal={
        "scales":[{
            "extent_cells":8,
            "source_regional_PRE_sha256":mod.sha(p),
            "source_PRE_by_parent_node":{
                str(i):{
                    "node_id":float(i),
                    "material_configuration_code":1.,
                } for i in ids
            },
        }]
    }
    source_by_kind={
        "multiscale":source,"interface":interface,"nodal":nodal,
    }
    def fake_read(kind,dir_):
        return source_by_kind[kind],"source_manifest_fake_for_unit_test"
    monkeypatch.setattr(mod,"read_pinned",fake_read)
    triangles=[
        SimpleNamespace(node_ids=core_faces[tid] if tid in core_faces
                        else (1,10,11)) for tid in tids
    ]
    feg=SimpleNamespace(
        nodes=[SimpleNamespace(latitude_deg=float(i)/100.,
                               longitude_deg=float(i)/200.) for i in ids],
        elements=triangles,
    )
    monkeypatch.setattr(mod,"parse_feg",lambda content,mode:feg)
    r=mod.source_core_geometry(
        mdir,tmp_path/"interface",tmp_path/"nodal",8)
    assert r["source_original_core_triangle_ids"]==core_tids
    assert len(r["source_core_triangle_bindings"])==8
    assert r["source_core_only_node_id"]==9
    assert r["source_core_interface_nodes"]==list(range(1,9))
    assert set(n for triangle in r["source_core_triangles"].values()
               for n in triangle)==set(range(1,10))
    assert r["source_FEG_sha256"]==mod.sha(f)
    assert r["source_PRE_sha256"]==mod.sha(p)


def test_refuse_output_overwrite_before_reading_sources(tmp_path):
    target=tmp_path/"already_exists"
    target.mkdir()
    with pytest.raises(StitchedCandidateError,
                       match="CORE_SOURCE_OUTPUT_ALREADY_EXISTS"):
        mod.execute(multiscale=tmp_path,interface=tmp_path,
                    nodal=tmp_path,force=tmp_path,
                    scenario_path=tmp_path/"candidate_not_available.json",
                    extent=8,output=target)
