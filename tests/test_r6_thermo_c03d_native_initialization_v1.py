import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03d_native_initialization as c


def test_sentinel_never_requests_nonzero_pt():
    assert c.STDIN.splitlines()==[b"c03d",b"n",b"0 0"]


def test_option_replacement_only_named_default():
    assert c.set_option(b"hybrid_EoS_H2O default | x\n","hybrid_EoS_H2O","2")==b"hybrid_EoS_H2O 2 | x\n"
    with pytest.raises(ValueError,match="C03D_OPTION_DRIFT"):
        c.set_option(b"hybrid_EoS_H2O 4 | x\n","hybrid_EoS_H2O","2")


def test_section_replacement():
    assert c.replace_section("begin x\na\nend x\n","begin x","end x",["b"])=="begin x\nb\nend x\n"


def test_roster_sections_and_unaccounted():
    raw=b"Summary of included solution models:\n\n A B\n\nSummary of rejected solution models (see warnings above for reasons):\n\n C\n\nInteractively enter bulk compositions (y/n)?\nEnter (T = 0 to quit) T(K) P(bar)\n"
    z=c.observe(raw,b"",["A","B","C","D"])
    assert z["native_model_dispositions"]["included"]==["A","B"]
    assert z["native_model_dispositions"]["rejected"]==["C"]
    assert z["unaccounted_requested_models"]==["D"]
    assert z["requested_equilibrium_points"]==0
    assert not z["native_endmember_pruning_verified"]


def test_observe_reject_equilibrium_output():
    with pytest.raises(ValueError,match="C03D_UNEXPECTED_EQUILIBRIUM_OUTPUT"):
        c.observe(b"Interactively enter bulk compositions (y/n)?\nEnter (T = 0 to quit)\n",b"Phase Compositions (molar proportions):",[])


def test_observe_requires_native_prompt():
    with pytest.raises(ValueError,match="C03D_NATIVE_PT_PROMPT_MISSING"):
        c.observe(b"",b"",[])


def test_duplicate_summary_rejected():
    with pytest.raises(ValueError,match="C03D_DUPLICATE_NATIVE_SUMMARY"):
        c.summary_section("Summary of included solution models:\n A\n\nSummary of included solution models:\n B\n",c.HEADINGS["included"],["A","B"])


def test_component_rows_use_exact_native_name_width():
    for name in c.ORDER:
        row=c.component_row(name,12.035486633767736)
        assert row[:5]==name.ljust(5)
        assert row[5:].split()==["1","12.035486633767736","0.0","0.0"]


def test_fixed_width_roundtrip_all_components():
    vals={k:float(i+1) for i,k in enumerate(c.ORDER)}
    rows=[c.component_row(k,vals[k]) for k in c.ORDER]
    raw=("begin thermodynamic component list\n"+"\n".join(rows)+"\nend thermodynamic component list\n").encode()
    assert c.fixed_width_readback(raw,vals)==vals


def test_fixed_width_rejects_actual_failed_mgo_record():
    vals={k:float(i+1) for i,k in enumerate(c.ORDER)}
    rows=[c.component_row(k,vals[k]) for k in c.ORDER]
    rows[1]="MGO 1 12.035486633767736 0.0 0.0"
    raw=("begin thermodynamic component list\n"+"\n".join(rows)+"\nend thermodynamic component list\n").encode()
    with pytest.raises(ValueError,match="C03D_FIXED_WIDTH_COMPONENT"):
        c.fixed_width_readback(raw,vals)


def test_native_ver027_is_fatal_even_with_prompt():
    raw=b"**error ver027** Error reading the problem definition file:\nInteractively enter bulk compositions (y/n)?\nEnter (T = 0 to quit)\n"
    with pytest.raises(ValueError,match="C03D_NATIVE_FATAL:.*ver027"):
        c.observe(raw,b"",[])
