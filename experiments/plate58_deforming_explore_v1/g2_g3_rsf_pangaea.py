"""R6 noncanonical lab analogue: one/two-state Dieterich rate-and-state friction.

PANGAEA 921284 (Ikari & Kopf, 2020): Earth fault-gouge inverse MODEL FITS,
NOT original sensor stresses and NOT T0 ARCANA material assignments.
Only friction/stress DIFFERENCES are returned: mu_ref is not in Table 2.
No source interface traction vector, solver, fault mapping, T1 or HistoryStore.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

DOI = "10.1594/PANGAEA.921284"
SCHEMA = "ARCANA_R6_G2_G3_PANGAEA921284_RSF_LAB_ANALOGUE_V1"
AUTHORITY = "EARTH_LAB_INVERSE_MODEL_ANALOGUE_NOT_ARCANA_T0"
# Explicit 0-based positions in the PANGAEA Table 2 catalog (19 columns).
INDEX = {"event":0,"sample":3,"experiment":4,"v0":6,"v1":7,
         "a":8,"b1":9,"dc1":10,"b2":11,"dc2":12,"a_minus_b":13}


class RSFSourceError(ValueError):
    pass


def need(ok, message):
    if not ok:
        raise RSFSourceError(message)


def number(value, label, positive=False):
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise RSFSourceError("RSF_MISSING_OR_INVALID_"+label) from exc
    need(math.isfinite(x) and (not positive or x>0),
         "RSF_MISSING_OR_INVALID_"+label)
    return x


def ingest_pangaea_table2(data: bytes) -> dict:
    """Import official PANGAEA tab text, retaining exact file SHA and row IDs.

    Fail closed if export columns drift. Missing b2 and Dc2 means a true
    *single*-state published fit only when BOTH values are blank.
    """
    need(isinstance(data,bytes) and bool(data), "RSF_EMPTY_SOURCE_FILE")
    raw_sha=hashlib.sha256(data).hexdigest()
    try:
        text=data.decode("utf-8-sig")
    except UnicodeError as exc:
        raise RSFSourceError("RSF_SOURCE_ENCODING_UTF8_REQUIRED") from exc
    lines=text.splitlines()
    need(lines and lines[0].startswith("/* DATA DESCRIPTION:"),
         "RSF_PANGAEA_METADATA_HEADER_REQUIRED")
    end=next((i for i,line in enumerate(lines) if line.strip()=="*/"),None)
    need(end is not None and end+2<=len(lines),
         "RSF_PANGAEA_METADATA_TERMINATOR_MISSING")
    metadata="\n".join(lines[:end+1])
    need("921284" in metadata and
         "Ikari" in metadata and "Kopf" in metadata,
         "RSF_PANGAEA_TABLE2_IDENTITY_NOT_VERIFIED")
    reader=csv.reader(io.StringIO("\n".join(lines[end+1:])),delimiter="\t")
    header=next(reader,None)
    need(header is not None and len(header)==19 and
         "event" in header[0].lower() and
         "exp" in header[4].lower() and
         "v" in header[6].lower() and
         "v" in header[7].lower() and
         header[8].strip().lower().endswith("(a)") and
         header[9].strip().lower().endswith("(b1)") and
         header[10].strip().lower().endswith("(dc1)") and
         header[11].strip().lower().endswith("(b2)") and
         header[12].strip().lower().endswith("(dc2)") and
         "a-b" in header[13].lower(),
         "RSF_PANGAEA_TABLE2_HEADER_COLUMNS_CHANGED")
    records=[]
    for row_no,row in enumerate(reader,start=end+3):
        if not row or not any(v.strip() for v in row):
            continue
        need(len(row)==19,"RSF_PANGAEA_ROW_COLUMN_COUNT_CHANGED")
        event,sample,experiment=(row[INDEX[k]].strip() for k in
                                  ("event","sample","experiment"))
        need(event and sample and experiment,
             "RSF_PANGAEA_SAMPLE_EXPERIMENT_ID_REQUIRED")
        v0=number(row[INDEX["v0"]],"V0_UM_S",positive=True)
        v1=number(row[INDEX["v1"]],"V1_UM_S",positive=True)
        a=number(row[INDEX["a"]],"A")
        b1=number(row[INDEX["b1"]],"B1")
        dc1=number(row[INDEX["dc1"]],"DC1_UM",positive=True)
        b2raw=row[INDEX["b2"]].strip()
        dc2raw=row[INDEX["dc2"]].strip()
        need(bool(b2raw)==bool(dc2raw),
             "RSF_SECOND_STATE_B_AND_DC_MUST_BE_PAIRED")
        b2=number(b2raw,"B2") if b2raw else None
        dc2=number(dc2raw,"DC2_UM",positive=True) if dc2raw else None
        reported=number(row[INDEX["a_minus_b"]],"PUBLISHED_A_MINUS_B")
        derived=a-b1-(b2 if b2 is not None else 0.)
        # Published tab values are rounded, so allow a modest precision tolerance.
        need(math.isclose(reported,derived,rel_tol=0,abs_tol=6e-4),
             "RSF_PUBLISHED_A_MINUS_B_MISMATCH")
        need(all(abs(v)<1. for v in (a,b1,derived)) and
             (b2 is None or abs(b2)<1.),
             "RSF_NONPHYSICAL_FRICTION_PARAMETER_SCALE")
        records.append({"source_line":row_no,"event":event,
            "sample_label":sample,"experiment":experiment,
            "v0_m_s":v0*1e-6,"v1_m_s":v1*1e-6,
            "a":a,"states":[{"b":b1,"Dc_m":dc1*1e-6}]+(
              [{"b":b2,"Dc_m":dc2*1e-6}] if b2 is not None else []),
            "published_a_minus_b":reported,
            "model_extracted_not_raw_observation":True})
    need(bool(records),"RSF_NO_SOURCE_MODEL_ROWS")
    return {"schema":SCHEMA,"authority":AUTHORITY,"doi":DOI,
       "source_sha256":raw_sha,"raw_file_bytes":len(data),
       "fitted_model_rows":records,"model_extracted_not_instrument_raw":True,
       "lab_temperature_k":293.15,"lab_effective_normal_stress_pa":1e7,
       "brine_nacl_mass_percent":3.5,
       "arcana_lithology_bound":False,"arcana_fault_bound":False,
       "physical_T1":None,"mechanical_solve_authorized":False}


def steady_reference_states(row: dict):
    v0=number(row["v0_m_s"],"V0",positive=True)
    states=row["states"]
    need(1<=len(states)<=2,"RSF_ONE_OR_TWO_STATES_REQUIRED")
    return [number(s["Dc_m"],"DC",positive=True)/v0 for s in states]


def advance_aging_states(row: dict, theta: list[float], velocity_m_s: float,
                         dt_s: float) -> list[float]:
    """Exact constant-speed aging-law step: dtheta/dt = 1 - V*theta/Dc."""
    v=number(velocity_m_s,"VELOCITY",positive=True)
    dt=number(dt_s,"DT")
    need(dt>=0 and len(theta)==len(row["states"]),
         "RSF_AGE_STEP_INVALID")
    output=[]
    for state,theta0 in zip(row["states"],theta,strict=True):
        d=number(state["Dc_m"],"DC",positive=True)
        th=number(theta0,"THETA",positive=True)
        exponent=-v*dt/d
        at_steady=d/v
        next_theta=at_steady+(th-at_steady)*math.exp(exponent)
        need(math.isfinite(next_theta) and next_theta>0,
             "RSF_AGE_NUMERIC_INVALID")
        output.append(next_theta)
    return output


def relative_friction_response(row: dict, velocity_m_s: float,
                               theta: list[float], *,
                               effective_normal_pa: float=1e7) -> dict:
    """Return delta(mu), delta(tau) w.r.t. v0 steady. Never absolute traction.

    Only allow the two explicitly model-fit velocity endpoints and their
    inclusive interval; off-range prediction requires separate scientific
    acceptance and is rejected even though the equation is mathematically valid.
    """
    v=number(velocity_m_s,"V",positive=True)
    v0=number(row["v0_m_s"],"V0",positive=True)
    v1=number(row["v1_m_s"],"V1",positive=True)
    sigma=number(effective_normal_pa,"EFFECTIVE_NORMAL",positive=True)
    need(math.isclose(sigma,1e7,rel_tol=0,abs_tol=1e-6),
         "RSF_PRESSURE_OUTSIDE_PUBLISHED_LAB_SUPPORT")
    need(min(v0,v1)*(1-1e-12)<=v<=max(v0,v1)*(1+1e-12),
         "RSF_VELOCITY_OUTSIDE_SOURCE_STEP_SUPPORT")
    states=row["states"]
    need(1<=len(states)<=2 and len(theta)==len(states),
         "RSF_STATES_INCOMPLETE")
    a=number(row["a"],"A")
    delta_mu=a*math.log(v/v0)
    bsum=0.
    for s,t in zip(states,theta,strict=True):
        b=number(s["b"],"B")
        dc=number(s["Dc_m"],"DC",positive=True)
        th=number(t,"THETA",positive=True)
        delta_mu+=b*math.log(th*v0/dc)
        bsum+=b
    ss=(a-bsum)*math.log(v/v0)
    need(math.isfinite(delta_mu) and math.isfinite(ss),
         "RSF_RELATIVE_STRESS_NUMERIC_INVALID")
    return {"delta_mu":delta_mu,"delta_tau_pa":sigma*delta_mu,
        "steady_delta_mu":ss,"steady_delta_tau_pa":sigma*ss,
        "direct_effect_a":a,"state_effect_b_total":bsum,
        "source_lab_only":True,"absolute_mu_known":False,
        "absolute_shear_traction_pa":None,"fault_normal_direction":None,
        "fault_slip_direction":None,"arcana_fault_element_authorized":False,
        "mechanical_solve_authorized":False,"physical_T1":None}


def read_source(path):
    return ingest_pangaea_table2(Path(path).read_bytes())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True,
                        help="Official UTF-8 tab-separated PANGAEA 921284 export")
    parser.add_argument("--output",type=Path,required=True,
                        help="NEW immutable noncanonical evidence directory")
    args=parser.parse_args()
    need(not args.output.exists(),"RSF_OUTPUT_EXISTS_NO_OVERWRITE")
    source_sha=hashlib.sha256(args.source.read_bytes()).hexdigest()
    report=read_source(args.source)
    need(report["source_sha256"]==source_sha,
         "RSF_SOURCE_CHANGED_DURING_READ")
    # Do not repackage source, and never emit an inferred absolute traction.
    args.output.mkdir(parents=True,exist_ok=False)
    rp=args.output/"REPORT.json"
    rp.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    (args.output/"MANIFEST.json").write_text(json.dumps({
      "schema":"ARCANA_R6_G2_G3_LAB_RSF_EVIDENCE_MANIFEST_V1",
      "status":"SOURCE_INGESTED__EARTH_ANALOGUE_ONLY_NOT_T0",
      "source_doi":DOI,
      "source_sha256":source_sha,
      "files":{"REPORT.json":hashlib.sha256(rp.read_bytes()).hexdigest()},
      "no_physical_solve":True,"no_T1":True,
      "no_canonical_promotion":True
    },indent=2)+"\n")
    print(json.dumps({"status":"SOURCE_INGESTED__EARTH_ANALOGUE_ONLY_NOT_T0",
       "model_fit_rows":len(report["fitted_model_rows"]),
       "source_sha256":source_sha,"mechanical_solve_authorized":False,
       "physical_T1":None},indent=2))


if __name__=="__main__":
    main()
