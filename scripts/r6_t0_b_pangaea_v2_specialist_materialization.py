"""Emit the evidence-backed B-v2 specialist materialization gate report."""
from __future__ import annotations

import json
from pathlib import Path

from arcana_worldsim.r6.t0_materialization.specialist_runtime import (
    REPORT_JSON,
    REPORT_MD,
    build_report,
    render_markdown,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    report = build_report(ROOT)
    (ROOT / REPORT_JSON).write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (ROOT / REPORT_MD).write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "decision": report["principal_decision"],
        "specialist_runtimes_available": [
            key for key, value in report["specialist_runtime_qualification"]["runtimes"].items()
            if value["available_on_path"]
        ],
        "pre_orbdata_fegs": report["FEG_status"]["pre_orbdata_fegs"],
        "shells_ready_fegs": report["FEG_status"]["shells_ready_fegs"],
        "runtime_authorized": report["runtime_manifest"]["runtime_authorized"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
