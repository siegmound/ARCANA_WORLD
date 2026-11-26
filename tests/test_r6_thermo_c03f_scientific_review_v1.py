import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03f_scientific_review as r


def test_signed_speciation_not_silently_clipped():
    text=("Phase speciation (molar proportions):\n"
          "Chl(W) afchl: 0.20000, och2: -0.20000, clin: 1.00000\n"
          "Structural formulae for 688 format solution models:")
    rows,neg=r.speciation(text,"x")
    assert rows[0]["coefficients"]["och2"]=="-0.20000"
    assert neg[0]["endmember"]=="och2"


def test_speciation_not_normalized_by_force():
    text=("Phase speciation (molar proportions):\n"
          "Chl(W) clin: 0.40000\nStructural formulae for 688 format solution models:")
    with pytest.raises(ValueError,match="SPECIATION_SUM"):
        r.speciation(text,"x")


def test_sites_printed_rounding():
    text=("Structural formulae for 688 format solution models:\n"
          "Phase Site Multiplicity Molar Site Fractions\n"
          "Chl(W)\n M1 1.00 Al(.0565)Fe(.3537)Mg(.5898)\n"
          "Molar Properties and Density:")
    assert r.site_review(text)[0]["printed_range_and_sum_compatible"]


def test_sites_negative_is_not_accepted():
    text=("Structural formulae for 688 format solution models:\n"
          "Chl(W)\n M1 1.00 Al(-.0100)Fe(1.0100)\nMolar Properties and Density:")
    assert not r.site_review(text)[0]["printed_range_and_sum_compatible"]


def test_elastic_printed_intervals():
    text=("Molar Properties and Density:\n"
          "System 6205.49 -82441024 7455.0 203.14 6046.4 0.25044E-04 0.11818E-05 1.0091 3054.8\n"
          "Seismic Properties:\n"
          "System 0.75377 0.88579E+06 0.45493E+06 5.3849 6.9896 3.8591 0.28074\n"
          "Bulk Composition:")
    result=r.elastic_review(text)
    assert all(result["printed_elastic_checks"].values())
    assert result["Ks_Pa"]==88579000000


def test_review_archive_is_distinct():
    assert r.OUT!=r.f.OUT


def model_fixture():
    return (b"header\nBio(TCC)\nabbreviation bi\nphl ann\nend_of_model\n"
            b"Chl(W)\nabbreviation chl\noch2 clin\nend_of_model\n")


def test_model_blocks_real_parser_contract():
    raw=model_fixture()
    neg=[{"model":"Bio(TCC)","endmember":"phl"},
         {"model":"Chl(W)","endmember":"och2"}]
    models,metadata=r.extract_model_blocks(raw,neg)
    assert models["Bio(TCC)"].startswith("Bio(TCC)\n")
    assert metadata["Chl(W)"]["line"]==6
    assert metadata["Bio(TCC)"]["normalized_text_sha256"]==r.hgp.sha(models["Bio(TCC)"].encode())


@pytest.mark.parametrize("model,member",[("missing","phl"),("Bio(TCC)","missing")])
def test_model_blocks_missing_identity(model,member):
    with pytest.raises(ValueError,match="C03FR"):
        r.extract_model_blocks(model_fixture(),[{"model":model,"endmember":member}])


def test_comment_only_endmember_not_evidence():
    raw=model_fixture().replace(b"phl ann",b"ann | phl")
    with pytest.raises(ValueError,match="NEGATIVE_SOURCE_IDENTITY"):
        r.extract_model_blocks(raw,[{"model":"Bio(TCC)","endmember":"phl"}])
