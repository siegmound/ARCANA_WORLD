"""D8 read-only archive replay. No solver, no edits to D3/D6 or D7 archive.
Single-aggregate branch follows pinned Perple_X olib.f:644-659, 774, 790-791.
"""
from decimal import Decimal
import json
import re

from experiments.r6_thermo_provider_pilot_v1 import s3_d6_native_material_readback as d6
from experiments.r6_thermo_provider_pilot_v1.s3_native_readback import (
    load, source_point, need, decimal_token, printed_interval, read_perplex_prn,
)

ARCHIVE = "R6_THERMO_S3_D7_HGP_PT_CROSS_NEW01"
MANIFEST = "5f029ba0122410a67396dc3fb46975ebd89761fda8ea9b84aa12b26d089611f7"
POINTS = [["P3000_T1050",3000,1050,"ecc37eea1f218607704b51d9afe4deb4a562df457946d27acca18510fde0db27"],["P4000_T1000",4000,1000,"1030060ed5a0a765746d84aac69f896df504e455428018926a592121dbfa8b4e"],["P4000_T1100",4000,1100,"7510cf29f8edc249f7f36de10986db3f3c2e6f67774b4023e6623358ff0707c3"],["P5000_T1050",5000,1050,"9d903e6e9e4185f6c7d59b20e98435dafa4ec52f133bc17e211c2c1726c7cf70"]]

def read_single_chemistry(prn: str, p_bar: int, t_k: int,
                     policy: dict | None = None) -> dict:
    """Read single-aggregate BL691; same D3 printed interval checks."""
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
    need(bulk.split()[0:5] == ["mol","g","wt","%","mol/kg"], "D8_SINGLE_BULK_HEADER")
    measured: dict[str, str] = {}
    for line in bulk.splitlines():
        fields = line.split()
        if fields and fields[0] in cols:
            need(fields[0] not in measured and len(fields) == 5,
                 "S3_PERPLEX_NATIVE_BULK_ROW_INVALID")
            for token in fields[1:]:
                decimal_token(token)
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


def single_material(prn, stdout, phases):
    expected = set(phases) | {"System"}
    molar = d6.table(d6.section(prn,"Molar Properties and Density:","Seismic Properties:"),
                     d6.MOLAR_HEADER,d6.MOLAR_KEYS,expected)
    seismic = d6.table(d6.section(prn,"Seismic Properties:","Bulk Composition:"),
                       d6.SEISMIC_HEADER,d6.SEISMIC_KEYS,expected)
    bulk = d6.section(prn,"Other Bulk Properties:","Chemical Potentials (J/mol):")
    need("Solid Heat Capacity" not in bulk,"D8_UNEXPECTED_SOLID_CP")
    cp = re.findall(r"(?m)^\s*Heat Capacity \(J/K/kg\)\s*=\s*(\S+)\s*$",bulk)
    need(len(cp)==1 and d6.number(cp[0]) is not None and d6.number(cp[0])>0,"D8_CP")
    thermal = {}
    factors = {"mass_g":"0.001","volume_J_bar":"0.00001","beta_bar_inv":"0.00001"}
    for name,row in molar.items():
        thermal[name] = {}
        for k,t in row.items():
            val = d6.number(t)
            if k in ("mass_g","volume_J_bar","cp_J_K","density_kg_m3","beta_bar_inv"):
                need(val is not None and val>0,"D8_NONPOSITIVE:"+name+":"+k)
            status = "NATIVE_ZERO_UNADJUDICATED" if k in ("alpha_K_inv","cp_cv") and val==0 else None
            thermal[name][k]=d6.reading(t,factors.get(k,"1"),status)
    row=molar["System"]
    checks = {"density_printed_interval_overlap":d6.ratio_overlap(row["mass_g"],row["volume_J_bar"],"100",row["density_kg_m3"]),
              "cp_mass_printed_interval_overlap":d6.ratio_overlap(row["cp_J_K"],row["mass_g"],"1000",cp[0])}
    need(all(checks.values()),"D8_AGGREGATE_IDENTITY_REVIEW")
    thermal["System"]["cp_J_kg_K"]=d6.reading(cp[0])
    estimated,missing=d6.warning_phases(stdout)
    need(set(estimated)<=set(phases),"D8_WARNING_PHASE_UNBOUND")
    elastic={}
    for name,row in seismic.items():
        elastic[name]={}
        for k,t in row.items():
            f="100000" if k.endswith("_bar") else "1000" if k.endswith("_km_s") else "1"
            elastic[name][k]=d6.reading(t,f,"NATIVE_ELASTIC_OBSERVATION_UNVALIDATED")
    return {"thermal_native":thermal,"elastic_native":elastic,
            "printed_identity_checks":{"System":checks},
            "estimated_shear_phases":estimated,"aggregate_seismic_warning":missing,
            "solid_separate_aggregate":"NOT_REPORTED","thermal_science":"UNKNOWN",
            "elastic_export_authorized":False,"world_material_assignment_authorized":False,
            "cp_basis":"NATIVE_ASSEMBLAGE_CP_NOT_EQUILIBRIUM_PATH_DERIVATIVE"}


def read(prn, stdout, p, t):
    bulk=d6.section(prn,"Bulk Composition:","Other Bulk Properties:")
    if bulk.split()[:5]==["mol","g","wt","%","mol/kg"]:
        chemistry=read_single_chemistry(prn,p,t)
        material=single_material(prn,stdout,chemistry["phases"])
        layout="SINGLE_AGGREGATE"
    else:
        chemistry=read_perplex_prn(prn,p,t)
        material=d6.parse_properties(prn,stdout,chemistry["phases"])
        layout="DUAL_AGGREGATE"
    # A finite aggregate is not independently measured when phase elastic data
    # use fallback; ver049 may suppress later warnings.
    suppressed=bool(re.search(r"\*\*warning ver049\*\* warning 178",stdout))
    estimated=material["estimated_shear_phases"]
    material["shear_warning_suppressed"]=suppressed
    material["aggregate_elastic_validity"]="UNKNOWN"
    for name in ("System","System - Fluid"):
        for value in material["elastic_native"].get(name,{}).values():
            if value["value_si"] is not None and (estimated or suppressed):
                value["status"]="NATIVE_AGGREGATE_WITH_FALLBACK_OR_SUPPRESSION_UNVALIDATED"
    return {"layout":layout,"chemistry":chemistry,"material":material}


def main():
    root=d6.BASE/ARCHIVE
    members=d6.verified_members(root,MANIFEST)
    result={}
    for key,p,t,digest in POINTS:
        pair=[]
        for i in (1,2):
            prefix=f"{key}_{i:02d}/"
            need(all(prefix+x in members for x in ("bl691_MEEMUM.prn","RUN_STDOUT.log","LAUNCH.json")),"D8_MEMBER_UNBOUND")
            work=root/prefix
            raw=(work/"bl691_MEEMUM.prn").read_bytes()
            need(d6.sha(raw)==digest,"D8_PRN_DRIFT")
            tele=json.loads((work/"LAUNCH.json").read_bytes())
            need(tele["exit_code"]==0 and not tele["timeout"],"D8_ENGINE_STATUS")
            prn=raw.decode("utf-8",errors="strict")
            stdout=(work/"RUN_STDOUT.log").read_text(encoding="utf-8")
            try:
                obs=read(prn,stdout,p,t)
            except ValueError as exc:
                print("D8_NATIVE_REVIEW",key,i,str(exc))
                print(prn)
                raise
            pair.append(obs)
        need(pair[0]==pair[1],"D8_REPLICA_READBACK_DRIFT")
        o=pair[0]
        result[key]=o
        print("POINT",key,"LAYOUT",o["layout"],"PRN_SHA256",digest)
        print("PHASES_WT_PCT",json.dumps(o["chemistry"]["phases"],sort_keys=True))
        print("COMPONENT_COVERAGE",o["chemistry"]["printed_component_coverage"])
        m=o["material"]; s=m["thermal_native"]["System"]
        print("SYSTEM",json.dumps({k:s[k] for k in ("mass_g","density_kg_m3","cp_J_kg_K","alpha_K_inv","beta_bar_inv","g_J")},sort_keys=True))
        print("CHECKS",json.dumps(m["printed_identity_checks"],sort_keys=True))
        print("SHEAR",m["elastic_native"]["System"]["mu_bar"],"SUPPRESSED",m["shear_warning_suppressed"])
    print("D8_ARCHIVE_READBACK_PASS")
    print("ADDITIONAL_ENGINE_RUNS=0")
    print("S3_ENGINE_RUNS=14")
    print("SCIENTIFICALLY_APPROVED_S3_CELLS=0")


if __name__=="__main__":
    main()
