"""Probe construction of an R6 t0 pyGPlates topological network."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.pygplates_mapping.adapter import load_mapping_input  # noqa: E402
from arcana_worldsim.r6.pygplates_topology.diagnostics import (  # noqa: E402
    render_markdown,
    runtime_unavailable_report,
)
from arcana_worldsim.r6.pygplates_topology.topology_probe import run_probe  # noqa: E402

JSON_REPORT = ROOT / "R6_PYGPLATES_TOPOLOGY_ASSEMBLY_REPORT.json"
MD_REPORT = ROOT / "R6_PYGPLATES_TOPOLOGY_ASSEMBLY_REPORT.md"


def main() -> int:
    data = load_mapping_input(ROOT)
    try:
        import pygplates  # type: ignore[import-not-found]
    except ImportError:
        report = runtime_unavailable_report(data, "PYGPLATES_RUNTIME_UNAVAILABLE")
        exit_code = 2
    else:
        try:
            report = run_probe(data, pygplates)
            exit_code = 0 if report["status"] == "PASS" else 1
        except Exception as exc:
            report = runtime_unavailable_report(
                data, f"PROBE_FAILED: {type(exc).__name__}: {exc}"
            )
            report["decision"] = "TOPOLOGY_PROBE_RUNTIME_ERROR"
            report["failure_class"] = "PROBE_RUNTIME_ERROR"
            exit_code = 1

    JSON_REPORT.write_text(
        json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    MD_REPORT.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
