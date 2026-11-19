"""Synthetic G3 source-continuation topology/owner tests; no mechanical solve."""
from types import SimpleNamespace
import numpy as np
import pytest
from experiments.plate58_deforming_explore_v1.continuation_A import (
    extent_cells,summarize_region,select_regional_pre)
from experiments.plate58_deforming_explore_v1.envelope import edge_incidence

def mock_mesh(side):
    r0,c0=101-side//2,22-side//2
    coords=np.asarray([(-90+r0+i,-180+c0+j)
        for i in range(side+1) for j in range(side+1)],dtype=float)
    ids=list(range(1,(side+1)**2+1))
    def node(i,j): return 1+i*(side+1)+j
    els,plates=[],[]
    for i in range(side):
        for j in range(side):
            u,v,w,x=node(i,j),node(i,j+1),node(i+1,j+1),node(i+1,j)
            for tri in ((u,v,w),(u,w,x)):
                els.append(SimpleNamespace(node_ids=tri))
                plates.append(8 if j<side//2 else 5)
    source={edge:f"R6BND-T0-SYNTH-{idx}"
        for idx,(edge,owners) in enumerate(edge_incidence(els,plates).items())
        if len(owners)==2 and owners[0][1]!=owners[1][1]}
    return ids,els,plates,SimpleNamespace(vertices_lat_lon=coords),source

def test_region_scales_preserve_core_and_halo():
    assert len(extent_cells(4))==16 and len(extent_cells(8))==64
    assert len(extent_cells(16))==256
    assert all(set(extent_cells(a)).issubset(extent_cells(b))
               for a,b in ((2,4),(4,8),(8,16)))
    assert set(((100,21),(101,22))).issubset(extent_cells(16))

@pytest.mark.parametrize("size,expected_nodes",[(8,81),(16,289)])
def test_real_source_style_cut_and_contact_identity(size,expected_nodes):
    r=summarize_region(size,*mock_mesh(size))
    assert len(r["parent_node_ids"])==expected_nodes
    assert r["source_contact_count"]==size
    assert r["source_plates_present"]==[5,8]
    assert all(len(v)==size for v in r["outer_cut_edges"].values())
    assert len(r["ambiguous_outer_cut_nodes"]["north"])==1
    assert len(r["ambiguous_outer_cut_nodes"]["south"])==1
    assert r["external_boundary_traction"] is None
    assert r["external_boundary_displacement"] is None
    assert r["G3_A_mantle_basal_normal_support"] is None
    assert r["physical_extent_and_convergence_qualified"] is False

def test_contact_source_not_invented():
    ids,els,plates,mesh,_=mock_mesh(8)
    with pytest.raises(ValueError,match="CONTACT_SOURCE_ID_NOT_AUTHENTIC"):
        summarize_region(8,ids,els,plates,mesh,{})

def test_regional_pre_only_original_records_and_ownership(tmp_path):
    source=tmp_path/"SRC_PRE.dat"
    out=tmp_path/"EXTRACT_PRE.dat"
    metadata={"header":{"magic":"MAGIC","schema":"SRC"},
       "node_count":64442,
       "field_order":["node_id"]+[f"field{i}" for i in range(50)]}
    with source.open("w") as f:
        f.write("MAGIC SRC 64442\n")
        for i in range(1,64443):
            f.write(str(i)+" "+" ".join(["1"]*50)+"\n")
    result=select_regional_pre(source,[3,1,2],metadata,out)
    rows=out.read_text().splitlines()
    assert result["row_count"]==3
    assert result["no_material_constitutive_properties_inferred"] is True
    assert len(rows)==4
    assert [int(row.split()[0]) for row in rows[1:]]==[1,2,3]
    assert all(len(row.split())==51 for row in rows[1:])
