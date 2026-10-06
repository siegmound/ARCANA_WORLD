"""Run the isolated, noncanonical B6N8-A diagnostic shadow experiment."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from arcana_worldsim.r6.b6n8a_shadow import run_diagnostic  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path,
                        help="new/empty directory outside repository and canonical store")
    parser.add_argument("--canonical-root", type=Path,
                        default=os.environ.get("ARCANA_WORLD_HISTORY_ROOT"),
                        help="canonical WORLD_HISTORY root (defaults to environment)")
    parser.add_argument("--window-fraction", type=float, default=0.25,
                        help="diagnostic fraction of B6N3-A model-scope bound; must be in (0,1)")
    args = parser.parse_args()
    if args.canonical_root is None:
        parser.error("--canonical-root or ARCANA_WORLD_HISTORY_ROOT is required")
    try:
        result = run_diagnostic(REPOSITORY_ROOT, args.canonical_root,
                                args.output_dir, args.window_fraction)
    except (OSError, ValueError) as exc:
        print(json.dumps({"decision": "BLOCKED_B6N8A_PREFLIGHT_REJECTED",
                          "reason": str(exc),
                          "result_written": False}, indent=2, sort_keys=True),
              file=sys.stderr)
        return 2
    print(json.dumps({
        "decision": result["decision"],
        "result_path": str((args.output_dir.resolve() / "B6N8A_SHADOW_RESULT.json")),
        "interface_node_count": result["experiment"]["interface_node_count"],
        "diagnostic_window_years": result["experiment"]["diagnostic_window_years"],
        "resolution_step_counts": [row["step_count"] for row in
                                   result["experiment"]["resolution_ladder"]],
        "canonical_unchanged": result["canonical_invariance"]["identical"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
