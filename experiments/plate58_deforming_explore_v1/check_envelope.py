"""Offline, read-only verification of the 16-cell source-bound G3 diagnostic."""
import argparse
import json
from pathlib import Path

from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
from experiments.plate58_deforming_explore_v1.envelope import (
    STATUS, edge_incidence, require, sha, side_of_edge,
)


def verify(folder):
    m=json.loads((folder/"MANIFEST.json").read_text())
    d=json.loads((folder/"NEIGHBORHOOD.json").read_text())
    require(m["status"] == d["status"] == STATUS and
            m["no_solver_run"] and m["no_T1"] and m["no_canonical_promotion"],
            "ENVELOPE_STATUS_OR_AUTHORITY_INVALID")
    require(set(m["files"]) == {"NEIGHBORHOOD.json","REGIONAL_16.feg"},
            "MANIFEST_FILE_INVENTORY_INVALID")
    for name,digest in m["files"].items():
        require((folder/name).is_file() and sha(folder/name)==digest,
                "ENVELOPE_FILE_HASH_INVALID:" + name)
    source=parse_feg((folder/"REGIONAL_16.feg").read_text(),mode="SHELLS_READY")
    require(len(source.nodes)==25 and len(source.elements)==32 and not source.faults,
            "ENVELOPE_MESH_INVALID")
    require(len(d["parent_cells"])==16 and len(d["parent_triangle_ids"])==32
            and len(d["parent_node_ids"])==25, "ENVELOPE_PARENT_INVENTORY_INVALID")
    graph=edge_incidence(source.elements,d["triangle_plate_ids"])
    # Local FEG IDs and global parent source IDs must give the same topology.
    contact=[e for e,v in graph.items() if len(v)==2 and v[0][1]!=v[1][1]]
    source_contact={
        tuple(sorted(d["parent_node_ids"][i-1] for i in edge))
        for edge in contact}
    expected={tuple(row["parent_node_ids"]) for row in d["boundary_analysis"]["source_contact"]}
    require(source_contact==expected and len(source_contact)==d["boundary_analysis"]["source_contact_count"],
            "SOURCE_CONTACT_REPLAY_MISMATCH")
    cuts=d["boundary_analysis"]["side_segments"]
    require(all(len(cuts[side])==4 for side in ("north","south","east","west")),
            "CUT_SEGMENT_COUNT_INVALID")
    require(all(row["prescribed_velocity"] is None and row["exterior_traction"] is None
                for side in cuts.values() for row in side), "FABRICATED_BC_NOT_ALLOWED")
    require(d["G3_north_cut"] is None and d["G3_south_cut"] is None and
            d["G3_basal_normal_support"] is None and
            d["G2_material_coefficients"] is None and
            not d["mechanical_solve_authorized"] and d["first_deforming_T1"] is None and
            d["solver_runs"]==0, "MECHANICAL_CLOSURE_FABRICATED")
    return {"status":"PASS_G3_NEIGHBOR_DIAGNOSTIC__SOLVE_BLOCKED",
            "nodes":len(source.nodes),"triangles":len(source.elements),
            "source_contact_segments":len(contact),
            "north_owners":d["boundary_analysis"]["side_plate_ownership"]["north"],
            "south_owners":d["boundary_analysis"]["side_plate_ownership"]["south"],
            "no_solve":True}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder",type=Path)
    print(json.dumps(verify(parser.parse_args().folder),indent=2))
