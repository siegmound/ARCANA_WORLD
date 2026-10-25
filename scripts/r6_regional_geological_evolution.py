from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
import tracemalloc

from arcana_worldsim.r6.functional_development import NodeMaterial, ReducedState
from arcana_worldsim.r6.geological_surface_microdomain import (
    SUPPORTS, load_verified_r6_initial_columns,
)
from arcana_worldsim.r6.regional_geological_evolution import (
    RegionalConfig, run_regional_segment, verify_regional_checkpoint,
)


DEFAULT_SOURCE = Path("outputs/r6_experimental_multiphysics/MATERIAL_RHEOLOGY_PROVIDER_20261025_03")
DEFAULT_OUTPUT = Path("outputs/r6_experimental_multiphysics/REGIONAL_GEOLOGICAL_EVOLUTION_V2_20261025_01")


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _state(payload):
    return ReducedState(
        time_s=float(payload["time_s"]), initial_width_m=float(payload["initial_width_m"]),
        width_m=float(payload["width_m"]), initial_crust_m=float(payload["initial_crust_m"]),
        initial_lithosphere_m=float(payload["initial_lithosphere_m"]), crust_m=float(payload["crust_m"]),
        lithosphere_m=float(payload["lithosphere_m"]), beta=float(payload["beta"]),
        accumulated_strain=float(payload["accumulated_strain"]),
        crust_fraction=float(payload["crust_fraction"]),
        material_coordinate=tuple(payload["material_coordinate"]),
        temperature_k=tuple(payload["temperature_k"]),
        materials=tuple(NodeMaterial(**row) for row in payload["materials"]),
        surface_temperature_k=float(payload["surface_temperature_k"]),
        base_temperature_k=float(payload["base_temperature_k"]))


def run(source_dir: Path, output_dir: Path, *, years: int,
        checkpoint_in: Path | None = None,
        routing_mode: str = "DYNAMIC_TOPOGRAPHY",
        perturb_cell: int | None = None,
        perturbation_m: float = 0.0,
        topography_offsets_m_by_cell: tuple[float, ...] | None = None,
        hydraulic_connectivity_edges: tuple[tuple[int, int], ...] = ()) -> dict:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite {output_dir}")
    started = time.perf_counter()
    tracemalloc.start()
    payloads, identity = load_verified_r6_initial_columns(source_dir)
    states = {support: _state(payloads[support]) for support in SUPPORTS}
    offsets = list(topography_offsets_m_by_cell or (0.0,) * 9)
    if len(offsets) != 9:
        raise ValueError("topography offset vector must contain nine values")
    if perturb_cell is not None:
        if not 0 <= perturb_cell < len(offsets):
            raise ValueError("perturbation cell must be in [0, 8]")
        if offsets[perturb_cell] != 0.0:
            raise ValueError("duplicate topography offset for perturbation cell")
        offsets[perturb_cell] = perturbation_m
    cfg = RegionalConfig(duration_years=max(years, 3), routing_mode=routing_mode,
        initial_elevation_offsets_m_by_cell=tuple(offsets),
        hydraulic_connectivity_edges=hydraulic_connectivity_edges)
    checkpoint = None
    if checkpoint_in is not None:
        raw = json.loads(checkpoint_in.read_text(encoding="utf-8"))
        checkpoint = raw.get("checkpoint", raw)
        verify_regional_checkpoint(checkpoint)
    result = run_regional_segment(states, identity, config=cfg,
                                  segment_years=years, checkpoint=checkpoint)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    result["measurements"] = {"elapsed_seconds_including_input_verification": time.perf_counter() - started,
                              "tracemalloc_peak_bytes": peak,
                              "rss_measured": False}
    output_dir.mkdir(parents=True, exist_ok=False)
    result_bytes = _canonical(result)
    result_sha = hashlib.sha256(result_bytes).hexdigest()
    (output_dir / "RESULT.json").write_bytes(result_bytes)
    sidecar = f"{result_sha}  RESULT.json\n".encode("ascii")
    (output_dir / "RESULT.json.sha256").write_bytes(sidecar)
    checkpoint_bytes = _canonical(result["checkpoint"])
    checkpoint_sha = hashlib.sha256(checkpoint_bytes).hexdigest()
    (output_dir / "REGIONAL_CHECKPOINT.json").write_bytes(checkpoint_bytes)
    checkpoint_sidecar = f"{checkpoint_sha}  REGIONAL_CHECKPOINT.json\n".encode("ascii")
    (output_dir / "REGIONAL_CHECKPOINT.json.sha256").write_bytes(checkpoint_sidecar)
    members = []
    for name in ("RESULT.json", "RESULT.json.sha256", "REGIONAL_CHECKPOINT.json",
                 "REGIONAL_CHECKPOINT.json.sha256"):
        data = (output_dir / name).read_bytes()
        members.append({"path": name, "size_bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest()})
    manifest = {"schema": "ARCANA_R6_REGIONAL_GEOLOGICAL_MANIFEST_V2",
                "completion": "SEGMENT_COMPLETED_AND_CHECKPOINT_SEALED",
                "source_identity_sha256": hashlib.sha256(_canonical(result["source_identity"])).hexdigest(),
                "members": members}
    manifest_bytes = _canonical(manifest)
    (output_dir / "MANIFEST.json").write_bytes(manifest_bytes)
    return {"output_dir": str(output_dir), "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "result_sha256": result_sha, "elapsed_seconds": result["measurements"]["elapsed_seconds_including_input_verification"],
            "output_bytes": sum(p.stat().st_size for p in output_dir.iterdir() if p.is_file()),
            "end_year": result["state"]["time_years"],
            "water_balance": result["balances"]["water"],
            "solid_balance": {k: v for k, v in result["balances"]["solid_mass_kg"].items() if k != "per_cell"},
            "routing_mode": result["state"]["config"]["routing_mode"],
            "final_drainage_targets": result["state"]["drainage_targets"],
            "routing_change_events": len(result["state"]["routing_events"]),
            "depression_storage_m3": sum(c["depression_storage_m3"] for c in result["state"]["cells"])}


def main() -> int:
    p = argparse.ArgumentParser(description="Short noncanonical 3x3 regional geology experiment")
    p.add_argument("--source-result-dir", type=Path, default=DEFAULT_SOURCE)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--years", type=int, default=1)
    p.add_argument("--checkpoint-in", type=Path)
    p.add_argument("--routing-mode", choices=("FIXED_BASELINE", "DYNAMIC_TOPOGRAPHY"),
                   default="DYNAMIC_TOPOGRAPHY")
    p.add_argument("--perturb-cell", type=int)
    p.add_argument("--perturbation-m", type=float, default=0.0)
    p.add_argument("--topography-offset", action="append", default=[], metavar="CELL=METRES",
                   help="explicit synthetic initial elevation offset; repeat per cell")
    p.add_argument("--connect-b5-hydrology", action="store_true",
                   help="enable only synthetic hydraulic edge C04-C05; no mechanics/Deep coupling")
    args = p.parse_args()
    try:
        offsets = [0.0] * 9
        seen_offset_cells = set()
        for item in args.topography_offset:
            cell_text, sep, value_text = item.partition("=")
            if not sep:
                raise ValueError("--topography-offset requires CELL=METRES")
            cell = int(cell_text)
            if not 0 <= cell < 9 or cell in seen_offset_cells:
                raise ValueError("topography offset cell invalid or duplicated")
            offsets[cell] = float(value_text)
            seen_offset_cells.add(cell)
        print(json.dumps(run(args.source_result_dir, args.output_dir,
                             years=args.years, checkpoint_in=args.checkpoint_in,
                             routing_mode=args.routing_mode,
                             perturb_cell=args.perturb_cell,
                             perturbation_m=args.perturbation_m,
                             topography_offsets_m_by_cell=tuple(offsets),
                             hydraulic_connectivity_edges=((4, 5),)
                                 if args.connect_b5_hydrology else ()), indent=2))
    except Exception as exc:
        p.exit(2, f"regional run failed closed: {type(exc).__name__}: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
