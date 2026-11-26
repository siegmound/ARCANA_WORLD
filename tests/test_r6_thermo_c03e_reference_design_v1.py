import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03e_reference_design as e


def receipt():
    return e.read(e.d.m.HERE/"c03d_r4_fair_receipt_v1.json")


def fixture():
    r=receipt()
    z={"pseudocompound_reports":[{"model":k,"count":v,"requested_model":True} for k,v in r["model_counts"].items()],
       "native_total_pseudocompounds_reports":[1454],
       "missing_endmember_reports":[{"model":k,"endmembers":[{"endmember":v} for v in values],
                                    "requested_model":True,"parsed_nonempty":True}
                                   for k,values in r["missing_by_model"].items()],
       "full_native_pruning_verified":False,"scientific_acceptance":False}
    return r,z


def test_all_counts_and_missing_reconcile():
    r,z=fixture()
    assert e.validate_details(z,r,list(r["model_counts"]))["counts"]==r["model_counts"]


def test_count_drift_is_rejected():
    r,z=fixture()
    z["pseudocompound_reports"][0]["count"]+=1
    with pytest.raises(ValueError,match="PSEUDOCOMPOUND_REPLAY"):
        e.validate_details(z,r,list(r["model_counts"]))


def test_missing_endmember_drift_is_rejected():
    r,z=fixture()
    z["missing_endmember_reports"][0]["endmembers"].clear()
    with pytest.raises(ValueError,match="MISSING_ENDMEMBER_REPLAY"):
        e.validate_details(z,r,list(r["model_counts"]))


def test_invalid_site_population_parser():
    raw=b"**warning ver059** endmember fparg_i  in solution model GlTrTsPg has invalid site populations.\n\n**warning ver059** endmember fts_i    in solution model GlTrTsPg has invalid site populations.\n"
    assert e.invalid_sites(raw)=={"GlTrTsPg":["fparg_i","fts_i"]}


def test_design_not_executable():
    z=e.reference_design({"reference_doi":"10.1029/2018JE005869"})
    assert z["reference_O2"]["exact_MORB_value"] is None
    assert z["benchmark_executable"] is False and z["authorized_equilibrium_solver_calls"]==0


def test_dialogue_rejects_nonzero_input():
    with pytest.raises((ValueError,KeyError),match="DIALOGUE_REPLAY|policy"):
        e.validate_dialogue({"events":[],"policy":e.d.dialogue.R4_POLICY,"state":"SENTINEL_SENT",
            "error":None,"scientific_warning_acceptance":False,"requested_equilibrium_points":0,
            "acknowledged_warning_codes":receipt()["acknowledged_warning_codes"]},b"300 1000\n",b"",receipt())
