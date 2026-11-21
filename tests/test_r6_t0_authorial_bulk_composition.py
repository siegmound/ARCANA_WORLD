"""R6 source-provenanced authorial bulk-rock chemistry: all values explicit."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from experiments.t0_authorial_composition_v1 import provider as p

ROOT=Path(__file__).resolve().parents[1]


def recipe(name="RC1",role="CONTINENTAL_CRUST_BULK",si=60.,iron=40.):
    return {
      "id":name,"role":role,
      "authority":p.AUTHORITY,
      "rationale":"Explicit hypothetical bulk chemistry, never natural T0 mineralogy",
      "source":{"kind":"AUTHORIAL_EXPLICIT_HYPOTHESIS",
                "reference":"SYNTHETIC_UNIT_TEST_ONLY"},
      "basis":"AS_REPORTED_WT_PERCENT_NO_NORMALIZATION",
      "oxides":{
        "SiO2":{"unit":"wt.%","value":si,"low":si-1,"high":si+1},
        "FeO*":{"unit":"wt.%","value":iron,"low":iron-1,"high":iron+1}},
      "full_chemistry_known":False,
      "Fe_redox_speciation":None,
      "water_wt_pct":None,"pore_pressure_pa":None,"oxygen_fugacity":None}


def scenario():
    s=p.make_template(ROOT)
    s["scenario_id"]="SYNTHETIC_EXPLORATION_001"
    s["recipes"]=[recipe(),recipe("RC2",si=70,iron=30)]
    s["mixtures"]=[{"id":"MX1","components":[
       {"recipe_id":"RC1","mass_fraction":0.6},
       {"recipe_id":"RC2","mass_fraction":0.4}]}]
    return s


def test_governed_original_64800_index_and_63620_thermal_support_stay_separate():
    x=p.source_index(ROOT)
    assert x["partition_counts"]["native"]==64800
    assert x["partition_counts"]["admitted"]==63620
    assert x["partition_counts"]["unresolved_positive_age_ocean_excluded"]==1072
    assert x["partition_counts"]["zero_age_ridge_excluded"]==108


def test_unselected_authorial_template_is_empty_and_no_t0():
    t=p.make_template(ROOT)
    assert t["recipes"]==t["mixtures"]==t["placements"]==[]
    assert not t["authorial_selection_confirmed"]
    assert t["physical_T1"] is None
    assert not t["canonical_T0_materialization_authorized"]


def test_authorial_bulk_oxide_recipe_conserves_element_budget_without_minerals():
    v=p.oxide_recipe(recipe())
    assert v["oxide_subset_total_wt_percent"]==pytest.approx(100.)
    assert v["elemental_oxide_equivalent_budget"]["oxide_to_element_budget_conserved"]
    assert v["natural_mineral_assemblage"] is None
    assert v["iron_redox_fluid_thermodynamic_state"] is None


def test_explicit_60_40_mass_mixture_matches_analytic_oxide_budget():
    s=scenario()
    result=p.compile_scenario(s,ROOT)
    a=result["experimental_mass_mixture_records"][0]
    assert a["oxide_mass_wt_percent"]["SiO2"]==pytest.approx(64.)
    assert a["oxide_mass_wt_percent"]["FeO*"]==pytest.approx(36.)
    assert a["oxide_authorial_intervals_wt_percent"]["SiO2"]==pytest.approx([63.,65.])
    assert a["oxide_subset_total_wt_percent"]==pytest.approx(100.)
    assert a["elemental_oxide_equivalent_budget"]["oxide_to_element_budget_conserved"]
    assert result["hypothetical_native_cell_assignment_count"]==0
    assert result["physically_ratified_T0_composition_cell_count"]==0
    assert result["physical_T0_bulk_chemistry"] is None
    assert result["Deep_mode_accessibility"] is None
    assert result["ore_deposits_and_resources"] is None
    assert result["physical_T1"] is None


@pytest.mark.parametrize("bad,tag",[
    ("mass","MASS_FRACTIONS_NOT_CONSERVED"),
    ("duplicate","MIXTURE_RECIPE_INVALID_OR_DUPLICATED"),
    ("role","INCOMPATIBLE_ROLES_OR_OXIDE_BASIS"),
    ("missing_silica","OXIDES_MISSING_OR_UNSUPPORTED"),
    ("both_iron","IRON_CONVENTION_AMBIGUOUS"),
    ("fluid","UNQUALIFIED_PHASE_FLUID_OR_FULL_CHEMISTRY"),
    ("unit","OXIDE_UNIT_OR_INTERVAL_REQUIRED"),
    ("interval","NOMINAL_OUTSIDE_INTERVAL"),
    ("negative","INVALID_NUMBER"),
    ("redox","UNQUALIFIED_PHASE_FLUID_OR_FULL_CHEMISTRY"),
])
def test_invalid_authorial_chemical_or_mixing_claims_fail_closed(bad,tag):
    s=scenario()
    if bad=="mass":s["mixtures"][0]["components"][0]["mass_fraction"]=0.61
    if bad=="duplicate":s["mixtures"][0]["components"][1]["recipe_id"]="RC1"
    if bad=="role":s["recipes"][1]["role"]="OCEANIC_CRUST_BULK"
    if bad=="missing_silica":s["recipes"][0]["oxides"].pop("SiO2")
    if bad=="both_iron":s["recipes"][0]["oxides"]["FeO"]=s["recipes"][0]["oxides"]["FeO*"]
    if bad=="fluid":s["recipes"][0]["water_wt_pct"]=.3
    if bad=="unit":s["recipes"][0]["oxides"]["SiO2"]["unit"]="ppm"
    if bad=="interval":s["recipes"][0]["oxides"]["SiO2"]["low"]=61.
    if bad=="negative":s["recipes"][0]["oxides"]["SiO2"]["value"]=-1.
    if bad=="redox":s["recipes"][0]["Fe_redox_speciation"]=0.2
    with pytest.raises(p.SourceAuthorityError,match=tag):
        p.compile_scenario(s,ROOT)


def test_unapproved_native_placement_and_missing_original_package_rejected():
    s=scenario()
    s["placements"]=[{"cell_id":"R6G1D-R000-C000",
        "plate_id":5,"crust_domain_id":4,"recipe_or_mixture_id":"MX1"}]
    with pytest.raises(p.SourceAuthorityError,match="SPATIAL_SOURCE_PROVIDERS_REQUIRED"):
        p.compile_scenario(s,ROOT)


def test_refuse_native_placement_even_with_source_files_but_no_author_approval(tmp_path):
    s=scenario()
    s["placements"]=[{"cell_id":"R6G1D-R000-C000",
        "plate_id":5,"crust_domain_id":4,"recipe_or_mixture_id":"RC1"}]
    with pytest.raises(p.SourceAuthorityError,match="AUTHORIAL_SELECTION_UNCONFIRMED"):
        p.compile_scenario(s,ROOT,field_package=tmp_path/"a",
                           plate_partition=tmp_path/"b",
                           admitted_membership=tmp_path/"c")


def test_original_binary_must_have_exact_source_sha(tmp_path):
    path=tmp_path/"fake.npz";path.write_bytes(b"fake")
    with pytest.raises(p.SourceAuthorityError,match="ORIGINAL_BINARY_SOURCE_SHA_MISMATCH"):
        p.pinned_npz(path,p.FIELD_SHA)


def test_unique_write_once_report_and_manifest_t0_is_null(tmp_path):
    s=scenario()
    result=p.compile_scenario(s,ROOT)
    out=tmp_path/"NEW"
    raw=json.dumps(s).encode()
    p.write_report(out,result,raw)
    report=json.loads((out/"REPORT.json").read_text())
    man=json.loads((out/"MANIFEST.json").read_text())
    assert man["source_scenario_sha256"]==hashlib.sha256(raw).hexdigest()
    assert man["files"]["REPORT.json"]==hashlib.sha256(
        (out/"REPORT.json").read_bytes()).hexdigest()
    assert man["no_canonical_promotion"] and man["no_T1"]
    assert report["mechanical_solve_authorized"] is False
    assert report["physical_T1"] is None
    with pytest.raises(p.SourceAuthorityError,match="OUTPUT_EXISTS_NO_OVERWRITE"):
        p.write_report(out,result,raw)


def test_source_index_original_git_blob_must_not_change(tmp_path):
    dst=tmp_path/p.INDEX
    dst.parent.mkdir(parents=True)
    dst.write_bytes((ROOT/p.INDEX).read_bytes()+b"x")
    with pytest.raises(p.SourceAuthorityError,match="SOURCE_HASH_DRIFT"):
        p.source_index(tmp_path)


def test_exact_63620_line_id_membership_sha_required(tmp_path):
    x=tmp_path/"bad.txt"
    x.write_text("R6G1D-R000-C000\n")
    with pytest.raises(p.SourceAuthorityError,match="MEMBERSHIP_HASH_MISMATCH"):
        p.exact_member_ids(x,"0"*64)


def test_synthetic_full_native_placement_source_validated_but_never_physical(tmp_path,monkeypatch):
    """Synthetic 180x360 original-style data; no real ARCANA selection is claimed."""
    s=scenario()
    s["placements"]=[{"cell_id":"R6G1D-R000-C000",
        "plate_id":5,"crust_domain_id":4,"recipe_or_mixture_id":"MX1"}]
    s["authorial_selection_confirmed"]=True
    s["authorial_selection_id"]="SYNTHETIC_FAKE_AUTHOR_APPROVAL"
    fields=tmp_path/"field.npz"
    plates=tmp_path/"plates.npz"
    members=tmp_path/"members.txt"
    np.savez(fields,physical_crust_domain_id=np.full((180,360),4,dtype=np.int16))
    rr,cc=np.indices((180,360))
    lab=np.tile(np.arange(1,13,dtype=np.int16),5400)
    lab[0]=5
    np.savez(plates,face_row=rr.reshape(-1).astype(np.int16),
             face_col=cc.reshape(-1).astype(np.int16),
             face_plate_id=lab)
    # Only a synthetic membership fixture; never a real authoritative R6 index.
    ids=[f"R6G1D-R{r:03d}-C{c:03d}"
         for r in range(180) for c in range(360)][:63620]
    members.write_text("".join(x+"\n" for x in ids))
    digest=p.sha(members.read_bytes())
    monkeypatch.setattr(p,"FIELD_SHA",p.sha(fields.read_bytes()))
    monkeypatch.setattr(p,"PLATE_SHA",p.sha(plates.read_bytes()))
    idx=p.source_index(ROOT)
    idx["membership_sha256"]["ADMITTED_INITIALIZER_SUPPORT"]=digest
    monkeypatch.setattr(p,"source_index",lambda _:idx)
    s["field_package_sha256"]=p.FIELD_SHA
    s["plate_partition_sha256"]=p.PLATE_SHA
    result=p.compile_scenario(s,ROOT,field_package=fields,
        plate_partition=plates,admitted_membership=members)
    assert result["hypothetical_native_cell_assignment_count"]==1
    assert result["physically_ratified_T0_composition_cell_count"]==0
    assert result["physical_T0_bulk_chemistry"] is None
    s["placements"][0]["plate_id"]=8
    with pytest.raises(p.SourceAuthorityError,match="PLATE_OR_CRUST_SOURCE_BINDING_MISMATCH"):
        p.compile_scenario(s,ROOT,field_package=fields,
            plate_partition=plates,admitted_membership=members)
    s["placements"][0]["plate_id"]=5
    s["placements"][0]["cell_id"]="R6G1D-R179-C359"
    with pytest.raises(p.SourceAuthorityError,match="CELL_NOT_PROVEN_ADMITTED"):
        p.compile_scenario(s,ROOT,field_package=fields,
            plate_partition=plates,admitted_membership=members)
