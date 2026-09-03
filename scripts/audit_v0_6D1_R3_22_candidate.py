from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arcana_worldsim.scientific_engines.r322_functional_phenotype_spec import audit_documents, build_all

EXPECTED_FILES = {
    "R3_22_GENERIC_FUNCTIONAL_PHENOTYPE_SPECIFICATION_CONTRACT.md",
    "README_R3_22.md",
    "configs/world1_r322_generic_functional_phenotype_spec_v0_6D1_R3_22.json",
    "schemas/R3_22_FUNCTIONAL_PHENOTYPE_SPEC_SCHEMA.json",
    "schemas/R3_22_REPLAY_STATE_SCHEMA.json",
    "scripts/run_v0_6D1_R3_22_functional_phenotype_spec.py",
    "src/arcana_worldsim/scientific_engines/r322_functional_phenotype_spec.py",
    "tests/test_r322_functional_phenotype_spec.py",
    "run_v0_6D1_R3_22_checks.ps1",
    "run_v0_6D1_R3_22_functional_phenotype_spec.ps1",
}


def fake_parent():
    return {
        "stage": "v0.6D1-R3.21",
        "status": "PASS_R321_H0_PRESENT_LINEAGE_REGISTRY_HISTORICAL_CLOSURE_AND_FUNCTIONAL_PHENOTYPE_FORK_READINESS_SEALED",
        "verdict": "SEALED",
        "checks_passed": 43,
        "source_checkpoint": {
            "json_sha256": "658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71",
            "npz_sha256": "f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406",
        },
        "seal_audit_sha256": "STATIC_AUDIT_PARENT_PLACEHOLDER",
        "seal_manifest_sha256": "STATIC_AUDIT_PARENT_PLACEHOLDER",
    }


def main() -> int:
    checks = []
    def check(name, cond, detail=None):
        checks.append({"name": name, "pass": bool(cond), "detail": detail})

    for rel in sorted(EXPECTED_FILES):
        check(f"file_present::{rel}", (ROOT / rel).is_file())

    for rel in (
        "configs/world1_r322_generic_functional_phenotype_spec_v0_6D1_R3_22.json",
        "schemas/R3_22_FUNCTIONAL_PHENOTYPE_SPEC_SCHEMA.json",
        "schemas/R3_22_REPLAY_STATE_SCHEMA.json",
    ):
        try:
            json.loads((ROOT / rel).read_text(encoding="utf-8"))
            ok = True
        except Exception as e:
            ok = False
        check(f"json_parse::{rel}", ok)

    audit = audit_documents(build_all(fake_parent()))
    check("internal_specification_audit_34_of_34", audit["checks_failed"] == 0 and audit["checks_passed"] == 34 and audit["checks_total"] == 34, audit)

    cfg = json.loads((ROOT / "configs/world1_r322_generic_functional_phenotype_spec_v0_6D1_R3_22.json").read_text())
    check("config_no_values_materialized", cfg["phenotype_values_materialized"] is False and cfg["heritability_values_materialized"] is False and cfg["genetic_covariance_values_materialized"] is False)
    check("config_no_biology_or_deep", cfg["biology_advanced"] is False and cfg["deep_biological_coupling"] is False)
    check("config_no_human_target", cfg["human_target"] is False and cfg["human_readiness_score"] is None)
    check("config_parent_counts", cfg["expected_present_species"] == 134 and cfg["expected_present_components"] == 295)

    failed = [x for x in checks if not x["pass"]]
    report = {
        "stage": "v0.6D1-R3.22",
        "status": "PASS_R322_STATIC_CANDIDATE_AUDIT" if not failed else "FAIL_R322_STATIC_CANDIDATE_AUDIT",
        "checks_passed": len(checks)-len(failed),
        "checks_total": len(checks),
        "checks_failed": len(failed),
        "checks": checks,
    }
    print(json.dumps(report, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
