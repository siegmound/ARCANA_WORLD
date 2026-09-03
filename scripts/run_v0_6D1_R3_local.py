from __future__ import annotations
import argparse, json, os, sys, time
from dataclasses import replace
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from rebased_natural_control_runtime_v0_6D1_R3_2 import R3Config, run


def jsonable_result(r):
    event_counts = {}
    for e in r["events"]:
        event_counts[e["event"]] = event_counts.get(e["event"], 0) + 1
    return {
        "stage": r["stage"],
        "config": r["config"],
        "initial_total_population": r["initial_total_population"],
        "final_total_population": r["final_total_population"],
        "species_count": len(r["species_ids"]),
        "component_count": len(r["component_ids"]),
        "species_ids": r["species_ids"],
        "event_counts": event_counts,
        "events": r["events"],
        "snapshots": r["snapshots"],
        "registry": r["registry"],
        "gate_diagnostics": r["gate_diagnostics"],
        "gene_flow_closure": r["gene_flow_closure"],
        "topology_remap_mass": r["topology_remap_mass"],
        "barrier_history": r["barrier_history"],
        "authority": r["authority"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--end-age-ma", type=float, default=150.0)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "local_runs" / "v0_6D1_R3_2")
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--fission-off", action="store_true")
    args = ap.parse_args()
    if args.threads > 0:
        # Must be set before heavy BLAS/OpenMP work; harmless when backend ignores it.
        for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
            os.environ[k] = str(args.threads)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    common = np.load(ROOT / "outputs/v0_6D1_R1/WORLD1_210Ma_REBASELINE_COMMON_STATE_v0_6D1_R1.npz", allow_pickle=False)
    a1 = np.load(ROOT / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz", allow_pickle=False)
    md = json.loads((ROOT / "references/v0_6D1_R3/D1_SPECIES_METADATA.json").read_text())
    rows = md["species"] if isinstance(md, dict) and "species" in md else md
    cfg = R3Config(end_age_ma=float(args.end_age_ma), persistent_vicariance_fission_enabled=not args.fission_off)
    tag = f"210_to_{str(args.end_age_ma).replace('.','p')}Ma" + ("_FISSION_OFF" if args.fission_off else "")
    t0 = time.time()
    r = run(common, a1, rows, cfg)
    elapsed = time.time() - t0
    meta = jsonable_result(r)
    meta["wall_seconds"] = elapsed
    (args.out_dir / f"{tag}_summary.json").write_text(json.dumps(meta, indent=2))
    np.savez_compressed(
        args.out_dir / f"{tag}_state.npz",
        population=r["population"], trait=r["trait"], va=r["va"],
        generation_time=r["generation_time"], ri=r["ri"], clock=r["clock"],
        contact=r["contact"], trait_distance=r["trait_distance"],
        component_guild=r["component_guild"],
        component_ids=np.asarray(r["component_ids"], dtype="U160"),
        component_root_species=np.asarray(r["component_root_species"], dtype="U80"),
        component_species=np.asarray(r["component_species"], dtype="U80"),
    )
    print(json.dumps({
        "status": "PASS_LOCAL_R3_2_RUN_COMPLETED",
        "tag": tag,
        "wall_seconds": elapsed,
        "final_total_population": r["final_total_population"],
        "species_count": len(r["species_ids"]),
        "component_count": len(r["component_ids"]),
        "event_counts": meta["event_counts"],
        "summary": str(args.out_dir / f"{tag}_summary.json"),
        "state": str(args.out_dir / f"{tag}_state.npz"),
    }, indent=2))

if __name__ == "__main__":
    main()
