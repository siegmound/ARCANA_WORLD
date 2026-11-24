"""S3-D6: read native Perple_X properties, independently of seismic validity.

Earth-only observations. No engine, no world-state write, no science promotion.
Native system G/N/V/Cp are totals for the reported assemblage, not per mole.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re

from experiments.r6_thermo_provider_pilot_v1.s3_native_readback import read_perplex_prn

BASE = Path("/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6")
ARCHIVES = {
    "S2": ("R6_THERMO_S2_REPEATABILITY_NEW01",
           "74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604"),
    "AB": ("R6_THERMO_S3_D5_HGP_AB_NEW01",
           "b05ac30520a92755b6fe5131b9c101cd404b00fb9ede9848f51d7ba96daa9fe2"),
    "C": ("R6_THERMO_S3_D5_HGP_C_NEW01",
          "693bd12bc34ecfc41b170295eeab5d4772c57ab004f1f84e211abc370480aeb8"),
}
CASES = {
    "S2_C1": ("S2", "PERPLEX_01/BL691_MEEMUM", "d942bfa0e73e0d0fcb4ca06fe2a074ea7883d4116ca632638f343e2a23f02c90"),
    "A": ("AB", "HGP_UPSTREAM_01", "653bf79e5ae48cef6437a0d204a329f4e841af0c956e0ce959c1ab27fcda74df"),
    "B": ("AB", "HGP_PAPER_ALPHA_01", "757b82f81e08f3d6e8f9c7409ee2cbdf6241d93cd46a3525a29bcb446fce3e66"),
    "C": ("C", "HGP_LOW_ALBITE_01", "653bf79e5ae48cef6437a0d204a329f4e841af0c956e0ce959c1ab27fcda74df"),
}
MOLAR_HEADER = ("N(g)", "G(J)", "S(J/K)", "V(J/bar)", "Cp(J/K)", "Alpha(1/K)",
                "Beta(1/bar)", "Cp/Cv", "Density(kg/m3)")
SEISMIC_HEADER = ("Gruneisen_T", "Ks(bar)", "Mu(bar)", "V0(km/s)", "Vp(km/s)",
                  "Vs(km/s)", "Poisson", "ratio")
MOLAR_KEYS = ("mass_g", "g_J", "s_J_K", "volume_J_bar", "cp_J_K", "alpha_K_inv",
              "beta_bar_inv", "cp_cv", "density_kg_m3")
SEISMIC_KEYS = ("gruneisen", "ks_bar", "mu_bar", "v0_km_s", "vp_km_s", "vs_km_s", "poisson")


class MaterialReadbackError(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise MaterialReadbackError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def number(token):
    if token == "NaN":
        return None
    need(re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?", token)
         is not None, "D6_INVALID_TOKEN:" + token)
    try:
        value = Decimal(token.replace("D", "E").replace("d", "e"))
    except InvalidOperation as exc:
        raise MaterialReadbackError("D6_DECIMAL_INVALID") from exc
    need(value.is_finite(), "D6_NONFINITE")
    return value


def interval(token):
    value = number(token)
    need(value is not None, "D6_INTERVAL_UNKNOWN")
    half = Decimal("0.5").scaleb(value.as_tuple().exponent)
    return value - half, value + half


def section(text, begin, end):
    need(text.count(begin) == 1 and text.count(end) == 1, "D6_SECTION_COUNT")
    tail = text.split(begin, 1)[1]
    need(end in tail, "D6_SECTION_ORDER")
    return tail.split(end, 1)[0]


def table(text, header, keys, expected):
    rows = [x.strip() for x in text.splitlines() if x.strip()]
    need(rows and tuple(rows[0].split()) == header, "D6_HEADER_DRIFT")
    out = {}
    for row in rows[1:]:
        fields = row.split()
        name = " ".join(fields[:-len(keys)])
        need(name in expected and name not in out, "D6_ROW_ID:" + name)
        tokens = fields[-len(keys):]
        for token in tokens:
            number(token)
        out[name] = dict(zip(keys, tokens, strict=True))
    need(set(out) == expected, "D6_ROW_COVERAGE")
    return out


def reading(token, factor="1", status=None):
    value = number(token)
    return {"native_token": token,
            "value_si": None if value is None else str(value * Decimal(factor)),
            "status": "UNKNOWN_NATIVE_NAN" if value is None else
                      (status or "NATIVE_OBSERVATION_UNVALIDATED")}


def ratio_overlap(numerator, denominator, multiplier, reported):
    nl, nh = interval(numerator)
    dl, dh = interval(denominator)
    rl, rh = interval(reported)
    need(nl > 0 and dl > 0, "D6_NONPOSITIVE_RATIO")
    f = Decimal(multiplier)
    return nl / dh * f <= rh and nh / dl * f >= rl


def cp_values(raw):
    result = {}
    for label in ("Heat Capacity (J/K/kg)", "Solid Heat Capacity (J/K/kg)"):
        hits = re.findall(r"(?m)^\s*" + re.escape(label) + r"\s*=\s*(\S+)\s*$", raw)
        need(len(hits) == 1 and number(hits[0]) is not None
             and number(hits[0]) > 0, "D6_CP_BULK_MISSING")
        result[label] = hits[0]
    return result


def warning_phases(stdout):
    estimated = re.findall(r"(?m)^\*\*warning ver178\*\*[^\n]*\n\s*the shear modulus of:\s*(\S+)", stdout)
    need(len(estimated) == len(set(estimated)), "D6_DUPLICATE_SHEAR_WARNING")
    missing_aggregate = bool(re.search(r"(?m)^\*\*warning ver177\*\*", stdout))
    return estimated, missing_aggregate


def parse_properties(prn, stdout, phases):
    """Phase labels are from the already verified phase-agnostic chemistry parser."""
    expected = set(phases) | {"System", "System - Fluid"}
    molar = table(section(prn, "Molar Properties and Density:", "Seismic Properties:"),
                  MOLAR_HEADER, MOLAR_KEYS, expected)
    seismic = table(section(prn, "Seismic Properties:", "Bulk Composition:"),
                    SEISMIC_HEADER, SEISMIC_KEYS, expected)
    cp = cp_values(section(prn, "Other Bulk Properties:", "Chemical Potentials (J/mol):"))
    estimated, missing_aggregate = warning_phases(stdout)
    need(set(estimated) <= set(phases), "D6_WARNING_PHASE_UNBOUND")
    # Preserve every native token. Factors use SI; no invented mixing rule.
    factors = {"mass_g":"0.001", "volume_J_bar":"0.00001", "beta_bar_inv":"0.00001"}
    thermal = {}
    for name, row in molar.items():
        thermal[name] = {}
        for key, token in row.items():
            value = number(token)
            status = None
            if value is not None and key in ("alpha_K_inv", "cp_cv") and value == 0:
                status = "NATIVE_ZERO_UNADJUDICATED"
            if key in ("mass_g","volume_J_bar","cp_J_K","density_kg_m3","beta_bar_inv"):
                need(value is not None and value > 0, "D6_THERMAL_NONPOSITIVE_OR_UNKNOWN:" + name + ":" + key)
            thermal[name][key] = reading(token, factors.get(key,"1"), status)
    elastic = {}
    for name,row in seismic.items():
        elastic[name] = {}
        for key,token in row.items():
            value = number(token)
            status = "NATIVE_OBSERVATION_UNVALIDATED"
            if name in estimated:
                status = "NATIVE_POISSON_FALLBACK_ASSOCIATED_UNVALIDATED"
            elif name in ("System","System - Fluid") and missing_aggregate:
                status = "NATIVE_AGGREGATE_WARNING_UNVALIDATED"
            elif value == 0 and name == "melt(G)" and key in ("mu_bar","vs_km_s"):
                status = "NATIVE_FLUID_ZERO"
            f = "100000" if key.endswith("_bar") else "1000" if key.endswith("_km_s") else "1"
            elastic[name][key] = reading(token,f,status)
    checks = {}
    for name, cp_label in (("System","Heat Capacity (J/K/kg)"),
                           ("System - Fluid","Solid Heat Capacity (J/K/kg)")):
        row = molar[name]
        checks[name] = {
            "density_printed_interval_overlap": ratio_overlap(row["mass_g"],
                row["volume_J_bar"], "100", row["density_kg_m3"]),
            "cp_mass_printed_interval_overlap": ratio_overlap(row["cp_J_K"],
                row["mass_g"], "1000", cp[cp_label]),
        }
        need(checks[name]["density_printed_interval_overlap"],
             "D6_AGGREGATE_DENSITY_IDENTITY_REVIEW:" + name)
        if name == "System":
            need(checks[name]["cp_mass_printed_interval_overlap"],
                 "D6_AGGREGATE_CP_IDENTITY_REVIEW")
            thermal[name]["cp_J_kg_K"] = reading(cp[cp_label])
        else:
            # Pinned upstream olib.f:693-701 uses TOTAL density psys(10)
            # in the solid Cp line; its enthalpy/entropy use psys1(10).
            # Preserve the native token, do not promote it as solid mass Cp.
            vl, vh = interval(row["volume_J_bar"])
            cl, ch = interval(row["cp_J_K"])
            dl, dh = interval(molar["System"]["density_kg_m3"])
            rl, rh = interval(cp[cp_label])
            checks[name]["cp_upstream_total_density_formula_overlap"] = (
                cl / vh * Decimal(100000) / dh <= rh
                and ch / vl * Decimal(100000) / dl >= rl)
            need(checks[name]["cp_upstream_total_density_formula_overlap"],
                 "D6_SOLID_CP_UPSTREAM_FORMULA_REVIEW")
            thermal[name]["cp_J_kg_K"] = reading(
                cp[cp_label], status="NATIVE_SOLID_CP_USES_TOTAL_DENSITY__DO_NOT_EXPORT_AS_SOLID_MASS_CP")
            derived = number(row["cp_J_K"]) / number(row["mass_g"]) * Decimal(1000)
            thermal[name]["cp_mass_normalized_derived_J_kg_K"] = {
                "value_si": str(derived), "status": "DERIVED_FROM_PRINTED_TOTALS_UNVALIDATED",
                "native_token": None, "formula": "1000*solid_cp_J_K/solid_mass_g"}
    return {"thermal_native": thermal, "elastic_native": elastic,
            "printed_identity_checks": checks, "estimated_shear_phases": estimated,
            "aggregate_seismic_warning": missing_aggregate,
            "thermal_science": "UNKNOWN", "elastic_export_authorized": False,
            "world_material_assignment_authorized": False,
            "system_extensive_basis": "REPORTED_ASSEMBLAGE_TOTAL_NOT_MOLAR",
            "cp_basis": "NATIVE_ASSEMBLAGE_CP_NOT_EQUILIBRIUM_PATH_DERIVATIVE",
            "units_note": "value_si uses kg,m3,Pa,1/Pa,m/s; native field key labels retained"}


def verified_members(root, digest):
    raw = (root / "MANIFEST.json").read_bytes()
    need(sha(raw) == digest, "D6_MANIFEST_DRIFT")
    manifest = json.loads(raw)
    files = manifest.get("files_sha256", manifest.get("files"))
    need(isinstance(files,dict) and bool(files), "D6_MEMBER_MAP")
    for rel, info in files.items():
        path = root / rel
        need(path.is_file() and not path.is_symlink()
             and path.resolve().is_relative_to(root.resolve()), "D6_MEMBER_PATH")
        expected = info if isinstance(info,str) else info["sha256"]
        need(sha(path.read_bytes()) == expected, "D6_MEMBER_DRIFT:" + rel)
    return files


def main():
    roots = {}
    members = {}
    for key,(name,digest) in ARCHIVES.items():
        roots[key] = BASE / name
        members[key] = verified_members(roots[key],digest)
    result = {}
    for key,(archive,rel,digest) in CASES.items():
        for filename in ("bl691_MEEMUM.prn","RUN_STDOUT.log"):
            need(rel+"/"+filename in members[archive], "D6_REQUIRED_FILE_UNBOUND")
        path = roots[archive] / rel
        raw = (path/"bl691_MEEMUM.prn").read_bytes()
        need(sha(raw) == digest,"D6_PRN_DRIFT")
        prn = raw.decode("utf-8",errors="strict")
        log = (path/"RUN_STDOUT.log").read_bytes()
        phase = read_perplex_prn(prn,4000,1050)
        result[key] = {"prn_sha256":digest,"stdout_sha256":sha(log),
                       **parse_properties(prn,log.decode("utf-8",errors="strict"),phase["phases"])}
    print(json.dumps({"cases":result,"additional_engine_runs":0,"S3_engine_runs":6,
                      "science":"UNKNOWN","approved_S3_cells":0,
                      "physical_T1":None,"WORLD_HISTORY_PRODUCTION_AUTHORIZED":False},
                     indent=2,allow_nan=False))
    print("S3_D6_NATIVE_MATERIAL_READBACK_PASS")


if __name__ == "__main__":
    main()
