from __future__ import annotations
import argparse, json, hashlib, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from rebaseline_210ma_v0_6D1_R1 import (
    RebaselineConfig, build_common_state, semantic_hash, conservation_diagnostics,
    paired_manifests, allowed_branch_delta, MODES,
)


def _load_npz(path: Path):
    z = np.load(path, allow_pickle=False)
    return {k: z[k] for k in z.files}


def _species_exposure(arrays, bio_cfg):
    pop = np.asarray(arrays["species_population"], float)
    opp = np.asarray(arrays["deep_mode_opportunity_equilibrium"], float)
    weights = np.asarray([float(bio_cfg["mode_load_weights"][m]) for m in MODES], float)
    # Z_X=0 => coupling=uptake=regulation=tolerance=0.5, acclimation/remodeling=0.
    coupling = 0.5; uptake = 0.5; regulation = 0.5
    operating = float(bio_cfg["regulation"]["baseline_operating_fraction"])
    divisor = 1.0 + float(bio_cfg["regulation"]["load_reduction_gain"]) * regulation * operating
    cell_L = uptake * np.sum(weights[:,None,None] * coupling * opp, axis=0) / divisor
    scale = float(bio_cfg["tolerance_scale"]["intercept"]) + float(bio_cfg["tolerance_scale"]["heritable_tolerance"]) * 0.5
    b = bio_cfg["threshold_base_load_units"]
    thresholds = {k: float(b[k]) * scale for k in ("L_min","L_opt","L_tol","L_injury")}
    totals = pop.sum((1,2))
    mean_L = np.divide(np.sum(pop * cell_L[None,:,:], axis=(1,2)), totals, out=np.zeros(len(totals)), where=totals>0)
    # population-weighted global regime fractions
    total_pop = float(pop.sum())
    flat_weight = pop.sum(0)
    Lmin,Lopt,Ltol,Lin = [thresholds[k] for k in ("L_min","L_opt","L_tol","L_injury")]
    masks = {
        "negligible": cell_L < Lmin,
        "adaptive": (cell_L >= Lmin) & (cell_L < Lopt),
        "post_optimum_stress": (cell_L >= Lopt) & (cell_L < Ltol),
        "tolerance_exceeded": (cell_L >= Ltol) & (cell_L < Lin),
        "injury": cell_L >= Lin,
    }
    regime = {k: (float(flat_weight[m].sum())/total_pop if total_pop>0 else 0.0) for k,m in masks.items()}
    return {
        "thresholds": thresholds,
        "species_mean_L_min": float(mean_L.min()),
        "species_mean_L_median": float(np.median(mean_L)),
        "species_mean_L_max": float(mean_L.max()),
        "global_population_weighted_L": float(np.sum(flat_weight*cell_L)/total_pop),
        "regime_population_fraction": regime,
        "max_cell_L": float(cell_L.max()),
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    args=ap.parse_args(); root=args.root.resolve()
    ref=root/"references"/"v0_6D1_R1"; out=root/"outputs"/"v0_6D1_R1"; out.mkdir(parents=True,exist_ok=True)
    metadata=json.loads((ref/"D1_species_metadata_120.json").read_text())
    a1=_load_npz(ref/"A1_WORLD1_210Ma_REFERENCE.npz")
    deep=_load_npz(ref/"DEEP_WORLD1_210Ma_REFERENCE_v0_5.npz")
    cal=json.loads((ref/"WORLD1_DEEP_FREE_ENERGY_CALIBRATION_v0_5.json").read_text())
    bio=json.loads((root/"references"/"deep_biological_coupling_v0_4.json").read_text())
    cfg_json=json.loads((root/"configs"/"world1_rebaseline_210ma_v0_6D1_R1.json").read_text())
    cfg=RebaselineConfig(**{k:cfg_json[k] for k in RebaselineConfig.__dataclass_fields__ if k in cfg_json})
    arrays, meta=build_common_state(metadata,a1,deep,cal,cfg)
    sem=semantic_hash(arrays,meta); meta["semantic_sha256"]=sem
    np.savez_compressed(out/"WORLD1_210Ma_REBASELINE_COMMON_STATE_v0_6D1_R1.npz", **arrays)
    (out/"WORLD1_210Ma_REBASELINE_COMMON_STATE_METADATA_v0_6D1_R1.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
    diag=conservation_diagnostics(arrays); diag["status"]="PASS" if diag["max_cell_population_closure_abs"]<1e-12 and diag["max_cell_capacity_closure_abs"]<1e-12 and diag["population_exceeds_capacity_count"]==0 and diag["nonland_population_cells"]==0 else "FAIL"
    (out/"REBASELINE_CONSERVATION_AUDIT_v0_6D1_R1.json").write_text(json.dumps(diag,indent=2,sort_keys=True)+"\n")
    exposure=_species_exposure(arrays,bio)
    exposure["status"]="PASS_INITIAL_DEEP_EXPOSURE_NONCATASTROPHIC" if exposure["regime_population_fraction"]["tolerance_exceeded"]==0 and exposure["regime_population_fraction"]["injury"]==0 else "FAIL"
    (out/"INITIAL_DEEP_EXPOSURE_AUDIT_v0_6D1_R1.json").write_text(json.dumps(exposure,indent=2,sort_keys=True)+"\n")
    h0,hx=paired_manifests(sem,cfg)
    (out/"H0_REPLAY_INITIALIZATION_v0_6D1_R1.json").write_text(json.dumps(h0,indent=2,sort_keys=True)+"\n")
    (out/"HX_REPLAY_INITIALIZATION_v0_6D1_R1.json").write_text(json.dumps(hx,indent=2,sort_keys=True)+"\n")
    delta=allowed_branch_delta(h0,hx)
    (out/"PAIRED_INITIALIZATION_DELTA_AUDIT_v0_6D1_R1.json").write_text(json.dumps(delta,indent=2,sort_keys=True)+"\n")
    # species table for human audit
    ids=arrays['species_id'].astype(str); gids=arrays['guild_id'].astype(int); pt=arrays['species_population'].sum((1,2)); kt=arrays['species_carrying_capacity'].sum((1,2)); occ=(arrays['species_population']>1e-12).sum((1,2))
    rows=[{"species_id":ids[i],"guild_id":int(gids[i]),"population_210Ma":float(pt[i]),"carrying_capacity_210Ma":float(kt[i]),"occupied_cells":int(occ[i]),"deep_latent_mean":0.0,"deep_latent_va":cfg.latent_va_equilibrium} for i in range(len(ids))]
    (out/"SPECIES_210Ma_REBASELINE_REGISTRY_v0_6D1_R1.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    summary={
        "status":"PASS_210MA_CANONICAL_REBASELINE_AND_PAIRED_H0_HX_INITIALIZATION_CANDIDATE" if diag['status']=='PASS' and delta['pass'] and exposure['status'].startswith('PASS') else 'FAIL',
        "semantic_sha256":sem,
        "species_count":len(ids),
        "global_population":float(pt.sum()),
        "global_carrying_capacity":float(kt.sum()),
        "population_closure_max_abs":diag['max_cell_population_closure_abs'],
        "capacity_closure_max_abs":diag['max_cell_capacity_closure_abs'],
        "latent_va":cfg.latent_va_equilibrium,
        "photo_share_E_th":cfg.photo_additive_share_E_th,
        "paired_seed":cfg.paired_rng_seed,
        "h0_hx_unexpected_delta_keys":delta['unexpected_delta_keys'],
        "initial_exposure":exposure,
    }
    (out/"V0_6D1_R1_MATERIALIZATION_SUMMARY.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2,sort_keys=True))
    return 0 if summary['status'].startswith('PASS') else 1
if __name__=='__main__': raise SystemExit(main())
