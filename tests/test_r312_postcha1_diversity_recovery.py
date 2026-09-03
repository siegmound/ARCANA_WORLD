from __future__ import annotations

from pathlib import Path
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.scientific_engines import r311_postcha1_recovery as r311
from arcana_worldsim.scientific_engines import r312_postcha1_diversity_recovery as r312


def _metadata_rows():
    d = json.loads((ROOT / "references/v0_6D1_R3/D1_SPECIES_METADATA.json").read_text(encoding="utf-8"))
    return d["species"] if isinstance(d, dict) and "species" in d else d


def test_parent_r311_authority_is_exact_sealed_boundary():
    a = r312.validate_parent_r311_authority(ROOT)
    st = a["state"]
    assert st.age_ma == 61.0
    assert st.elapsed_year == 149_000_000.0
    assert len(set(st.current_species)) == 95
    assert len(st.component_ids) == 236
    assert a["checkpoint_json_sha256"] == "bdf75d08bd39181dee3331f91b1dd6864ab8e0c1e88c94eed7813d148aebda3b"
    assert a["checkpoint_npz_sha256"] == "4f4582ca7f83926941f7224033a83356b2f5df196dcb8d3dbafae2e9b16e987c"
    assert a["summary_sha256"] == "b8194132711925d7ea2f67d0bf9bd7d9ad995ae37bef2f18df6c2fab49524bbd"
    counts = r312.event_counts(st)
    assert counts["CHA1_species_extinction"] == 212
    assert counts["CHA1_high_resolution_event_bridge_complete"] == 1
    assert counts["post_CHA1_ordinary_lifecycle_thaw"] == 1


def test_r312_scientific_parameters_are_r311_authority_not_retuned():
    cfg = r312.R312Config()
    parent = r311.R311Config()
    fields = [
        "biology_cadence_years", "transport_cadence_years", "speciation_check_interval_years",
        "ordinary_extinction_check_interval_years", "ordinary_extinction_minimum_persistence_years",
        "founder_minimum_persistence_years", "vicariance_persistence_min_years", "reconnection_persistence_min_years",
        "mutation_variance_supply_normalized_per_myr", "nonlinear_stabilizing_variance_depletion_per_myr_per_q",
        "selection_variance_depletion_per_generation", "variance_ceiling_normalized",
        "migration_reference_years", "migration_fraction_ceiling", "gene_flow_ceiling_per_step",
        "minimum_effective_isolation_generations", "minimum_intrinsic_ri", "minimum_trait_distance",
        "maximum_effective_exchange_pressure", "adaptive_k_eff", "segregation_recombination_fraction_per_generation",
        "deme_fission_check_interval_years", "reconnection_check_interval_years",
    ]
    for f in fields:
        assert getattr(cfg, f) == getattr(parent, f), f
    assert cfg.end_age_ma == 46.0
    assert "WITHOUT_RICHNESS_TARGET" in cfg.diversity_recovery_semantics


def test_canonical_window_is_exactly_plus_five_to_plus_twenty_myr_after_impact():
    assert r312.IMPACT_AGE_MA - r312.START_AGE_MA == 5.0
    assert r312.IMPACT_AGE_MA - r312.END_AGE_MA == 20.0
    assert int(round((r312.START_AGE_MA - r312.END_AGE_MA) * 1e6 / r312.R312Config().biology_cadence_years)) == 120


def test_recovery_metrics_are_descriptive_not_acceptance_targets():
    st = r312.validate_parent_r311_authority(ROOT)["state"]
    report = r312.diversity_recovery_report(st, st)
    assert report["reference_only_not_acceptance_targets"] is True
    assert report["pre_CHA1_species_reference"] == 305
    assert report["post_CHA1_500ky_species_reference"] == 93
    assert report["R3_11_61Ma_species"] == 95
    assert report["final_species"] == 95
    assert report["net_species_recovered_since_post_CHA1_500ky"] == 2
    assert np.isclose(report["fraction_of_direct_CHA1_species_loss_recovered"], 2 / 212)
    assert "No richness level" in report["interpretation_guard"]


def test_r312_one_step_continues_without_second_thaw_or_cha1_reapplication():
    parent = r312.validate_parent_r311_authority(ROOT)["state"]
    before = r312.event_counts(parent)
    a1 = np.load(ROOT / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz", allow_pickle=False)
    out, records = r312.run_diversity_recovery(parent, a1, _metadata_rows(), r312.R312Config(), end_age_ma=60.875)
    after = r312.event_counts(out)
    assert len(records) == 1
    assert out.age_ma == 60.875
    assert after["CHA1_species_extinction"] == before["CHA1_species_extinction"]
    assert after["CHA1_high_resolution_event_bridge_complete"] == before["CHA1_high_resolution_event_bridge_complete"]
    assert after["post_CHA1_ordinary_lifecycle_thaw"] == before["post_CHA1_ordinary_lifecycle_thaw"] == 1
    # Low-level continuation must not mutate the authoritative parent object.
    assert parent.age_ma == 61.0
    assert r312.event_counts(parent) == before
