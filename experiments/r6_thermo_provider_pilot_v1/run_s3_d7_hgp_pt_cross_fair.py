"""D7 bounded four-neighbour BL691 cross, fixed HGP C chemistry; EXPLORE only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from experiments.r6_thermo_provider_pilot_v1 import s3_d5_hgp_prepare as prep
from experiments.r6_thermo_provider_pilot_v1 import run_s3_d5_hgp_fair as h
from experiments.r6_thermo_provider_pilot_v1 import s3_d6_native_material_readback as d6
from experiments.r6_thermo_provider_pilot_v1.s3_native_readback import read_perplex_prn
from experiments.r6_thermo_provider_pilot_v1.pilot import blob
from experiments.r6_thermo_provider_pilot_v1.run_s2_fair import git, write_json

POINTS = ((4000,1000),(4000,1100),(3000,1050),(5000,1050))
LIMITS = {"address_space_limit_bytes":4*1024**3,
          "file_size_limit_bytes":16*1024**2,
          "retained_bytes_stop_threshold":64*1024**2,"walltime_s":150}
RECEIPT_BLOB = "d388b20a3e50e2a4589941893a1557f11b6d17f6"
PINS = {"s3_d6_native_material_readback.py":"7e31b55ed62a91609df9fd5c48db6992adc0ccd3",
        "s3_native_readback.py":"fedea50ff65f16609fcf3c3eabd62ec71fb06554",
        "run_s3_d5_hgp_fair.py":"5e58071db354664563645e10508045f553dc3e70",
        "s3_d6_fair_readback_receipt_v1.json":RECEIPT_BLOB}


def need(ok, code):
    if not ok:
        raise prep.HGPError(code)


def point_stdin(raw, p, t):
    need(type(p) is int and type(t) is int and (p,t) in POINTS, "D7_POINT_OUTSIDE_CROSS")
    pattern = rb"(?m)^1050([ \t]+)4000(\r?)$"
    hits = list(re.finditer(pattern,raw))
    need(len(hits)==1, "D7_ANCHOR_STDIN_DRIFT")
    m = hits[0]
    return raw[:m.start()] + str(t).encode() + m[1] + str(p).encode() + m[2] + raw[m.end():]


def observe(raw, log, p, t):
    prn = raw.decode("utf-8",errors="strict")
    stdout = log.decode("utf-8",errors="strict")
    # Admission and P/T are required even if a changed table format needs review.
    need("Summary of included solution models:" in stdout, "D7_MODEL_SUMMARY_MISSING")
    models = stdout.split("Summary of included solution models:",1)[1].split("---",1)[0]
    need("lAb(HGP)" in models.split() and "Fsp(HGP)" in models.split(), "D7_HGP_ADMISSION")
    for label, expected in (("P(bar)",p),("T(K)",t)):
        values = re.findall(r"(?m)^\s*"+re.escape(label)+r"\s*=\s*([0-9.]+)",prn)
        need(len(values)==1 and abs(float(values[0])-expected)<=.1,"D7_NATIVE_PT_DRIFT")
    result = {"prn_sha256":prep.sha(raw),"P_bar":p,"T_K":t,
              "warnings":re.findall(r"\*\*warning ver\d+\*\*[^\n]*",stdout),
              "chemistry":None,"material":None,"readback_review":[],
              "science":"UNKNOWN"}
    try:
        result["chemistry"] = read_perplex_prn(prn,p,t)
    except ValueError as exc:
        result["readback_review"].append("D3: "+str(exc))
    if result["chemistry"] is not None:
        try:
            result["material"] = d6.parse_properties(prn,stdout,result["chemistry"]["phases"])
        except ValueError as exc:
            result["readback_review"].append("D6: "+str(exc))
    # Keep native table snippets on any readback review, not invented values.
    if result["readback_review"]:
        result["native_review_excerpt"] = prn
    return result


def repeat(a,b):
    return {"raw_bytes_identical":a["prn_sha256"]==b["prn_sha256"],
            "readbacks_both_complete":not a["readback_review"] and not b["readback_review"],
            "science":"UNKNOWN","numeric_acceptance":"NOT_RATIFIED"}


def run(evidence_id):
    need(re.fullmatch(r"R6_THERMO_S3_D7_HGP_PT_CROSS_NEW[0-9]{2,}",evidence_id)
         is not None,"D7_EVIDENCE_ID")
    root = Path.cwd()
    head = git(root,"rev-parse","HEAD")
    need(not git(root,"status","--porcelain"),"D7_DIRTY")
    for name,digest in PINS.items():
        need(blob((prep.HERE/name).read_bytes())==digest,"D7_SOURCE_DRIFT:"+name)
    receipt = h.read_receipt()
    current = prep.preflight()
    h.check_preparation(current,receipt)
    need(current["source_sha"]==head,"D7_HEAD_DRIFT")
    original,ref,runtime = prep.verify_runtime_and_inputs()
    need(runtime==current["runtime"] and ref==current["reference"],"D7_RUNTIME_DRIFT")
    # Reuse authenticated C inputs and anchor without executing anchor again.
    cname,cdigest = d6.ARCHIVES["C"]
    croot = d6.BASE/cname
    cmembers = d6.verified_members(croot,cdigest)
    c = prep.prepare_inputs(original,"HGP_LOW_ALBITE")
    need({k:prep.sha(v) for k,v in c.items()}==receipt["cases"]["HGP_LOW_ALBITE"],"D7_C_INPUT_DRIFT")
    for name,raw in c.items():
        rel = "HGP_LOW_ALBITE_01/"+name
        need(rel in cmembers and (croot/rel).read_bytes()==raw,"D7_C_MEMBER_DRIFT")
    anchor_rel = "HGP_LOW_ALBITE_01/bl691_MEEMUM.prn"
    need(anchor_rel in cmembers and prep.file_sha(croot/anchor_rel)==d6.CASES["C"][2],"D7_ANCHOR_DRIFT")
    need(current["resources"]["disk_free_bytes"]>=LIMITS["retained_bytes_stop_threshold"],"D7_DISK")
    out = prep.EVIDENCE/evidence_id
    out.mkdir(exist_ok=False)
    attempted = 0
    try:
        write_json(out/"PROVENANCE.json",{"source_sha":head,"scope":"EARTH_BL691_EXPLORE_ONLY",
                   "D_025":"operator-declared sub-100GB user workspace policy",
                   "limits":LIMITS,"points":[list(x) for x in POINTS],"replicas_per_point":2,
                   "C_manifest_sha256":cdigest,"D6_receipt_git_blob":RECEIPT_BLOB,
                   "runtime":runtime,"allocation_independently_verified":False})
        results = {}
        for p,t in POINTS:
            key = f"P{p}_T{t}"
            observations = []
            for i in (1,2):
                work = out/f"{key}_{i:02d}"
                work.mkdir()
                inputs = dict(c)
                inputs["bl691_MEEMUM_input.txt"] = point_stdin(c["bl691_MEEMUM_input.txt"],p,t)
                for name,raw in inputs.items():
                    with (work/name).open("xb") as f:
                        f.write(raw)
                write_json(work/"INPUT_SHA256.json",{k:prep.sha(v) for k,v in inputs.items()})
                need(h.retained_bytes(out)<LIMITS["retained_bytes_stop_threshold"],"D7_RETAINED_STOP")
                need(prep.file_sha(runtime["binary"])==runtime["binary_sha256"],"D7_BINARY_DRIFT")
                attempted += 1
                telemetry = h.launch(Path(runtime["binary"]),work,LIMITS)
                prn = work/"bl691_MEEMUM.prn"
                need(prn.is_file() and not prn.is_symlink(),"D7_PRN_MISSING")
                obs = observe(prn.read_bytes(),(work/"RUN_STDOUT.log").read_bytes(),p,t)
                write_json(work/"READBACK.json",obs)
                observations.append({"observation":obs,"telemetry":telemetry})
                need(h.retained_bytes(out)<LIMITS["retained_bytes_stop_threshold"],"D7_RETAINED_STOP")
            a,b = (x["observation"] for x in observations)
            results[key] = {"replicas":observations,"repeatability":repeat(a,b)}
        review = any(not x["repeatability"]["raw_bytes_identical"] or
                     not x["repeatability"]["readbacks_both_complete"] for x in results.values())
        write_json(out/"RESULT.json",{"points":results,"review_required":review,
                  "science":"UNKNOWN","numeric_acceptance":"NOT_RATIFIED",
                  "scientifically_approved_S3_cells":0,"prior_S3_engine_runs":6,
                  "new_launch_attempts":attempted,"physical_T1":None,
                  "WORLD_HISTORY_PRODUCTION_AUTHORIZED":False})
        state = "D7_PT_CROSS_CAPTURED_REVIEW_REQUIRED" if review else "D7_PT_CROSS_DIAGNOSTIC_COMPLETE"
        h.seal(out,state,head,attempted)
        print(state)
    except BaseException as exc:
        if not (out/"MANIFEST.json").exists():
            write_json(out/"FAILURE.json",{"type":type(exc).__name__,"message":str(exc),
                                         "launch_attempts":attempted})
            h.seal(out,"D7_ATTEMPT_FAILED_PRESERVE",head,attempted)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-id",required=True)
    args = parser.parse_args()
    run(args.evidence_id)


if __name__=="__main__":
    main()
