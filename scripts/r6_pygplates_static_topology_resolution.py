"""Resolve the 12 canonical static R6 topological polygons at diagnostic epoch 0."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.pygplates_mapping.adapter import load_mapping_input  # noqa: E402
from arcana_worldsim.r6.pygplates_topology.diagnostics import (  # noqa: E402
    render_static_topology_markdown,
)
from arcana_worldsim.r6.pygplates_topology.static_resolution import (  # noqa: E402
    run_static_topology_resolution,
    runtime_unavailable_report,
)

JSON_REPORT = ROOT / "R6_PYGPLATES_STATIC_TOPOLOGY_RESOLUTION_REPORT.json"
MD_REPORT = ROOT / "R6_PYGPLATES_STATIC_TOPOLOGY_RESOLUTION_REPORT.md"


def main() -> int:
    data = load_mapping_input(ROOT)
    try:
        import pygplates  # type: ignore[import-not-found]
    except ImportError:
        report = runtime_unavailable_report(data, "PYGPLATES_RUNTIME_UNAVAILABLE")
    else:
        try:
            report = run_static_topology_resolution(data, pygplates)
        except Exception as exc:
            report = runtime_unavailable_report(
                data, f"STATIC_TOPOLOGY_PROBE_ERROR: {type(exc).__name__}: {exc}"
            )
            report["decision"] = "STATIC_TOPOLOGY_PROBE_ERROR"

    JSON_REPORT.write_text(
        json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    MD_REPORT.write_text(render_static_topology_markdown(report), encoding="utf-8")
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
    return 0 if report["status"] == "PASS" else 1 if report["status"] == "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
