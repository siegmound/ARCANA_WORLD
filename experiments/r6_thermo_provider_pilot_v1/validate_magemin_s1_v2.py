"""Independent report gate for revised MAGEMin S1 Earth-only numeric fixture.

This validates emitted evidence, not physical truth or chemical oxide closure.
The illustrative CUSTOM_IG README numeric mismatch is explicitly unresolved.
"""
from __future__ import annotations

import argparse
import math
import tomllib
from pathlib import Path

from experiments.r6_thermo_provider_pilot_v1.pilot import (
    load_magemin_toml,
)

G_KLB1_REFERENCE = -797.7873865220898
CP_KLB1_REFERENCE = 1208.466551730128


class S1ValidationError(ValueError):
    pass


def need(condition: bool, code: str) -> None:
    if not condition:
        raise S1ValidationError(code)


def finite(x: object) -> bool:
    return type(x) in (int, float) and math.isfinite(x)


def check_document(report: dict) -> dict:
    need(report.get("scope") == "EARTH_OFFICIAL_FIXTURE_ONLY_NOT_ARCANA"
         and report.get("cross_provider_comparable") is False
         and report.get("physical_T1_is_null") is True
         and report.get("reference_test_scope") == "S1_STANDALONE_NUMERICAL",
         "S1_AUTHORITY_MISMATCH")
    f = report.get("fixtures", {})
    need(set(f) == {"MAGEMIN_PREDEFINED_KLB1", "MAGEMIN_CUSTOM_IG"},
         "S1_FIXTURE_SET_INVALID")
    for case in f.values():
        need(case.get("database_label") == "ig" and finite(case.get("G_system")),
             "S1_DATABASE_OR_G_INVALID")
        fractions = case.get("phase_molar_fractions")
        need(isinstance(fractions, list)
             and len(fractions) == len(case.get("phases", []))
             and all(finite(x) and 0 <= x <= 1 for x in fractions)
             and abs(sum(fractions) - 1) < 1e-6,
             "S1_MOLAR_FRACTIONS_INVALID")
        mass = case.get("phase_mass_fractions", [])
        need(all(finite(x) and 0 <= x <= 1 for x in mass)
             and abs(sum(mass) - 1) < 1e-6,
             "S1_MASS_FRACTIONS_INVALID")
    klb = f["MAGEMIN_PREDEFINED_KLB1"]
    need(set(klb["phases"]) == {"ol", "spl", "cpx", "opx"},
         "S1_KLB1_ASSEMBLAGE_CHANGED")
    need(abs(klb["G_system"] - G_KLB1_REFERENCE) < 1e-3
         and finite(klb.get("KLB1_G_reference_abs_delta"))
         and math.isclose(klb["KLB1_G_reference_abs_delta"],
                          abs(klb["G_system"] - G_KLB1_REFERENCE),
                          rel_tol=0, abs_tol=1e-12),
         "S1_KLB1_G_REFERENCE_MISMATCH")
    need(finite(klb.get("KLB1_cp_reference_abs_delta"))
         and klb["KLB1_cp_reference_abs_delta"] < 2.0,
         "S1_KLB1_CP_REFERENCE_MISMATCH")
    cust = f["MAGEMIN_CUSTOM_IG"]
    need(set(cust["phases"]) == {"liq", "cpx", "opx"},
         "S1_CUSTOM_ASSEMBLAGE_CHANGED")
    need(cust.get("input_sum_as_reported_wt_percent") == 99.75,
         "S1_CUSTOM_COMPOSITION_CHANGED")
    need(cust.get("readme_quantitative_reconciliation") == "PENDING",
         "S1_README_DISCREPANCY_CONCEALED")
    for key in ("frac_M_wt", "frac_S_wt", "rho_M", "rho_S", "density_closure_abs"):
        need(finite(cust.get(key)), "S1_CUSTOM_MISSING_" + key)
    fm, fs = cust["frac_M_wt"], cust["frac_S_wt"]
    rm, rs = cust["rho_M"], cust["rho_S"]
    need(0 < fm < 1 and 0 < fs < 1 and rm > 0 and rs > 0
         and abs(fm + fs - 1) < 1e-6,
         "S1_CUSTOM_SOLID_MELT_INVALID")
    delta = abs(cust["rho_kg_m3"] - 1.0 / (fm / rm + fs / rs))
    need(delta < 1e-10 and cust["density_closure_abs"] < 1e-10
         and abs(delta - cust["density_closure_abs"]) < 1e-10,
         "S1_CUSTOM_DENSITY_CLOSURE_INVALID")
    return {
        "status": "MAGEMIN_S1_NUMERICAL_REPORT_CHECK_PASS",
        "cross_provider_equivalence": False,
        "readme_quantitative_reconciliation": "PENDING",
        "physical_T1": None,
    }


def check_file(path: Path) -> dict:
    # Retains original registry-based P/T, mass and provider checks.
    return check_document(load_magemin_toml(path))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    result = check_file(args.report)
    import json
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
