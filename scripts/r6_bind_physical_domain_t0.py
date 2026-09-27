from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.physical_domain_t0 import bind_physical_t0, render_markdown


def main() -> int:
    store_root = ROOT / "world_history_bindings" / "r6_physical_world_t0"
    report = bind_physical_t0(ROOT, store_root)
    (ROOT / "R6_PHYSICAL_DOMAIN_T0_BINDING_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8")
    (ROOT / "R6_PHYSICAL_DOMAIN_T0_BINDING_REPORT.md").write_text(
        render_markdown(report), encoding="utf-8")
    print(json.dumps({"decision": report["decision"],
                      "state_id": report["history_binding"]["state_id"],
                      "history_store_bound": report["history_binding"]["history_store_bound"],
                      "first_interval_authorized": report["first_interval"]["authorized"]},
                     ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
