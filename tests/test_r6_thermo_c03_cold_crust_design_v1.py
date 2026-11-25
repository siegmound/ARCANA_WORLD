import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03_cold_crust_design as c


def test_header_sightings_not_substrings():
    raw=b"Chl(W) 1\n# Chl(HP) 2\nFsp(HGP) 3\nChl(W) 4\n"
    result=c.candidate_tokens(raw)
    assert result["Chl(W)"]==2
    assert result["Chl(HP)"]==0
    assert result["Fsp(HGP)"]==1


def test_missing_source_points_fail_closed():
    with pytest.raises(ValueError,match="C03_SOURCE_POINT_MISSING"):
        c.sample_points({"samples":[]})


def test_source_points_preserve_unknown_pressure():
    rows=[{"extent":8,"layer":"crust","parent_node_id":n,"source_depth_m":d,
        "source_temperature_K":500.,"conditional_delta_P_kbar":2.,
        "absolute_pressure_pa":None,"material_recipe":None,"spatial_assignment":None}
        for n,d in c.POINTS]
    out=c.sample_points({"samples":rows})
    assert len(out)==2
    assert all(x["absolute_pressure_pa"] is None for x in out)
    rows[0]["absolute_pressure_pa"]=0
    with pytest.raises(ValueError,match="C03_SOURCE_AUTHORITY"):
        c.sample_points({"samples":rows})


def test_cold_cohort_counts_repeated_coordinates_separately():
    rows=[];regions={}
    for extent in (8,16):
        n=5*(extent+1)**2
        rows.extend({"extent":extent,"layer":"crust","source_temperature_K":500.,
            "conditional_delta_P_kbar":0.} for _ in range(n))
        regions[str(extent)]={"crust":{"below_felsic_design_T_min":n}}
    out=c.cold_cohort({"samples":rows,"regions":regions})
    assert out["8"]["unique_exact_cold_PT_coordinates"]==1
    assert out["8"]["zero_conditional_overburden"]==405
    assert out["16"]["most_common_cold_PT"][0]["count"]==1445
