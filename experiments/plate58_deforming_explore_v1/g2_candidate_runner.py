"""Apply an explicit G2 engineering candidate to the 25 SHA-bound PRE columns.

Never selects a material parameter or authorizes an ARCANA mechanical solve.
Requires a fully populated scenario given explicitly by the operator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from experiments.plate58_deforming_explore_v1.full_column import (
    evaluate_full_column, need,
)

STATUS = "PASS_G2_25_COLUMN_ENGINEERING_CANDIDATE__SHELLS_AND_T1_BLOCKED"
COUPLING_STATUS = "PASS_G2_G3_A_SOURCE_INTERFACE_BOUND__PHYSICAL_CLOSURE_OPEN"


def sha(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()


def evaluate_candidate(coupling_dir: Path, candidate_json: Path, output: Path):
    need(not output.exists(), "G2_OUTPUT_ALREADY_EXISTS")
    manifest=json.loads((coupling_dir/"MANIFEST.json").read_text())
    need(manifest["status"]==COUPLING_STATUS and
         manifest["no_solver_run"] and manifest["no_T1"] and
         manifest["no_canonical_promotion"], "G2_COUPLING_AUTHORITY_CHANGED")
    for name,digest in manifest["files"].items():
        need(sha(coupling_dir/name)==digest, "G2_COUPLING_MEMBER_HASH_CHANGED")
    pre=json.loads((coupling_dir/"G2_PRE_BINDING.json").read_text())
    geometry=json.loads((coupling_dir/"GEOMETRY.json").read_text())
    transfer=json.loads((coupling_dir/"G3_A_TRANSFER_CONTRACT.json").read_text())
    source_ids=[int(c["parent_id"]) for c in pre["source_columns"]]
    need(len(source_ids)==25 and len(set(source_ids))==25 and
         set(source_ids)==set(geometry["geometry"]["source_halo_parent_node_ids"]) and
         transfer["actual_interface_tangent"] is None and
         transfer["actual_effective_load"] is None and
         transfer["mechanical_solve_authorized"] is False and
         pre["effective_constitutive_closure"] is None,
         "G2_G3_SOURCE_INTERPOLATION_OR_SOLVE_CHANGED")
    candidate=json.loads(candidate_json.read_text())
    need(candidate.get("authority")=="ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
         "G2_CANDIDATE_AUTHORITY_INVALID")
    results=[{"parent_id":item["parent_id"],
              "calculation":evaluate_full_column(item["source_PRE"],candidate)}
             for item in pre["source_columns"]]
    report={
        "status":STATUS, "schema":"ARCANA_R6_G2_SOURCE_BOUND_CANDIDATE_25_COLUMNS_V1",
        "scope":"CONSTITUTIVE_ENGINEERING_CANDIDATE_ONLY",
        "input_coupling_manifest_sha256":sha(coupling_dir/"MANIFEST.json"),
        "input_pre_sha256":sha(coupling_dir/"G2_PRE_BINDING.json"),
        "input_candidate_sha256":sha(candidate_json),
        "candidate_source_identifier":candidate["source_identifier"],
        "columns":results,"column_count":len(results),
        "shells_lr_coefficients":None,"G3_A_physical_tangent":None,
        "basal_support":None,"mechanical_solve_authorized":False,
        "solver_runs":0,"physical_T1":None}
    output.mkdir(parents=True,exist_ok=False)
    path=output/"G2_CANDIDATE.json"
    path.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
    (output/"MANIFEST.json").write_text(json.dumps({
        "status":STATUS,"files":{"G2_CANDIDATE.json":sha(path)},
        "no_solver_run":True,"no_T1":True,"no_canonical_promotion":True},
        indent=2,sort_keys=True)+"\n")
    return {"status":STATUS, "column_count":len(results),
            "mechanical_solve_authorized":False,"solver_runs":0}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("coupling_dir",type=Path)
    p.add_argument("candidate_json",type=Path)
    p.add_argument("output",type=Path)
    options=p.parse_args()
    print(json.dumps(evaluate_candidate(options.coupling_dir,
             options.candidate_json,options.output),indent=2))


if __name__=="__main__":
    main()
