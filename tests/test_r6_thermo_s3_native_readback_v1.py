"""S3 candidate native parser: synthetic, deliberately non-physical values."""
import copy
import pytest
from experiments.r6_thermo_provider_pilot_v1.s3_native_readback import (
    S3NativeError, read_magemin_case, read_perplex_prn, classify_phase_sets,
)


@pytest.fixture
def policy():
    return {"candidate_tracks": [
        {"id": "S3A_MAGEMIN_CUSTOM_IG", "P": [8, 9, 10, 11, 12],
         "T": [1000, 1050, 1100, 1150, 1200],
         "fixed_original_oxide_input": {
             "names": ["SiO2", "FeO", "Fe2O3", "H2O"],
             "amounts_wt_percent": [60, 30, 2, 8]}},
        {"id": "S3B_PERPLEX_BL691", "P": [2000, 3000, 4000, 5000, 6000],
         "T": [950, 1000, 1050, 1100, 1150],
         "fixed_original_molar_input": {
             "names": ["SiO2", "MgO"]}},
    ]}


@pytest.fixture
def mag(policy):
    from experiments.r6_thermo_provider_pilot_v1.s3_native_readback import expected_magemin_native_basis
    basis = expected_magemin_native_basis(policy["candidate_tracks"][0])
    names = list(basis)
    weights = [basis[k] for k in names]
    phases = [f"synthetic_{i}" for i in range(len(names))]
    comp = [[1.0 if i == j else 0.0 for j in range(len(names))]
            for i in range(len(names))]
    return {"status": 0, "database": "ig", "dataset": "tc_ds636",
            "P_kbar": 10.0, "T_C": 1100.0,
            "G_system": -100., "rho_kg_m3": 2600., "iterations": 4,
            "phases": phases, "phase_mass_fractions": weights,
            "oxides": names, "bulk_wt": weights, "phase_comp_wt": comp,
            "bulk_res_norm": 0., "native_component_weight_closure_abs": 0.,
            "source_native_basis_closure_custom": 0.}


def prn_single(mol="1.000", name="SyntheticPhase", wt="100.00"):
    return f"""Stable phases at:
                          T(K)     =  1050.00
                          P(bar)   =  4000.00

Phase Compositions (molar  proportions):
                  wt %      vol %     mol %     mol        SiO2     MgO
 {name}        {wt}      100.00     100.00    {mol}       1.00000  0.00000

Phase speciation (molar proportions):

Bulk Composition:
 SiO2  1.000  0  0  0  0  0  0  0
 MgO   0.000  0  0  0  0  0  0  0
Other Bulk Properties:
"""


def test_magemin_allows_unnamed_dynamic_phases(mag, policy):
    x = read_magemin_case(mag, 10, 1100, policy)
    assert len(x["phases"]) == 4
    assert x["max_native_component_delta"] == 0
    assert "UNQUALIFIED" in x["status"]


@pytest.mark.parametrize(("field", "bad"), [
    ("status", 1), ("database", "mb"), ("dataset", "other"),
    ("P_kbar", 11.0), ("T_C", float("nan")),
    ("G_system", float("inf")), ("rho_kg_m3", 0),
    ("phase_mass_fractions", [1.0]), ("phases", ["dup", "dup"]),
    ("bulk_res_norm", 1e-2), ("iterations", -1),
    ("native_component_weight_closure_abs", .1),
])
def test_magemin_rejects_invalid_native_fields(mag, policy, field, bad):
    sample = copy.deepcopy(mag)
    sample[field] = bad
    with pytest.raises(S3NativeError):
        read_magemin_case(sample, 10, 1100, policy)


def test_magemin_chemistry_mismatch_rejected(mag, policy):
    sample = copy.deepcopy(mag)
    sample["bulk_wt"][0] += .01
    with pytest.raises(S3NativeError):
        read_magemin_case(sample, 10, 1100, policy)


def test_perplex_arbitrary_phase_name_supported(policy):
    r = read_perplex_prn(prn_single(name="NovelPhase(G)"), 4000, 1050, policy)
    assert r["phases"] == {"NovelPhase(G)": 100.0}
    assert r["printed_component_coverage"] == 2


@pytest.mark.parametrize("change", [
    lambda s: s.replace("T(K)     =  1050.00", "T(K)     =  1060.00"),
    lambda s: s.replace("100.00      100.00", "70.00      100.00"),
    lambda s: s.replace("1.00000  0.00000", "0.70000  0.00000"),
    lambda s: s.replace("1.000  0  0", "1.500  0  0"),
    lambda s: s.replace("Phase speciation", "Phase abundance"),
    lambda s: s.replace("SyntheticPhase", "NaNPhase").replace("1.00000", "NaN"),
    lambda s: s.replace("SyntheticPhase", "SyntheticPhase\n SyntheticPhase  100.00  100.00  100.00  1.000  1.00000  0.00000"),
])
def test_perplex_rejects_malformed(change, policy):
    with pytest.raises(S3NativeError):
        read_perplex_prn(change(prn_single()), 4000, 1050, policy)


def test_perplex_rejects_out_of_candidate_grid(policy):
    with pytest.raises(S3NativeError):
        read_perplex_prn(prn_single(), 4001, 1050, policy)


def test_cross_pt_phase_set_change_not_failure():
    a = {"provider": "MAGEMin_C.jl", "P": 10, "T": 1100,
         "phases": {"liq": .2, "opx": .8}}
    b = {"provider": "MAGEMin_C.jl", "P": 11, "T": 1100,
         "phases": {"liq": .6, "cpx": .4}}
    result = classify_phase_sets(a, b)
    assert result["status"] == "CROSS_PT_PHASE_SET_CHANGE_OBSERVED_NOT_A_FAIL"
    assert result["added"] == ["cpx"] and result["removed"] == ["opx"]
    b["P"] = 10
    assert classify_phase_sets(a, b)["status"] == "SAME_PT_PHASE_DISAGREEMENT_REQUIRES_REVIEW"
    b["provider"] = "Perple_X"
    with pytest.raises(S3NativeError):
        classify_phase_sets(a, b)
