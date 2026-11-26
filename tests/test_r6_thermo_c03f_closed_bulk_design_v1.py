import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03f_closed_bulk_design as r


def point(phases):
    return {"id":"B01","target":"pre","target_present":True,
            "phase_wt_percent":phases,"density_kg_m3":3000,"Cp_J_kg_K":1000,
            "H2O_wt_percent":4}


def test_comparison_preserves_model_identity():
    x=r.review_pair(point({"pre":20,"Act(M)":30}),point({"pre":22,"acti":25}))
    assert x["phase_delta_DP_minus_ACT_percentage_points"]=={"pre":2,"amphibole_family":-5}
    assert x["solver_confounding"] and not x["DP_solution_observed"]


def test_complex_amphibole_requires_review():
    with pytest.raises(ValueError,match="AMPHIBOLE"):
        r.review_pair(point({"pre":20,"Act(M)":30}),point({"pre":22,"acti":25,"cAmph(DP)":1}))
