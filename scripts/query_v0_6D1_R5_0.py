from pathlib import Path
import argparse
import json
import sys

from arcana_worldsim.state_query.r50_query import R50QueryContract, execute_query

p = argparse.ArgumentParser(description="Run one governed R5.0 arbitrary-age query")
p.add_argument("--root", required=True)
p.add_argument("--age-ka", type=float, required=True)
p.add_argument("--query-id", required=True)
p.add_argument("--out", required=True)
p.add_argument("--domains", nargs="+", default=None)
p.add_argument("--row-min", type=int)
p.add_argument("--row-max", type=int)
p.add_argument("--col-min", type=int)
p.add_argument("--col-max", type=int)
a = p.parse_args()

region_values = (a.row_min, a.row_max, a.col_min, a.col_max)
if any(v is not None for v in region_values) and not all(v is not None for v in region_values):
    p.error("row-min,row-max,col-min,col-max must be supplied together")
region = None if all(v is None for v in region_values) else {
    "grid_row_min": a.row_min, "grid_row_max": a.row_max,
    "grid_col_min": a.col_min, "grid_col_max": a.col_max,
}
kwargs = {}
if a.domains is not None:
    kwargs["requested_domains"] = tuple(a.domains)
q = R50QueryContract(query_id=a.query_id, target_age_ka=a.age_ka, region=region, **kwargs)
try:
    result = execute_query(Path(a.root), q, out_dir=Path(a.out), allow_unverified_r456=False)
    print(json.dumps({
        "stage": "v0.6D1-R5.0",
        "status": "R50_ARBITRARY_AGE_QUERY_COMPLETE",
        "query_id": q.query_id,
        "target_age_ka": q.target_age_ka,
        "semantic_state_sha256": result["semantic_state_sha256"],
        "provenance_modes": {k: v["mode"] for k, v in result["provenance"].items()},
        "output_dir": str(Path(a.out)),
    }, indent=2))
except Exception as e:
    print(json.dumps({"stage": "v0.6D1-R5.0", "status": "FAIL_CLOSED", "error": repr(e)}, indent=2))
    sys.exit(1)
