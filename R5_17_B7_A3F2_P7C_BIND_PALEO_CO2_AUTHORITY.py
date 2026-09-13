from __future__ import annotations

import bisect
import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path

HEAD = "43731502aa210f0714473f0f71606eaf5f769375"
CO2 = Path(".arcana_engines/CO2_authority/antarctica2015co2composite-noaa.txt")
P7T = Path("R5_17_B7_A3F2_P7T_HUMAN_SUPPORT_TEMPORAL_SNAPSHOT_AUTHORITY.json")
REGISTRY = Path("R5_17_B7_A3F2_P7T_TEMPORAL_SNAPSHOT_REGISTRY.csv")
OUT_JSON = Path("R5_17_B7_A3F2_P7C_PALEO_CO2_AUTHORITY_BINDING.json")
OUT_MD = Path("R5_17_B7_A3F2_P7C_PALEO_CO2_AUTHORITY_BINDING.md")
OUT_CSV = Path("R5_17_B7_A3F2_P7C_CO2_SNAPSHOT_BINDING.csv")
AGES = [200.0, 125.0, 120.0, 20.0, 15.0, 14.0, 13.0, 12.0, 11.0, 10.0, 5.0, 0.0]
DATUM_BP = 200.0


def main() -> int:
    head = subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    if head != HEAD:
        raise RuntimeError("ARCANA HEAD changed during P7C")
    if not CO2.is_file() or not P7T.is_file() or not REGISTRY.is_file():
        raise RuntimeError("P7C requires the cached NOAA authority and P7T registry")
    p7t = json.loads(P7T.read_text(encoding="utf-8"))
    p7t_ages = [float(x) for x in p7t["shared_temporal_registry"]["ages_ka_before_model_present"]]
    if p7t["decision"] != "HUMAN_SUPPORT_TEMPORAL_SNAPSHOT_AUTHORITY_READY" or p7t_ages != AGES:
        raise RuntimeError("P7T temporal authority changed; refusing independent age selection")
    with REGISTRY.open(newline="", encoding="utf-8") as f:
        registry_ages = [float(row["age_ka"]) for row in csv.DictReader(f)]
    if registry_ages != AGES:
        raise RuntimeError("P7T CSV registry does not match P7T JSON")

    raw = CO2.read_bytes()
    data = [line.split() for line in CO2.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
    header, parsed = data[0], [[float(v) for v in row] for row in data[1:]]
    ages_bp = [row[0] for row in parsed]
    co2 = [row[1] for row in parsed]
    if header != ["age_gas_calBP", "co2_ppm", "co2_1s_ppm"] or len(parsed) != 1901:
        raise RuntimeError("unexpected NOAA schema or row count")
    if any(not math.isfinite(v) for row in parsed for v in row) or any(ages_bp[i] > ages_bp[i + 1] for i in range(len(ages_bp) - 1)) or len(set(ages_bp)) != len(ages_bp):
        raise RuntimeError("NOAA ages are not finite, monotonic, and unique")

    bound = []
    for age_ka in AGES:
        requested = age_ka * 1000.0 + DATUM_BP
        if requested < ages_bp[0] or requested > ages_bp[-1]:
            raise RuntimeError(f"mapped snapshot outside NOAA coverage: {requested}")
        pos = bisect.bisect_left(ages_bp, requested)
        if pos < len(ages_bp) and ages_bp[pos] == requested:
            left_age = right_age = requested
            left_co2 = right_co2 = co2[pos]
            method = "EXACT_OBSERVATION"
            result_co2 = co2[pos]
            width = left_distance = right_distance = 0.0
        else:
            if pos == 0 or pos == len(ages_bp):
                raise RuntimeError("extrapolation would be required")
            left_age, right_age = ages_bp[pos - 1], ages_bp[pos]
            left_co2, right_co2 = co2[pos - 1], co2[pos]
            width = right_age - left_age
            left_distance, right_distance = requested - left_age, right_age - requested
            result_co2 = left_co2 + (right_co2 - left_co2) * left_distance / width
            method = "INTERPOLATED_WITHIN_BRACKET"
        if not math.isfinite(result_co2):
            raise RuntimeError("non-finite CO2 binding")
        bound.append({"arcana_age_ka": age_ka, "arcana_age_years": age_ka * 1000.0, "mapped_external_age_bp": requested, "left_record_age_bp": left_age, "right_record_age_bp": right_age, "left_co2_ppm": left_co2, "right_co2_ppm": right_co2, "method": method, "result_co2_ppm": result_co2, "bracket_width_years": width, "distance_to_left_years": left_distance, "distance_to_right_years": right_distance, "source_dataset": "noaa-icecore-17975", "authority_status": "VALIDATED_EXTERNAL_PHYSICAL_AUTHORITY"})
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        fields = list(bound[0])
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(bound)
    max_width = max(row["bracket_width_years"] for row in bound)
    result = {
        "stage": "R5.17-B7-A3F2-P7C", "status": "P7C_AUTHORITY_BOUND", "parent_head": HEAD,
        "parent_p7t_decision": p7t["decision"], "human_support_operational_domain": "200 ka -> 0 ka",
        "age_axis_policy": "RELATIVE_NATURAL_FORCING_DATUM_ALIGNMENT", "arcana_time_axis_class": "MODEL_RELATIVE_BEFORE_PRESENT", "arcana_zero_ka_semantics": "relative simulation endpoint; not literal Gregorian identity",
        "co2_modeling_datum": {"name": "EARTH_PREINDUSTRIAL_1750_CE", "datum_calendar_interpretation": "1750 CE preindustrial greenhouse-gas comparison baseline", "datum_age_bp": DATUM_BP, "scientific_reference": "IPCC AR6 preindustrial baseline convention; approximately 278.3 ppm CO2 reference", "is_modeling_datum": True, "is_arcana_calendar_identity": False},
        "mapping_formula": "external_age_BP = (arcana_age_ka * 1000) + 200",
        "co2_datum_offset_years": 200, "noaa_time_axis": "calendar years BP, external present 1950 AD", "anthropogenic_tail_adjudication": "ANTHROPOGENIC_TAIL_EXCLUDED_FROM_NATURAL_BASELINE",
        "external_authority": {"dataset": "Antarctic Ice Cores Revised 800KYr CO2 Data", "identifier": "noaa-icecore-17975", "doi": "10.25921/n8y4-bp27", "source": "https://www.ncei.noaa.gov/pub/data/paleo/icecore/antarctica/antarctica2015co2composite-noaa.txt", "local_path": str(CO2.resolve()), "size_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "row_count": len(parsed), "header": header, "units": "years BP for age; ppm for CO2", "monotonic_non_decreasing": True, "duplicate_ages": 0, "missing_values": False, "coverage": {"min_age_years_bp": min(ages_bp), "max_age_years_bp": max(ages_bp)}},
        "coverage_after_mapping": {"full_physical_coverage": True, "mapped_oldest_bp": max(row["mapped_external_age_bp"] for row in bound), "mapped_youngest_bp": min(row["mapped_external_age_bp"] for row in bound), "no_extrapolation": True},
        "snapshot_binding": {"snapshot_count": len(bound), "exact_count": sum(row["method"] == "EXACT_OBSERVATION" for row in bound), "interpolated_count": sum(row["method"] == "INTERPOLATED_WITHIN_BRACKET" for row in bound), "unresolved_count": 0, "rows": bound, "csv_path": str(OUT_CSV), "csv_sha256": hashlib.sha256(OUT_CSV.read_bytes()).hexdigest(), "BIOME4_CO2_INPUT_READY": True},
        "interpolation_quality": {"status": "PASS" if max_width <= 5000 else "PASS_WITH_FLAGGED_GAPS", "maximum_bracket_width_years": max_width, "flag_threshold_years": 5000, "spline": False, "smoothing": False, "climate_fitting": False},
        "zero_ka_sanity_check": {"mapped_age_bp": 200.0, "co2_ppm": bound[-1]["result_co2_ppm"], "preindustrial_regime_check": 250.0 <= bound[-1]["result_co2_ppm"] <= 310.0, "reference_ppm_not_forced": 278.3},
        "authority_role": "EXTERNAL_GLOBAL_ATMOSPHERIC_FORCING_ANALOG", "not_role": ["ARCANA_DIRECT_OBSERVATION", "ARCANA_CARBON_CYCLE_SIMULATION"],
        "chronology_consistency": "SMALL_DECLARED_DATUM_OFFSET",
        "governance": {"BIOME4_runtime_ready": True, "BIOME4_scientific_run": False, "PALEO_CO2_AUTHORITY_BOUND": True, "physical_npp_materialized": False, "soil_physical_state_materialized": False, "Madingley_invoked": False, "animal_resource_support_materialized": False, "human_management_used": False, "population_target_used": False, "k_x_t_materialized": False, "canonical_mutation": False, "AQUATIC_MARINE_RESOURCE_SUPPORT": "NOT_MATERIALIZED"},
        "decision": "PALEO_CO2_AUTHORITY_READY_WITH_INTERPOLATION", "recommended_next": "P7S using the exact P7T shared temporal registry",
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text("# R5.17-B7-A3F2-P7C\n\n## Decision\n\n**PALEO_CO2_AUTHORITY_READY_WITH_INTERPOLATION**. The exact P7T registry is bound to the cached NOAA/NCEI physical CO₂ authority over the 200 ka -> 0 ka human-support domain.\n\nThe selected policy is `RELATIVE_NATURAL_FORCING_DATUM_ALIGNMENT` with a 200-year modeling offset: `external_age_BP = (arcana_age_ka * 1000) + 200`. This uses the Earth preindustrial 1750 CE convention as a modeling datum only; ARCANA 0 ka remains a relative simulation endpoint, not a literal Earth calendar identity.\n\nAll 12 snapshots are within NOAA coverage with no extrapolation. The anthropogenic tail is excluded. CO₂ values are bound in the companion CSV for P7S/BIOME4 routing; no BIOME4 scientific run, physical NPP, soil, Madingley, animal resource support, `K(x,t)`, state/index update, staging, commit, or push occurred. `AQUATIC_MARINE_RESOURCE_SUPPORT = NOT_MATERIALIZED`.\n", encoding="utf-8")
    print(f"wrote {OUT_JSON}, {OUT_MD}, and {OUT_CSV}")


if __name__ == "__main__":
    main()
