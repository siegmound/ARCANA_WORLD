"""Fast pure-function checks; physical input staging runs separately on FAIR."""
import math

import pytest

from experiments.plate58_deforming_explore_v1.prepare import (
    SECONDS_YEAR, interface_edges, readiness_gate, strain_rate_scales,
)


class Element:
    def __init__(self, *nodes):
        self.node_ids = nodes


def patch():
    # 3x3 nodes; left plate 8 and right plate 5, two rows.
    elements = [
        Element(1, 2, 5), Element(1, 5, 4),
        Element(2, 3, 6), Element(2, 6, 5),
        Element(4, 5, 8), Element(4, 8, 7),
        Element(5, 6, 9), Element(5, 9, 8),
    ]
    return elements, [8, 8, 5, 5, 8, 8, 5, 5]


def test_contact_edges_are_two_shared_segments():
    elements, plates = patch()
    assert interface_edges(elements, plates) == [(2, 5), (5, 8)]
    assert len({n for pair in interface_edges(elements, plates) for n in pair}) == 3


def test_invalid_nonmanifold_triangle_incidence_rejected():
    elements, plates = patch()
    with pytest.raises(ValueError, match="NONMANIFOLD"):
        interface_edges([elements[0]] * 3, [8] * 3)


def test_kinematic_rate_sensitivity_is_not_declared_as_resolved_strain():
    values = strain_rate_scales(0.1575)
    assert [v["width_km"] for v in values] == [10.0, 100.0, 300.0]
    assert values[0]["nominal_extension_rate_s_inv"] == pytest.approx(
        0.1575 / (10_000 * SECONDS_YEAR))
    assert values[0]["nominal_extension_rate_s_inv"] > values[1]["nominal_extension_rate_s_inv"]
    assert values[1]["nominal_extension_rate_s_inv"] > values[2]["nominal_extension_rate_s_inv"]


@pytest.mark.parametrize("speed,widths", [
    (0.0,(100.0,)), (-0.2,(100.0,)), (math.nan,(100.0,)),
    (0.1,(-100.0,)), (0.1,(math.inf,)),
])
def test_invalid_rate_inputs_fail_closed(speed,widths):
    with pytest.raises(ValueError):
        strain_rate_scales(speed,widths)


def test_readiness_is_fail_closed_even_with_material_proxy_approval():
    row = {"decisions": {
        "G2_material": {
            "fit_a_b_c_d_by_layer": None, "effective_pressure_and_biot": None,
            "brittle_friction": None, "water_model": None,
            "creep_fit_validation": None},
        "G3_accommodation": {
            "physical_width_and_resolution": None, "time_validity": None},
        "G3_support": {
            "north_cut": None, "south_cut": None, "basal_normal_support": None}}}
    gate = readiness_gate(row)
    assert gate["mechanical_solve_authorized"] is False
    assert "G3_support.north_cut" in gate["missing"]
    assert "G3_support.basal_normal_support" in gate["missing"]
    assert "G2.fit_a_b_c_d_by_layer" in gate["missing"]
