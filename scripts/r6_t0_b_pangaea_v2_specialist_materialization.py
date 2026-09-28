"""Emit the current FAIR-bound readjudication without rewriting historical reports."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.t0_materialization.specialist_runtime import (
    READJUDICATION_JSON,
    READJUDICATION_MD,
    build_readjudication,
    render_readjudication_markdown,
)

def main() -> int:
    report = build_readjudication(ROOT)
    (ROOT / READJUDICATION_JSON).write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (ROOT / READJUDICATION_MD).write_text(
        render_readjudication_markdown(report), encoding="utf-8"
    )
    print(json.dumps({
        "decision": report["decision"],
        "runtime_commit": report["runtime"]["qualified_runtime_commit"],
        "qualified_for_arcana_capacity": report["runtime"]["qualified_for_arcana_mesh_capacity"],
        "pre_orbdata_ready": report["feg_readiness"]["PRE_ORBDATA_ready"],
        "shells_ready": report["feg_readiness"]["SHELLS_READY_ready"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
