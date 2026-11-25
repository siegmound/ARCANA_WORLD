"""D12: reproduce exact B6N8N support IDs; no geological assignment."""
from pathlib import Path
import hashlib
import json
import numpy as np

from experiments.r6_thermo_provider_pilot_v1 import s3_d10_t0_pt_relevance as d10
from experiments.t0_authorial_composition_v1 import provider as p
from arcana_worldsim.r6 import geological_source_t0_adapter as geo

BOUNDARY_FILE="R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json"
BOUNDARY_BLOB="7480060b334c0c4eb64013e12ff17e6322c0fd6a"
FIELD=Path("/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY/R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz")
PLATE=Path("/home/jlpfritas/HPC-POMDP/Arcana/_ARCANA_EXTERNAL_SOURCES/r6/tectonic_t0/R6_T0_VECTOR_PLATE_PARTITION.npz")
OUT=d10.BASE/"R6_T0_B6N8N_EXACT_MEMBERSHIP_NEW01"
CONT={1:"CONTINENTAL_COLD_STABLE",2:"CONTINENTAL_NORMAL",3:"CONTINENTAL_HOT_EXTENDED"}


def adjacent(edge,shape):
    r,c,axis=edge["row"],edge["column"],edge["axis"]
    nr,nc=shape
    p.require(type(r) is int and type(c) is int and 0<=r<nr and 0<=c<nc
              and axis in ("EAST","NORTH"),"D12_INVALID_EDGE")
    return (r,c),(r,(c+1)%nc) if axis=="EAST" else ((r+1)%nr,c)


def classify(fields,segments,selected):
    dom=fields["physical_crust_domain_id"]
    shape=dom.shape
    p.require(len(shape)==2 and all(a.shape==shape for a in fields.values()),"D12_FIELD_SHAPE")
    thermal=fields["continental_thermal_domain_id"]
    age=fields["oceanic_lithosphere_age_ma"]
    ocean=dom==1
    continental=np.isin(dom,[2,3,4,5,6])
    p.require(np.all(ocean|continental) and np.all(np.isin(thermal[continental],[1,2,3]))
              and np.all(np.isfinite(age[ocean])) and np.all(age[ocean]>=0)
              and np.all(age[ocean]<=160),"D12_UNCLASSIFIED_DOMAIN")
    for name in ("crustal_thickness_m","continental_reference_lithosphere_thickness_m","continental_reference_surface_heat_flow_w_m2"):
        p.require(np.all(np.isfinite(fields[name][continental])),"D12_CONTINENTAL_NONFINITE")
    ids=[x["boundary_id"] for x in segments]
    p.require(len(ids)==len(set(ids)) and selected<=set(ids),"D12_BOUNDARY_IDS")
    excluded=np.zeros(shape,dtype=bool)
    edges=0
    for seg in segments:
        a,b=adjacent(seg["parent_grid_edge"],shape)
        v=seg["relative_normal_velocity_m_per_year"]
        p.require(np.isfinite(v),"D12_BOUNDARY_VELOCITY")
        if seg["boundary_id"] not in selected and v>0 and ocean[a] and ocean[b]:
            excluded[a]=excluded[b]=True
            edges+=1
    masks={name:continental&(thermal==key) for key,name in CONT.items()}
    masks["ZERO_AGE_RIDGE"]=ocean&(age==0)
    masks["UNRESOLVED_POSITIVE_AGE_OCEAN"]=ocean&(age>0)&excluded
    masks["OCEAN_POSITIVE_AGE_ADMITTED"]=ocean&(age>0)&~excluded
    p.require(np.all(sum(x.astype(np.int8) for x in masks.values())==1),"D12_PARTITION_NOT_EXACT")
    audit={"unselected_positive_normal_ocean_ocean_segments":edges,
           "unique_adjacent_ocean_cells":int(excluded.sum()),
           "overlap_selected_ridge":int((excluded&masks["ZERO_AGE_RIDGE"]).sum())}
    masks["ADMITTED_INITIALIZER_SUPPORT"]=continental|masks["OCEAN_POSITIVE_AGE_ADMITTED"]
    return masks,audit


def encoded(mask):
    return "".join(f"R6G1D-R{r:03d}-C{c:03d}\n" for r,c in np.argwhere(mask)).encode("utf-8")


def verified_membership(masks,index):
    bodies={}
    expected=index["membership_sha256"]
    p.require(set(masks)==set(expected),"D12_CLASS_KEYS")
    counts={x["class"]:x["count"] for x in index["support_classes"]}
    counts["ADMITTED_INITIALIZER_SUPPORT"]=index["partition_counts"]["admitted"]
    for name,mask in masks.items():
        body=encoded(mask)
        p.require(int(mask.sum())==counts[name] and hashlib.sha256(body).hexdigest()==expected[name],
                  "D12_MEMBERSHIP_DRIFT:"+name)
        bodies[name]=body
    return bodies


def main():
    root=d10.ROOT
    pins=geo.verify_manifests(root)
    idx=p.source_index(root)
    fields=geo.verified_npz(FIELD,p.FIELD_SHA,geo.FIELDS)
    parts=geo.verified_npz(PLATE,p.PLATE_SHA,("face_row","face_col","face_plate_id"))
    grid=geo.reconstruct_plates(parts,pins["plate_ids"])
    p.require(grid.shape==(180,360) and set(np.unique(grid))==set(range(12)),"D12_CANONICAL_PLATES")
    raw=(root/BOUNDARY_FILE).read_bytes()
    p.require(geo.gitblob(raw)==BOUNDARY_BLOB,"D12_BOUNDARY_BLOB_DRIFT")
    boundary=json.loads(raw)
    selected=set(pins["field"]["derived_fields"]["oceanic_age"]["selected_source_boundary_ids"])
    segments=boundary["segments"]
    p.require(len(selected)==79 and len(segments)==1983 and boundary["parent_vector_partition_sha256"]==p.PLATE_SHA,"D12_BOUNDARY_PROVENANCE")
    masks,audit=classify(fields,segments,selected)
    p.require(all(v==idx["boundary_exclusion_audit"][k] for k,v in audit.items()),"D12_BOUNDARY_EXCLUSION_AUDIT_DRIFT")
    bodies=verified_membership(masks,idx)
    p.require(not OUT.resolve().is_relative_to(root.resolve()) and not OUT.exists(),"D12_OUTPUT_EXISTS_OR_IN_REPO")
    OUT.mkdir(parents=True,exist_ok=False)
    manifest={"schema":"R6_T0_B6N8N_EXACT_MEMBERSHIP_V1","field_sha256":p.FIELD_SHA,
        "plate_sha256":p.PLATE_SHA,"boundary_git_blob":BOUNDARY_BLOB,"files":{},
        "material_assignments":0,"physical_T1":None,"mechanical_solve_authorized":False,
        "WORLD_HISTORY_PRODUCTION_AUTHORIZED":False}
    for name,body in sorted(bodies.items()):
        filename=name+".txt"
        (OUT/filename).write_bytes(body)
        digest=hashlib.sha256((OUT/filename).read_bytes()).hexdigest()
        p.require(digest==idx["membership_sha256"][name],"D12_OUTPUT_HASH_DRIFT")
        manifest["files"][filename]=digest
        print("CLASS",name,int(masks[name].sum()),digest)
    p.exact_member_ids(OUT/"ADMITTED_INITIALIZER_SUPPORT.txt",idx["membership_sha256"]["ADMITTED_INITIALIZER_SUPPORT"])
    print("BOUNDARY_AUDIT",json.dumps(audit,sort_keys=True))
    (OUT/"MANIFEST.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print("MANIFEST_SHA256",geo.sha((OUT/"MANIFEST.json").read_bytes()))
    print("PLATE_IDS",json.dumps(list(map(int,np.unique(grid)))))
    print("D12_NATIVE_MEMBERSHIP_COMPLETE")
    print("MATERIAL_ASSIGNMENTS=0")
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()
