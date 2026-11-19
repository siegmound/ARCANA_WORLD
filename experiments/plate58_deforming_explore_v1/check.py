"""Read-only validation of the isolated plate 5:8 staging packet."""
import argparse
import json
from pathlib import Path

from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
from experiments.plate58_deforming_explore_v1.prepare import (
    STATUS, interface_edges, readiness_gate, require, sha,
)


def verify(folder):
    manifest = json.loads((folder/"MANIFEST.json").read_text())
    case = json.loads((folder/"CASE.json").read_text())
    require(manifest["status"] == case["status"] == STATUS, "STAGE_STATUS_INVALID")
    require(manifest["no_solver_run"] and manifest["no_T1"] and
            manifest["no_canonical_promotion"], "STAGE_AUTHORITY_INVALID")
    for name, expected in manifest["files"].items():
        require((folder/name).is_file() and sha(folder/name) == expected,
                "STAGE_FILE_SHA_INVALID:" + name)
    model = parse_feg((folder/"regional.feg").read_text(), mode="SHELLS_READY")
    require(len(model.nodes) == 9 and len(model.elements) == 8 and not model.faults,
            "FEG_REGION_INCOMPATIBLE")
    require({n for edge in interface_edges(
        model.elements, [case["plate_by_parent_triangle"][str(pid)]
                         for pid in case["parent_triangle_ids"]])
             for n in edge} ==
            {n for edge in case["local_contact_edges"] for n in edge},
            "CONTACT_TOPOLOGY_CHANGED")
    require(len(case["prescribed_distal_node_velocity"]) == 6, "DISTAL_BC_MISSING")
    require(len(case["parent_node_PRE"]) == 9, "PRE_REGION_INCOMPLETE")
    require(case["readiness"] == readiness_gate(case) and
            not case["readiness"]["mechanical_solve_authorized"],
            "UNAUTHORIZED_MECHANICAL_SOLVE")
    require(case["solver_output"] is None and case["physical_deforming_t1"] is None,
            "SOLVE_OR_T1_IN_STAGING")
    return {"status":"PASS_STAGED_SOURCE_BOUND__SOLVE_BLOCKED",
            "FEG_nodes":len(model.nodes), "FEG_triangles":len(model.elements),
            "closure_missing":case["readiness"]["missing"],
            "actual_solve_runs":0}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder",type=Path)
    print(json.dumps(verify(parser.parse_args().folder),indent=2))
