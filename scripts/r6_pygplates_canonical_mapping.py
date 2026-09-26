"""Create a read-only P2 pyGPlates geometry capability diagnostic."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.pygplates_mapping.adapter import (  # noqa: E402
    construct_geometry_candidates,
    load_mapping_input,
)
from arcana_worldsim.r6.pygplates_mapping.diagnostics import (  # noqa: E402
    build_report,
    render_markdown,
)

JSON_REPORT = ROOT / "R6_PYGPLATES_CANONICAL_MAPPING_REPORT.json"
MD_REPORT = ROOT / "R6_PYGPLATES_CANONICAL_MAPPING_REPORT.md"


def main() -> int:
    data = load_mapping_input(ROOT)
    try:
        import pygplates  # type: ignore[import-not-found]
    except ImportError:
        report = build_report(data, None, None, "PYGPLATES_RUNTIME_UNAVAILABLE")
        exit_code = 2
    else:
        try:
            geometry = construct_geometry_candidates(data, pygplates)
            report = build_report(data, str(pygplates.__version__), geometry)
            exit_code = 0
        except Exception as exc:  # Report construction failure without a fabricated pass.
            report = build_report(
                data,
                str(getattr(pygplates, "__version__", "UNKNOWN")),
                None,
                f"GEOMETRY_CANDIDATE_CONSTRUCTION_FAILED: {type(exc).__name__}: {exc}",
            )
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
