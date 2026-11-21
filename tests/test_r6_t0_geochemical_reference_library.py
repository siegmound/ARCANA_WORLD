"""R6 Earth oxide reference provenance and unknown ARCANA chemistry are distinct."""
import hashlib
import json
from pathlib import Path

import pytest

from experiments.t0_geochemical_reference_v1.compile_references import (
    DATA, ROOT, R6_SOURCES, SOURCES, GeochemistrySourceError,
    build, continental_reference, depleted_mantle_reference,
    oceanic_morb_trace_reference, elemental_oxide_budget,
    git_blob_sha, read_r6_support, source_bytes,
)

def test_original_two_earth_research_tables_byte_identical_to_pinned_upstream():
    for name, sha in SOURCES.items():
        raw,digest=source_bytes(DATA/name,sha)
        assert git_blob_sha(raw)==sha
        assert digest==hashlib.sha256(raw).hexdigest()

def test_published_rudnick_gao_four_reference_profiles_remain_unassigned():
    records=continental_reference((DATA/"CC__Rudnick_Gao__2014.csv").read_bytes())
    assert len(records)==4
    assert records[0]["source_major_oxides_wt_percent"]["SiO2"]==66.6
    assert records[3]["source_major_oxides_wt_percent"]["SiO2"]==60.6
    assert records[0]["selected_source_trace_elements"]["U"]["value"]==2.7
    assert records[0]["selected_source_trace_elements"]["U"]["unit"]=="ppm"
    assert all(x["arcana_cell_assignments"]==0 for x in records)
    assert all(x["physical_rock_phase_assemblage"] is None for x in records)
    assert all(x["mass_budget"]["oxide_to_element_budget_conserved"] for x in records)

def test_published_salters_stracke_depleted_mantle_h2o_is_only_earth_model():
    r=depleted_mantle_reference((DATA/"DM__Salters_Stracke__2004.csv").read_bytes())
    assert r["source_major_oxides_wt_percent"]["SiO2"]==44.9
    assert r["water_model"]["H2O_mass_concentration_ppm"]==116.
    assert r["water_model"]["IS_NOT_ARCANA_PORE_PRESSURE_OR_MANTLE_HYDRATION"]
    assert r["arcana_fault_assignments"]==0
    assert r["mass_budget"]["oxide_to_element_budget_conserved"]
    assert r["physical_rock_phase_assemblage"] is None

def test_oxide_stoichiometry_mass_balance_exact_without_mineral_inference():
    result=elemental_oxide_budget({"SiO2":100.})
    assert result["source_major_oxide_subset_total_wt_percent"]==100.
    assert result["oxide_equivalent_element_mass_wt_percent"]["Si"]==pytest.approx(
        100*28.085/(28.085+2*15.999))
    assert result["oxide_equivalent_element_mass_wt_percent"]["O"]==pytest.approx(
        100*2*15.999/(28.085+2*15.999))
    assert result["normative_mineral_modal_percent"] is None

def test_feo_star_is_only_feo_equivalent_not_ferric_speciation():
    result=elemental_oxide_budget({"FeO*":10.,"SiO2":80.})
    assert result["oxygen_from_FeO_equivalent_is_not_Fe_redox"]
    assert result["source_major_oxide_subset_total_wt_percent"]==90.
    assert result["unaccounted_components_and_volatiles_wt_percent"] is None

@pytest.mark.parametrize("value",[-1.,float("nan"),float("inf")])
def test_negative_nan_inf_source_oxide_values_fail_closed(value):
    with pytest.raises(GeochemistrySourceError):
        elemental_oxide_budget({"SiO2":value})

def test_unknown_oxide_cannot_use_implicit_molecular_weight():
    with pytest.raises(GeochemistrySourceError,match="UNKNOWN_OXIDE"):
        elemental_oxide_budget({"MINERAL_FAKE":10.})

def test_continental_literature_table_header_and_units_are_not_guessed():
    original=(DATA/"CC__Rudnick_Gao__2014.csv").read_bytes()
    bad=original.replace(b"SiO2,wt.%",b"SiO2,ppm",1)
    with pytest.raises(GeochemistrySourceError,match="UNITS_INCOMPLETE"):
        continental_reference(bad)

def test_mantle_H2O_must_be_ppm_not_mass_percent():
    original=(DATA/"DM__Salters_Stracke__2004.csv").read_bytes()
    bad=original.replace(b'"H2O","116","ppm"',b'"H2O","116","wt%"',1)
    assert bad!=original
    with pytest.raises(GeochemistrySourceError,match="WRONG_UNITS"):
        depleted_mantle_reference(bad)

def test_native_t0_grid_restricted_thermal_support_not_composition():
    out=read_r6_support(ROOT)
    assert out["native_cells"]==64800
    assert out["thermal_support_admitted"]==63620
    assert out["continental_thermal_support"]==14258
    assert out["positive_age_ocean_thermal_support"]==49362
    assert out["geologically_unresolved_ocean_support"]==1072
    assert out["age_zero_ridge_excluded"]==108
    assert out["geochemical_composition_assigned_cells"]==0
    assert out["no_global_or_regional_mineral_facies_are_inferred"]

def test_exact_referenced_r6_material_source_git_blobs_are_pinned():
    for filepath,blob in R6_SOURCES.items():
        raw,digest=source_bytes(ROOT/filepath,blob)
        assert git_blob_sha(raw)==blob and len(digest)==64

def test_full_real_earth_reference_compilation_never_writes_history(tmp_path):
    out=tmp_path/"EARTH_REFERENCE_NEW"
    summary=build(ROOT,out)
    assert summary["earth_reference_records"]==6
    assert summary["T0_composition_assignments"]==0
    assert summary["T0_mineral_phase_assignments"]==0
    assert summary["T0_fault_gouge_assignments"]==0
    assert summary["physical_T1"] is None
    report=json.loads((out/"REPORT.json").read_text())
    assert len(report["Earth_reference_analogues"])==6
    assert report["planetary_composition_field_T0"] is None
    assert report["fault_mineralogy_hydration_porosity_pore_pressure"] is None
    assert report["ore_deposit_resource_field"] is None
    assert report["Deep_X_accessibility_field"] is None
    assert report["mechanical_solve_authorized"] is False
    manifest=json.loads((out/"MANIFEST.json").read_text())
    assert manifest["files"]["REPORT.json"]==hashlib.sha256(
        (out/"REPORT.json").read_bytes()).hexdigest()
    assert manifest["no_canonical_promotion"]
    with pytest.raises(GeochemistrySourceError,match="OUTPUT_ALREADY_EXISTS"):
        build(ROOT,out)

def test_source_mutation_detected_before_geochemical_analysis(tmp_path):
    altered=tmp_path/"CC__Rudnick_Gao__2014.csv"
    altered.write_bytes((DATA/"CC__Rudnick_Gao__2014.csv").read_bytes()+b" ")
    with pytest.raises(GeochemistrySourceError,match="SOURCE_GIT_BLOB_SHA_MISMATCH"):
        source_bytes(altered,SOURCES[altered.name])

def test_published_sun_mcdonough_n_morb_is_trace_only_no_units_guessed():
    r=oceanic_morb_trace_reference((DATA/"Sun_McDonough__1989.csv").read_bytes())
    assert r["reference_id"]=="EARTH_SUN_MCDONOUGH_1989_N_TYPE_MORB_TRACE"
    assert r["source_trace_values_units_unverified"]["U"]==0.047
    assert r["source_trace_unit"] is None
    assert r["major_oxide_mass_budget"] is None
    assert r["bulk_oceanic_crust_composition"] is None
    assert r["arcana_cell_assignments"]==0


def test_n_morb_missing_units_must_not_be_implicitly_ppm():
    r=oceanic_morb_trace_reference((DATA/"Sun_McDonough__1989.csv").read_bytes())
    assert r["no_automatic_oxide_or_element_mass_conversion"] is True
    assert r["source_trace_unit"] is None
