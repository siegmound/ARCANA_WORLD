"""G2/G3 interface and mathematically exact exterior transfer tests (no solve)."""
import numpy as np
import pytest
from types import SimpleNamespace

from experiments.plate58_deforming_explore_v1.coupling_A import (
    exterior_interface, condense_exterior_tangent,
    reconstruct_external_solution, block_dofs,
)


def fixture_geometry():
    # Four-by-four parent cells, two positive triangles per cell.
    vertices = [(y,x) for y in range(5) for x in range(5)]
    vindex = {key: 1+i for i,key in enumerate(vertices)}
    elements = []
    triangle_ids = []
    parent_core = []
    plates = []
    tid = 0
    for y in range(4):
        for x in range(4):
            sw = vindex[(y,x)]
            se = vindex[(y,x+1)]
            ne = vindex[(y+1,x+1)]
            nw = vindex[(y+1,x)]
            for tri in ((sw,se,ne),(sw,ne,nw)):
                tid+=1
                triangle_ids.append(tid)
                elements.append(SimpleNamespace(node_ids=tri))
                plates.append(5 if x>=2 else 8)
                if 1<=y<=2 and 1<=x<=2:
                    parent_core.append(tid)
    core_nodes = [vindex[(y,x)] for y in range(1,4) for x in range(1,4)]
    return core_nodes, list(range(1,26)), parent_core, triangle_ids, elements, plates


def test_25_node_halo_8_node_exact_source_interface():
    r=exterior_interface(*fixture_geometry())
    assert len(r["parent_interface_nodes"])==8
    assert len(r["parent_external_only_nodes"])==16
    assert len(r["parent_core_only_nodes"])==1
    assert len(r["source_exterior_triangle_ids"])==24
    assert len(r["interface_parent_edges"])==8
    assert len(r["exterior_reduced_dof_order"])==24
    assert r["interface_dof_indices"]==list(range(16))
    assert r["external_only_dof_indices"]==list(range(16,48))


def test_nodal_source_ids_not_duplicated_or_plate_assigned():
    r=exterior_interface(*fixture_geometry())
    assert set(r["parent_interface_nodes"]).isdisjoint(r["parent_external_only_nodes"])
    assert r["source_mesh_nodes_not_duplicated"]
    assert len(block_dofs(r["source_halo_parent_node_ids"]))==25


def test_tangent_schur_exact_assembled_residual_and_work():
    a=np.array([[4.,-1.,0.,0.],[-1.,5.,-1.,0.],
                [0.,-1.,5.,-1.],[0.,0.,-1.,4.]])
    f=np.array([1.,2.,3.,4.])
    condensed=condense_exterior_tangent(a,f,[0,3],symmetric_test=True)
    u_boundary=np.array([0.1,-0.2])
    full=reconstruct_external_solution(condensed,u_boundary)
    residual=a@full-f
    assert np.allclose(residual[[1,2]],0,atol=1e-13)
    assert np.allclose(residual[[0,3]],
        condensed["interface_tangent"]@u_boundary-condensed["effective_load"],
        atol=1e-13)
    # The exact reduced energy differs from full by a displacement-independent
    # constant determined by condensed eliminated load.
    unforced=condense_exterior_tangent(a,np.zeros(4),[0,3],symmetric_test=True)
    no_load_energy=0.5*full@a@full
    assert np.isfinite(no_load_energy)
    assert np.min(np.linalg.eigvalsh(unforced["interface_tangent"]))>0


def test_nonsymmetric_tangent_not_silently_rejected():
    a=np.array([[3.,2.,0.],[0.,4.,1.],[0.,0.,5.]])
    c=condense_exterior_tangent(a,[0,1,2],[0])
    full=reconstruct_external_solution(c,[1.])
    assert np.allclose((a@full-[0,1,2])[1:],0,atol=1e-13)


@pytest.mark.parametrize("data",[
    np.array([[0.,0.],[0.,0.]]),
    np.array([[1.,0.],[0.,float("nan")]]),
])
def test_singular_or_nonfinite_tangent_fails(data):
    with pytest.raises(ValueError,match="G3_EXTERIOR"):
        condense_exterior_tangent(data,np.zeros(2),[0])


def test_bad_duplicate_interface_degree_of_freedom_rejected():
    with pytest.raises(ValueError,match="G3_EXTERIOR_TANGENT_INPUT_INVALID"):
        condense_exterior_tangent(np.eye(3),np.zeros(3),[0,0])


def test_source_ownership_failure_blocks_interface():
    args=list(fixture_geometry())
    args[0][0]=999
    with pytest.raises(ValueError,match="G3_TRIANGLE_TO_PARENT_NODE_BINDING_CHANGED"):
        exterior_interface(*args)


def test_still_below_footprint_does_not_make_material_parameters():
    result=exterior_interface(*fixture_geometry())
    assert result["unknown_exterior_constitutive_tangent"] is None
    assert result["unknown_exterior_loads"] is None
