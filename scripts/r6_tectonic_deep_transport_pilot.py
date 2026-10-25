from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.tectonic_deep_pilot import load_archived_state_jsonl, run_multistep_transport_comparison

DEFAULT_ARCHIVE = Path(r"F:\corsiiiuu\Magistrale\Arcana\ENG10K_LUNA_ANALYSIS\ENG10K_ARCHIVE_ec79bf89_01.tar.gz")
DEFAULT_OUTPUT = ROOT / "outputs/r6_experimental_multiphysics/TECTONIC_DEEP_TRANSPORT_PILOT_20261025_01/RESULT.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Short noncanonical multi-step Deep transport comparison")
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--steps", type=int, default=3)
    parser.add_argument("--step-years", type=float, default=1.0)
    parser.add_argument("--transport-fraction", type=float, default=0.2)
    args = parser.parse_args()
    target = args.output.resolve()
    if "WORLD_HISTORY" in str(target).upper():
        parser.error("canonical WORLD_HISTORY paths are prohibited")
    if target.exists():
        parser.error(f"output already exists; refusing overwrite: {target}")
    state, provenance = load_archived_state_jsonl(str(args.archive))
    result = run_multistep_transport_comparison(
        state,
        steps=args.steps,
        step_years=args.step_years,
        extension_velocity_m_per_year=float(provenance["frozen_euler_extension_m_per_year"]),
        transport_fraction=args.transport_fraction,
    )
    result["input_provenance"] = provenance
    result["component_source_sha256"] = {
        "thermal_kernel_module": hashlib.sha256(
            (ROOT / "src/arcana_worldsim/r6/functional_development.py").read_bytes()
        ).hexdigest(),
        "deep_v06a_operator_module": hashlib.sha256(
            (ROOT / "src/deep_d3_coupling_v0_6A.py").read_bytes()
        ).hexdigest(),
        "pilot_adapter_module": hashlib.sha256(
            (ROOT / "src/arcana_worldsim/r6/tectonic_deep_pilot.py").read_bytes()
        ).hexdigest(),
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    for _ in range(5):
        result["measurements"]["output_bytes"] = size
        encoded = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
        if len(encoded) == size:
            break
        size = len(encoded)
    with target.open("xb") as handle:
        handle.write(encoded)
        handle.flush()
    actual_size = target.stat().st_size
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    print(json.dumps({
        "result_path": str(target),
        "result_sha256": digest,
        "actual_output_bytes": actual_size,
        "steps": args.steps,
        "transport_changes_spatial_distribution": result["comparison"]["transport_changes_spatial_distribution"],
        "max_distribution_difference_j": result["comparison"]["max_abs_final_cell_distribution_difference_j"],
        "elapsed_seconds_both_branches": result["measurements"]["elapsed_seconds_both_branches"],
        "tracemalloc_peak_bytes": result["measurements"]["tracemalloc_peak_bytes"],
        "result": result,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
