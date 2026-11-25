"""S3-D9: archived equilibrium-path enthalpy secants; diagnostic only."""
from decimal import Decimal
from itertools import product
import json

from experiments.r6_thermo_provider_pilot_v1 import s3_d6_native_material_readback as d6
from experiments.r6_thermo_provider_pilot_v1 import s3_d8_native_layout_readback as d8

D = Decimal


def specific_h(system, temperature):
    """G and S are total native J and J/K, not per mole; mass token in grams."""
    t = D(str(temperature))
    d6.need(t.is_finite() and t > 0, "D9_BAD_T")
    g, s, m = (system[k]["native_token"] for k in ("g_J", "s_J_K", "mass_g"))
    gv, sv, mv = (d6.number(x) for x in (g, s, m))
    d6.need(gv is not None and sv is not None and mv is not None and mv > 0,
            "D9_BAD_NATIVE_TOTALS")
    gi, si, mi = (d6.interval(x) for x in (g, s, m))
    d6.need(mi[0] > 0, "D9_BAD_MASS_INTERVAL")
    values = [(x + t*y) / (z / D(1000)) for x,y,z in product(gi,si,mi)]
    return ((gv + t*sv)/(mv/D(1000)), min(values), max(values))


def secant(lo, hi, t_lo, t_hi):
    dt = D(str(t_hi))-D(str(t_lo))
    d6.need(dt.is_finite() and dt > 0, "D9_BAD_DT")
    return ((hi[0]-lo[0])/dt, (hi[1]-lo[2])/dt, (hi[2]-lo[1])/dt)


def read_pair(root, members, rels, p, t, digest):
    pair = []
    for rel in rels:
        for name in ("bl691_MEEMUM.prn", "RUN_STDOUT.log"):
            d6.need(rel+"/"+name in members, "D9_MEMBER_UNBOUND")
        raw = (root/rel/"bl691_MEEMUM.prn").read_bytes()
        d6.need(d6.sha(raw)==digest, "D9_PRN_DRIFT")
        stdout = (root/rel/"RUN_STDOUT.log").read_text(encoding="utf-8")
        o = d8.read(raw.decode("utf-8", errors="strict"), stdout, p, t)
        sys = o["material"]["thermal_native"]["System"]
        pair.append((sys, o["chemistry"]["phases"]))
    d6.need(len(pair)==2 and pair[0]==pair[1], "D9_REPLICA_DRIFT")
    return pair[0]


def main():
    root=d6.BASE/d8.ARCHIVE
    members=d6.verified_members(root,d8.MANIFEST)
    points={}
    for key,p,t,digest in d8.POINTS:
        points[key]=(p,t,*read_pair(root,members,[f"{key}_{i:02d}" for i in (1,2)],p,t,digest))
    archive,manifest=d6.ARCHIVES["C"]
    root=d6.BASE/archive
    members=d6.verified_members(root,manifest)
    _,rel,digest=d6.CASES["C"]
    d6.need(rel.endswith("_01"), "D9_C_REPLICA_ID")
    points["P4000_T1050"]=(4000,1050,*read_pair(root,members,[rel,rel[:-2]+"02"],4000,1050,digest))
    # Same original HGP C bulk; equality of printed mass is an extra screen, not a chemistry proof.
    masses={d6.number(x[2]["mass_g"]["native_token"]) for x in points.values()}
    d6.need(len(masses)==1 and None not in masses, "D9_PRINTED_MASS_DRIFT")
    h={}
    for key,(p,t,system,phases) in sorted(points.items()):
        h[key]=specific_h(system,t)
        print("POINT",key,json.dumps({"G_J":system["g_J"],"S_J_K":system["s_J_K"],
             "mass":system["mass_g"],"H_J_kg":[str(v) for v in h[key]],
             "Cp_native_J_kg_K":system["cp_J_kg_K"],"phases_wt_pct":phases},sort_keys=True))
    for a,b in ((1000,1050),(1050,1100),(1000,1100)):
        ka,kb=f"P4000_T{a}",f"P4000_T{b}"
        result=secant(h[ka],h[kb],a,b)
        native=(D(points[ka][2]["cp_J_kg_K"]["value_si"])+D(points[kb][2]["cp_J_kg_K"]["value_si"]))/2
        print("PATH_SECANT",a,b,json.dumps({"H_secant_J_kg_K":[str(v) for v in result],
              "endpoint_native_Cp_mean_J_kg_K":str(native),
              "secant_minus_endpoint_mean_J_kg_K":str(result[0]-native),
              "interval_kind":"PRINTED_TOKEN_ROUNDING_ONLY_NOT_SCIENTIFIC_UNCERTAINTY"},sort_keys=True))
    print("D9_ARCHIVE_ENTHALPY_DIAGNOSTIC_COMPLETE")
    print("ADDITIONAL_ENGINE_RUNS=0")
    print("SCIENTIFICALLY_APPROVED_S3_CELLS=0")


if __name__=="__main__":
    main()
