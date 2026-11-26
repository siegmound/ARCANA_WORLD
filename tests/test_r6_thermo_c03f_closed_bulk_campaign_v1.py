import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03f_closed_bulk_campaign as f


def point():
    return {"id":"test","T_K":506.7223873,"P_bar_candidate":1924.72,
            "source_point":{"parent_node_id":35304,"absolute_pressure_pa":None,
                            "pressure_semantics":"HYPOTHETICAL_COMPARATIVE_ONLY"}}


def native():
    return b"Stable phases at:\nT(K) = 506.722\nP(bar) = 1924.72\nPhase Compositions (molar  proportions):\n"


def test_two_field_capture():
    assert f.capture(native(),point())["native_potential_readback"]=={"T(K)":"506.722","P(bar)":"1924.72"}


@pytest.mark.parametrize("raw",[native().replace(b"1924.72",b"2000"),
    native()+b"**warning ver046**",native().replace(b"Stable phases at:",b""),
    native()+b"T(K) = 506.722\n"])
def test_bad_native_readback(raw):
    with pytest.raises(ValueError,match="C03FC"):
        f.capture(raw,point())


def fixture():
    cols=sorted(set(f.c.ORDER)|{"H2O"})
    norm={k:0.1 for k in cols}
    body=["Phase Compositions (molar  proportions):",
          "phase wt % vol % mol % "+" ".join(cols),
          "synthetic 100.00 100.00 100.00 1.000 "+" ".join(["0.100"]*10),
          "Phase speciation (molar proportions):","Bulk Composition:","mol g wt % mol/kg"]
    body += [k+" 0.100 1.000 10.00 0.100" for k in cols]
    body += ["Other Bulk Properties:","Molar Properties and Density:",
             "System 30.000 -100.0 10.00 1.000 12.000 0.01 0.01 1.00 3000.0",
             "Seismic Properties:"]
    return {"id":"test","output_text":"\n".join(body)},norm


def test_closed_all_ten():
    p,n=fixture()
    result=f.audit_closed(p,n)
    assert set(result["bulk_closure_at_print_precision"])==set(n)
    assert result["native_bulk_readback_verified"]
    assert not result["scientific_promotion"]


@pytest.mark.parametrize("component",["H2O","O2"])
def test_closed_input_not_exempt(component):
    p,n=fixture()
    n[component]=0.2
    with pytest.raises(ValueError,match="CONSERVED_INPUT_CLOSURE:"+component):
        f.audit_closed(p,n)


def test_modal_closure():
    p,n=fixture()
    p["output_text"]=p["output_text"].replace("synthetic 100.00","synthetic 90.00")
    with pytest.raises(ValueError,match="MODAL_CLOSURE"):
        f.audit_closed(p,n)


def test_new_archive_and_limits():
    assert f.OUT!=f.r.OUT and f.LIMITS["walltime_s"]==180
