import pytest
from experiments.r6_thermo_provider_pilot_v1 import c03d_r4_model_audit as a
from experiments.r6_thermo_provider_pilot_v1 import c03d_native_dialogue as d

W966=(b"**warning ver966** EoS code 1 for O2 in data file hp02ver.dat requires "
      b"volumetric data. The code will automatically be set to 0")
W968=(b"**warning ver968** O2 is a name reserved for fluid species in hp02ver.dat "
      b"G(Pr,T) activity or fugacity of O2")


def advance(allow):
    state=d.Dialogue(allow_si013=True,allow_gl017=allow)
    raw=d.PROJECT
    assert state.next_response(raw)==b"c03d\n"
    for warning in (W966,W968,d.SI013):
        raw+=warning+d.WARNING
        assert state.next_response(raw)==b"y\n"
    return state,raw


def test_exact_legacy_warning_and_sentinel():
    state,raw=advance(True)
    raw+=d.GL017+d.WARNING
    assert state.next_response(raw)==b"y\n"
    assert state.acknowledged==["966","968","013","017"]
    raw+=d.BULK
    assert state.next_response(raw)==b"n\n"
    raw+=d.PT
    assert state.next_response(raw)==b"0 0\n"


def test_legacy_warning_without_audit_rejected():
    state,raw=advance(False)
    with pytest.raises(ValueError,match="UNAPPROVED_INTERACTIVE_WARNING"):
        state.next_response(raw+d.GL017+d.WARNING)


def test_other_model_or_modified_warning_rejected():
    for msg in (d.GL017.replace(b"GlTrTsPg",b"Act(M)"),d.GL017.replace(b"erratic",b"stable")):
        state,raw=advance(True)
        with pytest.raises(ValueError,match="UNAPPROVED_INTERACTIVE_WARNING"):
            state.next_response(raw+msg+d.WARNING)


def test_repeated_legacy_warning_rejected():
    state,raw=advance(True)
    raw+=d.GL017+d.WARNING
    assert state.next_response(raw)==b"y\n"
    with pytest.raises(ValueError,match="UNAPPROVED_INTERACTIVE_WARNING"):
        state.next_response(raw+d.GL017+d.WARNING)


def fixture():
    blocks={str(i):{"text":"| site_check_override","normalized_text_sha256":"x"} for i in range(17)}
    blocks["GlTrTsPg"]={"text":"site_check_override\nend_of_model","normalized_text_sha256":"y"}
    return blocks


def test_model_audit_only_active_flag():
    assert a.model_audit(fixture())["allowed_diagnostic_warning_models"]==["GlTrTsPg"]


def test_model_audit_extra_flag_rejected():
    blocks=fixture()
    blocks["0"]["text"]="site_check_override"
    with pytest.raises(ValueError,match="SITE_CHECK_OVERRIDE_DRIFT"):
        a.model_audit(blocks)


def test_native_multiline_endmember_report_and_pseudocompounds():
    raw=b"**warning ver114** the following endmembers are missing for O(HP):\n\n teph fran\n extra\n\n 4 pseudocompounds generated for: O(HP) \nTotal number of pseudocompounds: 4\n"
    z=a.native_model_details(raw,["O(HP)"],{"teph":{"outside_active_components":["MNO"]}})
    x=z["missing_endmember_reports"][0]
    assert [v["endmember"] for v in x["endmembers"]]==["teph","fran","extra"]
    assert x["endmembers"][0]["outside_active_components"]==["MNO"]
    assert z["pseudocompound_reports"][0]["count"]==4
    assert z["native_total_pseudocompounds_reports"]==[4]
    assert z["scientific_acceptance"] is False


def test_unknown_model_is_reported_not_promoted():
    z=a.native_model_details("**warning ver114** the following endmembers are missing for X:\n\n a\n\n",[])
    assert z["missing_endmember_reports"][0]["requested_model"] is False
    assert z["full_native_pruning_verified"] is False
