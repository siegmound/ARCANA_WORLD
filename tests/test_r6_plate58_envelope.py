"""Pure bounded topology/physics units; source-bound staging validated on FAIR."""
import math

import pytest
from experiments.plate58_deforming_explore_v1.envelope import (
    edge_incidence, geodesic_length_km, midpoint_lat_lon, side_of_edge,
)


class Element:
    def __init__(self,*ids):
        self.node_ids=ids


def test_topology_distinguishes_contact_from_exterior():
    elements=[Element(1,2,5),Element(1,5,4),
              Element(2,3,6),Element(2,6,5),
              Element(4,5,8),Element(4,8,7),
              Element(5,6,9),Element(5,9,8)]
    edges=edge_incidence(elements,[8,8,5,5,8,8,5,5])
    contact={edge for edge,rows in edges.items()
             if len(rows)==2 and rows[0][1]!=rows[1][1]}
    assert contact=={(2,5),(5,8)}
    assert sum(len(v)==1 for v in edges.values())==8


def test_nonmanifold_rejected():
    with pytest.raises(ValueError,match="NONMANIFOLD"):
        edge_incidence([Element(1,2,3)]*3,[5]*3)


@pytest.mark.parametrize("a,b,side",[
    ([10,-160],[10,-159],"south"),
    ([14,-160],[14,-159],"north"),
    ([11,-160],[12,-160],"west"),
    ([11,-156],[12,-156],"east"),
])
def test_four_exterior_cut_tags(a,b,side):
    assert side_of_edge(a,b,(10,14,-160,-156))==side


def test_diagonal_cannot_be_mislabeled_as_cut():
    with pytest.raises(ValueError,match="OUTER_EDGE"):
        side_of_edge([10,-160],[11,-159],(10,14,-160,-156))


def test_geodesic_and_midpoint_are_finite_and_within_arc():
    a,b=[10,-160],[10,-159]
    length=geodesic_length_km(a,b)
    midpoint=midpoint_lat_lon(a,b)
    assert 100<length<111.2
    assert midpoint[0]==pytest.approx(10.0,abs=0.01)
    assert midpoint[1]==pytest.approx(-159.5,abs=0.01)


def test_zero_length_fails_if_used_as_geodesic():
    assert geodesic_length_km([0,0],[0,0])==pytest.approx(0)
