from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arcana_worldsim.scientific_engines.r322_functional_phenotype_spec import (  # noqa: E402
    R322GateError,
    audit_documents,
    build_all,
    sha256_file,
    validate_parent_seal,
    write_json,
)


def manifest_for(out: Path, names: list[str], parent: dict) -> dict:
    rows = {}
    for name in names:
        p = out / name
        rows[name] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    return {
        "stage": "v0.6D1-R3.22",
        "status": "CANDIDATE_OUTPUT_MANIFEST",
        "parent_authority": parent,
        "files": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--parent-seal-dir", type=Path)
    ap.add_argument("--output-dir", type=Path)
    ns = ap.parse_args()
    root = ns.root.resolve()
    parent_seal_dir = (ns.parent_seal_dir or (root / "outputs" / "v0_6D1_R3_21_SEAL")).resolve()
    out = (ns.output_dir or (root / "outputs" / "v0_6D1_R3_22")).resolve()

    try:
        parent = validate_parent_seal(parent_seal_dir)
        docs = build_all(parent)
        audit = audit_documents(docs)
        if audit["checks_failed"]:
            raise R322GateError(f"R3.22 internal specification audit failed: {audit['checks_failed']} checks")

        out.mkdir(parents=True, exist_ok=True)
        file_docs = {
            "R3_22_FUNCTIONAL_PHENOTYPE_SPECIFICATION.json": docs["specification"],
            "R3_22_PRIMITIVE_TRAIT_CATALOG.json": docs["traits"],
            "R3_22_DERIVED_CAPABILITY_GRAPH.json": docs["derived"],
            "R3_22_CONSTRAINT_AND_TRADEOFF_GOVERNANCE.json": docs["constraints"],
            "R3_22_REPLAY_STATE_INTERFACE.json": docs["replay"],
            "R3_22_EMPIRICAL_CALIBRATION_REQUIREMENTS.json": docs["calibration"],
            "R3_22_AUDIT_SUMMARY.json": audit,
        }
        for name, obj in file_docs.items():
            write_json(out / name, obj)

        md = [
            "# ARCANA WorldSim v0.6D1-R3.22 — Generic Functional Phenotype Specification Audit",
            "",
            f"Status: `{audit['status']}`",
            f"Checks: **{audit['checks_passed']}/{audit['checks_total']} PASS**",
            "",
            "This stage defines only the generic functional phenotype state space and replay/calibration interfaces.",
            "It does not materialize lineage phenotype values, execute biology, enable Deep, or rank human-likeness.",
            "",
            "## State design",
            "",
            "- 31 primary evolvable functional traits at component level;",
            "- 10 R3.21-reserved domains;",
            "- tool-use potential and environmental problem-solving are derived contextual capabilities;",
            "- species summaries are downstream population-weighted aggregates only;",
            "- future G matrices must be finite, symmetric and positive semidefinite;",
            "- all heritability, covariance, cost and aggregation numerics remain unmaterialized pending empirical calibration.",
            "",
        ]
        (out / "R3_22_AUDIT.md").write_text("\n".join(md) + "\n", encoding="utf-8")

        names = sorted([p.name for p in out.iterdir() if p.is_file() and p.name != "R3_22_OUTPUT_MANIFEST.json"])
        write_json(out / "R3_22_OUTPUT_MANIFEST.json", manifest_for(out, names, parent))

        print(json.dumps({
            "stage": "v0.6D1-R3.22",
            "status": audit["status"],
            "output_dir": str(out),
            "summary": {
                "parent": parent["status"],
                "domains": 10,
                "primitive_traits": 31,
                "derived_capabilities": 2,
                "state_level": "COMPONENT",
                "phenotype_values_materialized": False,
                "new_biology_executed": False,
                "human_target": False,
                "deep_biological_coupling": False,
                "checks_passed": audit["checks_passed"],
                "checks_total": audit["checks_total"],
            },
        }, indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"stage": "v0.6D1-R3.22", "status": "FAIL_CLOSED", "error": str(e)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
