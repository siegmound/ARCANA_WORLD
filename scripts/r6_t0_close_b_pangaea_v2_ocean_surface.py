"""Materialize the versioned GDH1 T0 ocean-surface closure."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.t0_materialization.b_pangaea_v2 import close_ocean_surface


def main() -> int:
    report = close_ocean_surface(ROOT)
    (ROOT / "R6_T0_B_PANGAEA_LIKE_V2_OCEAN_SURFACE_CLOSURE.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    closure_file = ROOT / "R6_T0_B_PANGAEA_LIKE_V2_OCEAN_SURFACE_CLOSURE.json"
    candidate_path = ROOT / "R6_TECTONIC_T0_AUTHORIAL_REALIZATION_CANDIDATES.json"
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    candidate["current_materialization"] = {
        "kind": "VERSIONED_GDH1_OCEAN_SURFACE_CLOSURE",
        "path": closure_file.name,
        "sha256": hashlib.sha256(closure_file.read_bytes()).hexdigest(),
        "parent_field_package_sha256": report["parent"]["field_package_sha256"],
        "field_package_path": report["materialized"]["field_package_path"],
        "field_package_sha256": report["materialized"]["field_package_sha256"],
        "canonical_t0_promoted": False,
    }
    candidate_path.write_text(json.dumps(candidate, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    (ROOT / "R6_T0_B_PANGAEA_LIKE_V2_GDH1_MODEL_CONFIGURATION.json").write_text(
        json.dumps(report["model_configuration"], indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    s = report["statistics"]
    lineage = report["component_lineage"]
    model = report["model_configuration"]
    lines = [
        "# R6 T0 B-v2 ocean thermal-isostatic surface closure", "",
        f"**Decision:** `{report['decision']}`", "",
        f"- Parent package: `{report['parent']['field_package_path']}` SHA256 `{report['parent']['field_package_sha256']}`.",
        f"- New package: `{report['materialized']['field_package_path']}` SHA256 `{report['materialized']['field_package_sha256']}`.",
        f"- Model: `{model['model_id']}` ({model['version']}); {model['citation']}.",
        "- Authority: GDH1 coefficients are a published Earth-analogue physical model configuration; derived thermal component is `SPECIALIST_DERIVED_T0`; authorial residual remains `AUTHORIAL_T0_PRIMITIVE`.",
        "- No Earth observation, Earth bathymetry grid, OrbData output, or canonical geography was imported or changed.", "",
        "## Component lineage", "",
        f"- Age input SHA256: `{lineage['age_field']['sha256_before_after'][0]}` -> `{lineage['age_field']['sha256_before_after'][1]}` (unchanged).",
        f"- Thermal component `{lineage['thermal_component']['name']}` SHA256: `{lineage['thermal_component']['sha256']}`.",
        f"- Authorial residual SHA256: `{lineage['authorial_residual']['sha256_before_after'][0]}` -> `{lineage['authorial_residual']['sha256_before_after'][1]}` (unchanged).",
        f"- Canonical land elevation SHA256: `{lineage['land_component']['sha256_before_after'][0]}` -> `{lineage['land_component']['sha256_before_after'][1]}` (unchanged).",
        f"- Total surface `{lineage['total_surface']['name']}` SHA256: `{lineage['total_surface']['sha256']}`.",
        "- Ocean total is thermal elevation plus the unchanged authorial residual; land total copies the canonical land array exactly.", "",
        "- All unchanged parent field hashes are retained under `component_lineage.unchanged_parent_field_hashes`; only the prior all-ocean unknown mask is replaced with the recomputed unknown-total mask.", "",
        "## GDH1 configuration and model-form uncertainty", "",
        "For age <20 Ma, depth is 2600 + 365√age m. For age ≥20 Ma, depth is 5651 − 2473 exp(−0.0278 age) m. Depth is positive downward; thermal elevation is its negative relative to the existing R6 zero datum.",
        f"At the 20 Ma branch, the young limit is {model['branch_at_20_ma']['young_limit_depth_m']:.6f} m and the old branch is {model['branch_at_20_ma']['old_branch_depth_m']:.6f} m; the specified piecewise law has a {model['branch_at_20_ma']['discontinuity_old_minus_young_m']:.6f} m old-minus-young step. No smoothing was applied.",
        f"Model-form axis: `{report['model_form_uncertainty']['axis']}`; primary `{report['model_form_uncertainty']['primary']}`; future comparator `{report['model_form_uncertainty']['comparator']}`. No ensemble or second candidate world was generated. Reference: [Holdt et al. (2025)](https://doi.org/10.1029/2024JB029890).", "",
        "## Ocean diagnostics", "",
        f"- Governed ocean cells: {s['ocean_cells']}; known elevation cells: {s['known_ocean_elevation_cells']}; unknown: {s['unknown_ocean_elevation_cells']}; coverage: {s['ocean_coverage_fraction']:.9f}.",
        f"- Thermal elevation min/max: {s['thermal_elevation_min_m']:.3f} / {s['thermal_elevation_max_m']:.3f} m.",
        f"- Residual area-weighted mean / RMS / hard cap: {s['residual_area_weighted_mean_m']:.9f} / {s['residual_area_weighted_rms_m']:.6f} / {s['residual_hard_cap_abs_m']:.3f} m.",
        f"- Total ocean elevation min/max: {s['total_ocean_elevation_min_m']:.3f} / {s['total_ocean_elevation_max_m']:.3f} m.",
        f"- Total ocean area-weighted mean / median: {s['total_ocean_area_weighted_mean_m']:.3f} / {s['total_ocean_area_weighted_median_m']:.3f} m.",
        f"- Positive-down final ocean depth min/max: {s['total_ocean_depth_min_m']:.3f} / {s['total_ocean_depth_max_m']:.3f} m.",
        f"- GDH1 depth monotone over 0–160 Ma: {s['age_depth_monotone_0_160_ma']}; ocean cells at/above zero datum: {s['ocean_cells_at_or_above_zero_datum']}.", "",
        "## PRE_ORBDATA", "",
        "**Not ready.** Ocean surface is now complete on governed cell support, but PRE_ORBDATA still requires nodal inputs and closed auxiliary-grid/runtime interfaces.",
        *[f"- {item}" for item in report["pre_orbdata_impact"]["remaining_gates"]], "",
        "Age and residual were not regenerated. OrbData, SHELLS mechanics, forward evolution, `dt`, and `t1` were not run or created.", "",
    ]
    (ROOT / "R6_T0_B_PANGAEA_LIKE_V2_OCEAN_SURFACE_CLOSURE.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"decision": report["decision"], "field_package_sha256": report["materialized"]["field_package_sha256"],
                      "thermal_component_sha256": lineage["thermal_component"]["sha256"],
                      "total_surface_sha256": lineage["total_surface"]["sha256"],
                      "pre_orbdata_ready": report["pre_orbdata_impact"]["PRE_ORBDATA_ready"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
