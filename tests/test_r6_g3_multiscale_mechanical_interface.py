"""G3 cross-scale mechanical interface/three-plate contact invariants."""
from collections import defaultdict
from types import SimpleNamespace

import pytest

from experiments.plate58_deforming_explore_v1.g3_multiscale_interface import (
    derive_external_interface,
)
from experiments.plate58_deforming_explore_v1.continuation_A import (
    summarize_region,
)


def toy_region(width, with_third=False):
    n=width+1
    r0,c0=101-width//2,22-width//2
    coords=[(-90+r0+i,-180+c0+j) for i in range(n) for j in range(n)]
    def node(i,j):return 1+i*n+j
    tris=[]
    plates=[]
    for i in range(width):
        for j in range(width):
            for tri in ((node(i,j),node(i,j+1),node(i+1,j+1)),
                        (node(i,j),node(i+1,j+1),node(i+1,j))):
                tris.append(SimpleNamespace(node_ids=tri))
                plate=8 if j<width//2 else 5
                if with_third and i>=width//2+1 and j>=width//2+1:
                    plate=11
                plates.append(plate)
    from experiments.plate58_deforming_explore_v1.envelope import edge_incidence
    incidence=edge_incidence(tris,plates)
    source={edge:f"R6BND-T0-SYNTH-{i}"
            for i,(edge, owners) in enumerate(incidence.items())
            if len(owners)==2 and owners[0][1]!=owners[1][1]}
    class FakeCoordinates:
        def __getitem__(self,index):
            if isinstance(index,int): return coords[index]
            return [coords[k] for k in index]
    class FakeArray:
        def __getitem__(self,index):
            return coords[index]
    mesh=SimpleNamespace(vertices_lat_lon=FakeArray())
    reg=summarize_region(width,list(range(1,n*n+1)),tris,plates,mesh,source)
    reg["parent_triangle_ids"]=list(range(1,len(tris)+1))
    reg["parent_triangle_plate_ids"]=plates
    return reg,SimpleNamespace(nodes=[SimpleNamespace(node_id=i+1)
                    for i in range(n*n)],elements=tris,faults=[])


def core_ids(width):
    # Domain centered on the source core 2x2 parent-cell patch.
    n=width+1
    center=width//2
    nodes=[1+i*n+j for i in range(center-1,center+2)
                         for j in range(center-1,center+2)]
    # The core center has a unique source node ID; never shadow grid width.
    center_id=1+center*n+center
    interface=sorted(parent_id for parent_id in nodes if parent_id!=center_id)
    center_node=[center_id]
    # Two triangles per source cell, indexed by (i*ncell+j)*2.
    tids=[]
    for i in (center-1,center):
        for j in (center-1,center):
            k=2*(i*width+j)+1
            tids.extend([k,k+1])
    ecount=defaultdict(int)
    reg,feg=toy_region(width)
    for tid in tids:
        tri=feg.elements[tid-1].node_ids
        a,b,c=tri
        for edge in ((a,b),(b,c),(c,a)):
            ecount[tuple(sorted(edge))]+=1
    return tids,sorted(edge for edge,c in ecount.items() if c==1),interface,center_node


@pytest.mark.parametrize("width,third,dofs,outer",[
    (8,False,160,72),(16,True,576,280),
])
def test_derive_multiscale_3plate_aware_source_interface(width,third,dofs,outer):
    reg,feg=toy_region(width,third)
    tids,edges,interface,center=core_ids(width)
    result=derive_external_interface(reg,feg,tids,edges,interface,center)
    assert result["velocity_dof_count"]==dofs
    assert result["source_interface_node_ids"]==interface
    assert len(result["source_exterior_only_node_ids"])==outer
    assert len(result["source_exterior_triangles"])==2*width*width-8
    assert result["interface_dof_indices"]==list(range(16))
    assert result["physical_mechanical_tangent"] is None
    assert result["mechanical_solve_authorized"] is False
    assert ([5,8] in [row["plate_pair"] for row in
                      result["contact_graph_by_plate_pair"]])
    if third:
        assert result["plate_ids_present"]==[5,8,11]
        assert any(11 in row["plate_pair"] for row in
                   result["contact_graph_by_plate_pair"])
    else:
        assert result["plate_ids_present"]==[5,8]


def test_missing_source_contact_fails_not_invents():
    reg,feg=toy_region(8)
    ids,edges,interface,center=core_ids(8)
    reg["source_contact_edges"]=[]
    with pytest.raises(ValueError,match="CONTACT_PAIR_GRAPH_CHANGED"):
        derive_external_interface(reg,feg,ids,edges,interface,center)


def test_shared_source_interface_no_duplicate_dofs():
    reg,feg=toy_region(8)
    ids,edges,interface,center=core_ids(8)
    result=derive_external_interface(reg,feg,ids,edges,interface,center)
    order=result["mechanical_node_order_interface_first"]
    assert len(set(order))==len(order)==80
    assert set(interface).issubset(order)
    assert center[0] not in order


def test_fabricated_outer_traction_rejected():
    reg,feg=toy_region(8)
    ids,edges,interface,center=core_ids(8)
    reg["outer_cut_edges"]["north"][0]["physical_traction"]=[1.,2.]
    with pytest.raises(ValueError,match="UNAUTHORIZED_OR_MISMATCHED_EXTERNAL_CUT"):
        derive_external_interface(reg,feg,ids,edges,interface,center)


@pytest.mark.parametrize("width,third",[(8,False),(16,True)])
def test_fixture_parent_inventory_and_exact_core_perimeter(width,third):
    """Prevent range exclusive-end and shadowed-center errors in test fixtures."""
    reg,feg=toy_region(width,third)
    tids,edges,interface,center=core_ids(width)
    assert len(reg["parent_node_ids"])==(width+1)**2
    assert reg["parent_node_ids"]==list(range(1,(width+1)**2+1))
    assert len(feg.nodes)==(width+1)**2
    assert len(tids)==8
    assert len(edges)==8
    assert len(interface)==8
    assert len(center)==1
    assert center[0] not in interface
    assert len(set(interface+center))==9
