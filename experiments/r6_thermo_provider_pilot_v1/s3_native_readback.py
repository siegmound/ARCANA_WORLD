"""S3 phase-agnostic, source-chemistry-bound, READ-ONLY Earth output parser.

This is an engineering diagnostic, NOT a scientific calibration, run permission,
S3 numerical acceptance policy, or model equivalence test. No engines are called.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import math
import re
from typing import Any

from experiments.r6_thermo_provider_pilot_v1.s3_design_contract import load


class S3NativeError(ValueError):
    pass


def need(ok: bool, code: str) -> None:
    if not ok:
        raise S3NativeError(code)


def finite(x: Any) -> bool:
    return type(x) in (int, float) and math.isfinite(x)


def source_point(policy: dict, track_id: str, p: int, t: int) -> dict:
    """Identify proposed candidate P/T only; NOT approve its calibration."""
    need(type(p) in (int, float) and type(t) in (int, float)
         and finite(p) and finite(t), "S3_INVALID_PT")
    tracks = [x for x in policy["candidate_tracks"] if x["id"] == track_id]
    need(len(tracks) == 1, "S3_UNKNOWN_PROVIDER_TRACK")
    track = tracks[0]
    need(p in track["P"] and t in track["T"], "S3_PT_NOT_IN_CANDIDATE_GRID")
    return track


def near_setpoint(observed: object, expected: int) -> bool:
    """Only 16 float64 ULP serialization protection; not physical tolerance."""
    return (finite(observed) and finite(expected)
            and abs(observed - expected) <= 16 * math.ulp(float(expected)))


def expected_magemin_native_basis(track: dict) -> dict[str, float]:
    inp = track["fixed_original_oxide_input"]
    d = dict(zip(inp["names"], inp["amounts_wt_percent"], strict=True))
    need("Fe2O3" in d and "FeO" in d and "O" not in d,
         "S3_SOURCE_IRON_COMPONENT_BASIS_INVALID")
    n = d.pop("Fe2O3") / 159.69
    d["FeO"] += 2 * n * 71.85
    d["O"] = n * 16.0
    total = sum(d.values())
    need(total > 0 and all(finite(x) and x >= 0 for x in d.values()),
         "S3_SOURCE_BULK_INVALID")
    return {k: v / total for k, v in d.items()}


def read_magemin_case(case: dict, p_kbar: int, t_c: int,
                      policy: dict | None = None) -> dict:
    """Parse one native MAGEMin case regardless of number/names of phases."""
    policy = load() if policy is None else policy
    track = source_point(policy, "S3A_MAGEMIN_CUSTOM_IG", p_kbar, t_c)
    need(isinstance(case, dict) and case.get("status") == 0
         and case.get("database") == "ig"
         and case.get("dataset") == "tc_ds636",
         "S3_MAGEMIN_NATIVE_STATUS_OR_MODEL_INVALID")
    need(near_setpoint(case.get("P_kbar"), p_kbar)
         and near_setpoint(case.get("T_C"), t_c),
         "S3_MAGEMIN_NATIVE_PT_DRIFT")
    need(finite(case.get("G_system"))
         and finite(case.get("rho_kg_m3")) and case["rho_kg_m3"] > 0
         and type(case.get("iterations")) is int and case["iterations"] >= 0,
         "S3_MAGEMIN_PHYSICAL_FIELDS_INVALID")
    names, fractions = case.get("phases"), case.get("phase_mass_fractions")
    oxides, bulk = case.get("oxides"), case.get("bulk_wt")
    comps = case.get("phase_comp_wt")
    need(isinstance(names, list) and len(names) > 0
         and all(type(n) is str and n.strip() for n in names)
         and len(set(names)) == len(names) and isinstance(fractions, list)
         and len(names) == len(fractions)
         and all(finite(v) and 0 <= v <= 1 for v in fractions)
         and abs(sum(fractions) - 1) <= 1e-8,
         "S3_MAGEMIN_PHASE_MODE_INVALID")
    expected_basis = expected_magemin_native_basis(track)
    need(isinstance(oxides, list) and len(oxides) == len(expected_basis)
         and set(oxides) == set(expected_basis)
         and len(oxides) == len(set(oxides))
         and isinstance(bulk, list) and len(bulk) == len(oxides)
         and all(finite(v) and v >= 0 for v in bulk)
         and abs(sum(bulk) - 1) <= 1e-8,
         "S3_MAGEMIN_NATIVE_OXIDE_BULK_INVALID")
    need(isinstance(comps, list) and len(comps) == len(names)
         and all(isinstance(row, list) and len(row) == len(oxides)
                 and all(finite(v) and v >= -1e-13 for v in row)
                 and abs(sum(row) - 1) <= 1e-8 for row in comps),
         "S3_MAGEMIN_PHASE_COMPONENTS_INVALID")
    calculated = [sum(fractions[i] * comps[i][j]
                      for i in range(len(names))) for j in range(len(oxides))]
    closure = max(abs(a - b) for a, b in zip(calculated, bulk))
    source_closure = max(abs(bulk[j] - expected_basis[oxide])
                         for j, oxide in enumerate(oxides))
    residual = case.get("bulk_res_norm")
    # Original S2 native-chemistry sanity guards, NOT approved S3 calibration limits.
    need(closure <= 1e-10 and source_closure <= 1e-12
         and finite(residual) and 0 <= residual <= 1e-9,
         "S3_MAGEMIN_NATIVE_CHEMISTRY_SANITY_FAIL")
    need(finite(case.get("native_component_weight_closure_abs"))
         and abs(closure - case["native_component_weight_closure_abs"]) < 1e-12
         and finite(case.get("source_native_basis_closure_custom"))
         and abs(source_closure - case["source_native_basis_closure_custom"]) < 1e-12,
         "S3_MAGEMIN_REPORTED_CHEMISTRY_DIAGNOSTIC_DRIFT")
    return {"provider": "MAGEMin_C.jl", "P": p_kbar, "T": t_c,
            "phases": dict(zip(names, fractions, strict=True)),
            "G_system": case["G_system"], "rho_kg_m3": case["rho_kg_m3"],
            "max_native_component_delta": closure,
            "max_source_component_delta": source_closure,
            "bulk_res_norm": residual,
            "status": "SOURCE_NATIVE_READBACK_ONLY__S3_SCIENCE_UNQUALIFIED"}


def decimal_token(token: str) -> Decimal:
    try:
        val = Decimal(token)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise S3NativeError("S3_PERPLEX_INVALID_DECIMAL_TOKEN") from exc
    need(val.is_finite() and val >= 0, "S3_PERPLEX_INVALID_DECIMAL_TOKEN")
    return val


def printed_interval(token: str) -> tuple[Decimal, Decimal]:
    val = decimal_token(token)
    half = Decimal("0.5").scaleb(val.as_tuple().exponent)
    return max(Decimal(0), val - half), val + half


def read_perplex_prn(prn: str, p_bar: int, t_k: int,
                     policy: dict | None = None) -> dict:
    """Read original-format BL691 native PRN with ANY valid named phase set."""
    policy = load() if policy is None else policy
    track = source_point(policy, "S3B_PERPLEX_BL691", p_bar, t_k)
    need(isinstance(prn, str) and prn.count(
        "Phase Compositions (molar  proportions):") == 1
         and prn.count("Phase speciation") >= 1
         and prn.count("Bulk Composition:") == 1
         and prn.count("Other Bulk Properties:") == 1,
         "S3_PERPLEX_MISSING_NATIVE_SECTIONS")
    for label, expected in (("T(K)", t_k), ("P(bar)", p_bar)):
        hits = re.findall(r"(?m)^\s*" + re.escape(label)
                          + r"\s*=\s*([+\-]?[0-9]+(?:\.[0-9]+)?)", prn)
        need(len(hits) == 1 and abs(float(hits[0]) - expected) <= 0.1,
             "S3_PERPLEX_NATIVE_PT_DRIFT")
    body = prn.split("Phase Compositions (molar  proportions):", 1)[1]
    body = body.split("Phase speciation", 1)[0]
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    need(len(lines) >= 2, "S3_PERPLEX_EMPTY_PHASE_TABLE")
    header = re.split(r"\s{2,}", lines[0])
    components = track["fixed_original_molar_input"]["names"]
    need(header[:4] == ["wt %", "vol %", "mol %", "mol"]
         and len(header[4:]) == len(components)
         and set(header[4:]) == set(components)
         and len(set(header[4:])) == len(header[4:]),
         "S3_PERPLEX_NATIVE_COMPONENT_HEADER_MISMATCH")
    cols = header[4:]
    phases: dict[str, dict] = {}
    for line in lines[1:]:
        fields = line.split()
        need(len(fields) == 5 + len(cols), "S3_PERPLEX_NATIVE_PHASE_WIDTH")
        name = fields[0]
        need(name not in phases, "S3_PERPLEX_DUPLICATE_PHASE")
        wt = decimal_token(fields[1])
        mol = decimal_token(fields[4])
        need(wt <= 100, "S3_PERPLEX_WEIGHT_OUT_OF_RANGE")
        comp = dict(zip(cols, fields[5:], strict=True))
        for token in comp.values():
            decimal_token(token)
        phases[name] = {"wt": wt, "mol": mol, "comp": comp,
                        "mol_token": fields[4]}
    need(phases and abs(sum(x["wt"] for x in phases.values())
                        - Decimal(100)) <= Decimal("0.05"),
         "S3_PERPLEX_PHASE_WEIGHTS_NOT_CLOSED")
    bulk = prn.split("Bulk Composition:", 1)[1]
    bulk = bulk.split("Other Bulk Properties:", 1)[0]
    measured: dict[str, str] = {}
    for line in bulk.splitlines():
        fields = line.split()
        if fields and fields[0] in cols:
            need(fields[0] not in measured and len(fields) == 9,
                 "S3_PERPLEX_NATIVE_BULK_ROW_INVALID")
            measured[fields[0]] = fields[1]
    need(set(measured) == set(cols), "S3_PERPLEX_NATIVE_BULK_MISSING")
    oxides = {}
    for component in cols:
        lower, upper = Decimal(0), Decimal(0)
        reconstructed = Decimal(0)
        for phase in phases.values():
            mole_token = phase["mol_token"]
            frac_token = phase["comp"][component]
            n = decimal_token(mole_token)
            frac = decimal_token(frac_token)
            nlo, nhi = printed_interval(mole_token)
            clo, chi = printed_interval(frac_token)
            reconstructed += n * frac
            lower += nlo * clo
            upper += nhi * chi
        mlo, mhi = printed_interval(measured[component])
        need(lower <= mhi and upper >= mlo,
             "S3_PERPLEX_MOLAR_ROUNDING_CLOSURE_FAIL_" + component)
        oxides[component] = {"reconstructed_mol": str(reconstructed),
                             "reported_mol": measured[component]}
    return {"provider": "Perple_X", "P": p_bar, "T": t_k,
            "phases": {name: float(row["wt"]) for name, row in phases.items()},
            "printed_component_coverage": len(oxides),
            "printed_oxide_molar_rounding_audit": oxides,
            "status": "PRINTED_RESOLUTION_READBACK_ONLY__S3_SCIENCE_UNQUALIFIED"}


def classify_phase_sets(a: dict, b: dict) -> dict:
    """A cross-point change is NOT a solver failure; no phase aliases inferred."""
    need(isinstance(a, dict) and isinstance(b, dict)
         and a.get("provider") == b.get("provider")
         and a.get("provider") in ("MAGEMin_C.jl", "Perple_X")
         and isinstance(a.get("phases"), dict)
         and isinstance(b.get("phases"), dict),
         "S3_CROSS_PROVIDER_OR_INVALID_PHASE_COMPARISON")
    left, right = set(a["phases"]), set(b["phases"])
    added, removed = sorted(right - left), sorted(left - right)
    if a.get("P") == b.get("P") and a.get("T") == b.get("T"):
        disposition = ("SAME_PT_PHASE_IDENTITIES_MATCH_NUMERICAL_COMPARISON_PENDING"
                       if not (added or removed)
                       else "SAME_PT_PHASE_DISAGREEMENT_REQUIRES_REVIEW")
    else:
        disposition = "CROSS_PT_PHASE_SET_CHANGE_OBSERVED_NOT_A_FAIL"
    return {"status": disposition, "added": added, "removed": removed,
            "common": sorted(left & right)}
