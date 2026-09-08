from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

OUTPUT_PATH = Path("R5_16_NEGATIVE_RESULT_PRESERVATION.json")
PREREQUISITE_PATH = Path("R5_16_LEGACY_RECONCILIATION_AUDIT.json")
EXPECTED_BRANCH = "main"
EXPECTED_SOURCE_COMMIT = "986288671724a5ec2b483a25dfdfa9afdb410e8e"
TARGET_COHORT = ["RPT_010_D02", "RPT_009_D02"]

R5_PATHS = {
    n: Path(f"outputs/v0_6D1_R5_{n}/R5_{n}_INTEGRATED_RECONCILIATION.json")
    for n in range(8, 15)
}
R515_PATH = Path("R5_15_FINAL_AUDIT_PASS2.json")
LEGACY_PATHS = {
    n: Path(f"outputs/v0_6D1_R3_{n}_SEAL/R3_{n}_FINAL_SEAL_AUDIT.json")
    for n in range(34, 40)
}


def run_git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode:
        raise SystemExit(f"git {' '.join(args)} failed:\n{proc.stderr}")
    return proc.stdout.strip()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Cannot parse JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object in {path}")
    return value


def all_true_dict(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and bool(value)
        and all(v is True for v in value.values())
    )


def all_pass_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(x, dict) and x.get("pass") is True for x in value)
    )


def exact_keys(value: Any) -> bool:
    return isinstance(value, dict) and set(value) == set(TARGET_COHORT)


def require(gaps: list[str], label: str, condition: bool) -> bool:
    if not condition:
        gaps.append(label)
    return condition


def build_audit(root: Path, branch: str, head: str) -> dict[str, Any]:
    os.chdir(root)
    gaps: list[str] = []

    required = [
        PREREQUISITE_PATH,
        R515_PATH,
        *R5_PATHS.values(),
        *LEGACY_PATHS.values(),
    ]
    missing = [p.as_posix() for p in required if not p.is_file()]
    if missing:
        gaps.extend(f"MISSING:{p}" for p in missing)
        return blocked(branch, head, gaps)

    c = load_json(PREREQUISITE_PATH)
    prerequisite_pass = all(
        [
            require(gaps, "C:stage", c.get("stage") == "v0.6D1-R5.16"),
            require(gaps, "C:subphase", c.get("subphase") == "R5.16-C"),
            require(
                gaps,
                "C:status",
                c.get("status") == "PASS_R516_LEGACY_RECONCILIATION_AUDIT",
            ),
            require(
                gaps,
                "C:integrity",
                c.get("legacy_reconciliation_integrity") is True,
            ),
            require(
                gaps,
                "C:gaps",
                c.get("open_legacy_reconciliation_gap_count") == 0,
            ),
            require(gaps, "C:stages", c.get("stages_verified") == 6),
        ]
    )

    r5: dict[int, dict[str, Any]] = {}
    r5_common_pass = True
    explicit = {
        8: ["human_200ka_not_final_unique_species_identity"],
        9: ["r328_0ka_unique_identity_not_materialized"],
        10: ["no_culture_identity_materialized", "no_unique_human_identity_materialized"],
        11: ["r330_checkpoint_two_lineages_no_unique_identity", "r330_no_culture_identity_materialized"],
        12: ["r331_no_ethnicity_named_culture", "r331_no_language_religion_agriculture_city_state", "r331_no_unique_human_identity"],
        13: ["r332_no_agriculture_or_domesticated_species", "r332_no_named_culture_language_religion_city_state_ethnicity", "r332_no_unique_human_identity"],
        14: ["agriculture_forbidden_at_r333", "align::observed_no_materialized_or_incipient_species", "align::observed_no_reproductive_control_or_domestication_stage", "both_human_lineages_retained", "plant_domestication_forbidden_at_r333"],
    }

    for n, path in R5_PATHS.items():
        d = load_json(path)
        r5[n] = d
        checks = d.get("checks")
        summary = d.get("summary")
        if not isinstance(checks, dict):
            checks = {}
        if not isinstance(summary, dict):
            summary = {}

        stage_ok = all(
            [
                require(gaps, f"R5.{n}:stage", d.get("stage") == f"v0.6D1-R5.{n}"),
                require(
                    gaps,
                    f"R5.{n}:candidate",
                    d.get("scientific_candidate_eligible") is True,
                ),
                require(
                    gaps,
                    f"R5.{n}:checks",
                    all_true_dict(d.get("checks")),
                ),
                require(
                    gaps,
                    f"R5.{n}:cohort",
                    summary.get("target_cohort") == TARGET_COHORT,
                ),
                require(
                    gaps,
                    f"R5.{n}:canonical",
                    summary.get("canonical_state_changed") is False,
                ),
                require(
                    gaps,
                    f"R5.{n}:deep",
                    summary.get("deep_biological_coupling") is False,
                ),
                require(
                    gaps,
                    f"R5.{n}:unique_identity",
                    summary.get("final_human_species_identity_materialized") is False,
                ),
                *[
                    require(gaps, f"R5.{n}:{name}", checks.get(name) is True)
                    for name in explicit[n]
                ],
            ]
        )
        r5_common_pass = r5_common_pass and stage_ok

    r515 = load_json(R515_PATH)
    r515c = r515.get("checks")
    if not isinstance(r515c, dict):
        r515c = {}
    r515_pass = all(
        [
            require(gaps, "R5.15:stage", r515.get("stage") == "v0.6D1-R5.15"),
            require(
                gaps,
                "R5.15:status",
                r515.get("status")
                == "PASS_R515_R334_TO_R339_BULK_LEGACY_RECONCILIATION_CANDIDATE",
            ),
            require(gaps, "R5.15:checks", all_true_dict(r515.get("checks"))),
            require(
                gaps,
                "R5.15:negative",
                r515c.get("negative_results_preserved") is True,
            ),
            require(
                gaps,
                "R5.15:deep",
                r515c.get("deep_coupling_remains_off") is True,
            ),
            require(
                gaps,
                "R5.15:unique_identity",
                r515c.get("unique_human_identity_not_materialized") is True,
            ),
            require(
                gaps,
                "R5.15:names",
                r515c.get("named_culture_language_religion_not_invented") is True,
            ),
            require(
                gaps,
                "R5.15:candidate_not_sealed",
                r515.get("r5_15_status") == "CANDIDATE"
                and r515.get("r5_15_sealed") is False,
            ),
        ]
    )

    legacy: dict[int, dict[str, Any]] = {}
    legacy_common_pass = True
    for n, path in LEGACY_PATHS.items():
        d = load_json(path)
        legacy[n] = d
        summary = d.get("summary")
        if not isinstance(summary, dict):
            summary = {}
        stage_ok = all(
            [
                require(gaps, f"R3.{n}:stage", d.get("stage") == f"v0.6D1-R3.{n}"),
                require(gaps, f"R3.{n}:sealed", d.get("verdict") == "SEALED"),
                require(gaps, f"R3.{n}:checks", all_pass_list(d.get("checks"))),
                require(gaps, f"R3.{n}:failed", d.get("checks_failed") == 0),
                require(
                    gaps,
                    f"R3.{n}:deep",
                    summary.get("deep_biological_coupling") is False,
                ),
                require(
                    gaps,
                    f"R3.{n}:unique_identity",
                    summary.get("unique_human_identity_materialized") is False,
                ),
            ]
        )
        legacy_common_pass = legacy_common_pass and stage_ok

    s34, s35, s36 = (legacy[n]["summary"] for n in (34, 35, 36))
    s37, s38, s39 = (legacy[n]["summary"] for n in (37, 38, 39))
    c12, c13, c14 = (r5[n]["checks"] for n in (12, 13, 14))
    sm13, sm14 = (r5[n]["summary"] for n in (13, 14))

    negative_domains = {
        "agriculture":
            sm13.get("agriculture_materialized") is False
            and sm14.get("agriculture_materialized") is False
            and all(
                s.get("agriculture_materialized") is False
                for s in (s34, s35, s36, s37)
            ),
        "reproductive_control_domestication":
            c14.get(
                "align::observed_no_reproductive_control_or_domestication_stage"
            ) is True,
        "materialized_plant_domesticates":
            all(
                s.get("materialized_functional_plant_domesticates") == []
                for s in (s34, s35, s36)
            )
            and sm14.get("plant_domestication_materialized") is False,
        "village_city_state":
            c12.get("r331_no_language_religion_agriculture_city_state") is True
            and c13.get(
                "r332_no_named_culture_language_religion_city_state_ethnicity"
            ) is True
            and s37.get("village_city_state_materialized") is False
            and s38.get("metallurgy_city_state_materialized") is False,
        "class_hierarchy": s37.get("class_hierarchy_materialized") is False,
        "currency_market": s37.get("currency_market_materialized") is False,
        "named_culture":
            c12.get("r331_no_ethnicity_named_culture") is True
            and c13.get(
                "r332_no_named_culture_language_religion_city_state_ethnicity"
            ) is True
            and s38.get("named_culture_language_religion_materialized") is False,
        "named_language":
            c12.get("r331_no_language_religion_agriculture_city_state") is True
            and s38.get("named_culture_language_religion_materialized") is False
            and s39.get(
                "named_myth_religion_ethnicity_language_materialized"
            ) is False,
        "named_religion_or_myth":
            c12.get("r331_no_language_religion_agriculture_city_state") is True
            and s38.get("named_culture_language_religion_materialized") is False
            and s39.get(
                "named_myth_religion_ethnicity_language_materialized"
            ) is False,
        "ethnicity":
            c12.get("r331_no_ethnicity_named_culture") is True
            and s39.get(
                "named_myth_religion_ethnicity_language_materialized"
            ) is False,
        "unique_human_identity":
            all(
                d["summary"].get("final_human_species_identity_materialized") is False
                for d in r5.values()
            )
            and all(
                d["summary"].get("unique_human_identity_materialized") is False
                for d in legacy.values()
            ),
        "deep_noetic_biological_coupling":
            all(
                d["summary"].get("deep_biological_coupling") is False
                for d in r5.values()
            )
            and all(
                d["summary"].get("deep_biological_coupling") is False
                for d in legacy.values()
            ),
    }
    for name, ok in negative_domains.items():
        require(gaps, f"NEGATIVE:{name}", ok)

    def has_check(stage: int, name: str) -> bool:
        return any(
            isinstance(x, dict)
            and x.get("name") == name
            and x.get("pass") is True
            for x in legacy[stage].get("checks", [])
        )

    human_governance = {
        "retained_lineages_exact_in_r5_8_to_r5_14":
            all(
                d["summary"].get("target_cohort") == TARGET_COHORT
                for d in r5.values()
            ),
        "r3_37_lineage_keys_exact":
            exact_keys(s37.get("resolved_lineage_economic_pathways")),
        "r3_38_lineage_keys_exact":
            exact_keys(s38.get("resolved_cultural_network_pathways")),
        "r3_39_lineage_keys_exact":
            exact_keys(s39.get("resolved_symbolic_language_identity_pathways")),
        "human_label_not_unique_identity_shortcut":
            r5[8]["checks"].get(
                "human_200ka_not_final_unique_species_identity"
            ) is True,
        "unique_identity_absent_through_r5_and_legacy":
            negative_domains["unique_human_identity"],
        "no_lineage_rescale_r3_38_r3_39":
            has_check(38, "no_lineage_rescale")
            and has_check(39, "no_lineage_rescale"),
    }
    for name, ok in human_governance.items():
        require(gaps, f"HUMAN:{name}", ok)

    negative_pass = all(negative_domains.values())
    human_pass = all(human_governance.values())
    passed = (
        prerequisite_pass
        and r5_common_pass
        and r515_pass
        and legacy_common_pass
        and negative_pass
        and human_pass
        and not gaps
    )

    return {
        "schema": "ARCANA_R5_16_NEGATIVE_RESULT_PRESERVATION_V1",
        "stage": "v0.6D1-R5.16",
        "subphase": "R5.16-D",
        "repository": "siegmound/ARCANA_WORLD",
        "branch": branch,
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "prerequisite_path": PREREQUISITE_PATH.as_posix(),
        "prerequisite_pass": prerequisite_pass,
        "method": {
            "explicit_negative_evidence_required": True,
            "absence_not_inferred_from_silence": True,
            "r5_8_to_r5_14_completion_artifacts_directly_checked": True,
            "r5_15_pass2_negative_governance_checks_directly_checked": True,
            "r3_34_to_r3_39_final_seal_semantics_directly_checked": True,
            "fresh_rerun_required": False,
            "external_engine_execution": False,
            "automatic_repair": False,
            "canonical_mutation": False,
            "seal_action": False,
            "numerical_replay_final_adjudication": False,
            "external_engine_governance_final_adjudication": False,
        },
        "r5_stages_verified": 7 if r5_common_pass else 0,
        "r5_15_negative_governance_verified": r515_pass,
        "legacy_sealed_stages_verified": 6 if legacy_common_pass else 0,
        "negative_domains": negative_domains,
        "negative_results_preserved": negative_pass,
        "human_lineage_governance": human_governance,
        "human_lineage_governance_preserved": human_pass,
        "retained_lineages": TARGET_COHORT,
        "open_negative_or_governance_gap_count": len(gaps),
        "open_negative_or_governance_gaps": gaps,
        "status": (
            "PASS_R516_NEGATIVE_RESULT_AND_HUMAN_GOVERNANCE_AUDIT"
            if passed
            else "BLOCKED_R516_NEGATIVE_RESULT_AND_HUMAN_GOVERNANCE_AUDIT"
        ),
        "next_if_pass":
            "R5.16-E_NUMERICAL_REPLAY_AND_EXTERNAL_ENGINE_GOVERNANCE_AUDIT",
    }


def blocked(branch: str, head: str, gaps: list[str]) -> dict[str, Any]:
    return {
        "schema": "ARCANA_R5_16_NEGATIVE_RESULT_PRESERVATION_V1",
        "stage": "v0.6D1-R5.16",
        "subphase": "R5.16-D",
        "repository": "siegmound/ARCANA_WORLD",
        "branch": branch,
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "negative_results_preserved": False,
        "human_lineage_governance_preserved": False,
        "open_negative_or_governance_gap_count": len(gaps),
        "open_negative_or_governance_gaps": gaps,
        "status": "BLOCKED_R516_NEGATIVE_RESULT_AND_HUMAN_GOVERNANCE_AUDIT",
        "next_if_pass":
            "R5.16-E_NUMERICAL_REPLAY_AND_EXTERNAL_ENGINE_GOVERNANCE_AUDIT",
    }


def main() -> None:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    os.chdir(root)
    branch = run_git("rev-parse", "--abbrev-ref", "HEAD")
    head = run_git("rev-parse", "HEAD")

    if branch != EXPECTED_BRANCH:
        raise SystemExit(f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}")

    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", EXPECTED_SOURCE_COMMIT, head],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if ancestry.returncode != 0:
        raise SystemExit(
            "R5.16-D requires the completed R5.16-C snapshot as an ancestor.\n"
            f"Required ancestor: {EXPECTED_SOURCE_COMMIT}\n"
            f"Found HEAD:        {head}"
        )

    protected_inputs = [
        PREREQUISITE_PATH.as_posix(),
        R515_PATH.as_posix(),
        *[p.as_posix() for p in R5_PATHS.values()],
        *[p.as_posix() for p in LEGACY_PATHS.values()],
    ]
    drift = subprocess.run(
        ["git", "diff", "--name-only", EXPECTED_SOURCE_COMMIT, "HEAD", "--", *protected_inputs],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if drift.returncode != 0:
        raise SystemExit(f"git diff input-drift check failed:\n{drift.stderr}")
    if drift.stdout.strip():
        raise SystemExit(
            "R5.16-D protected inputs changed after the R5.16-C snapshot:\n"
            + drift.stdout.strip()
        )

    dirty = run_git("status", "--porcelain", "--untracked-files=no")
    if dirty:
        raise SystemExit(
            "Tracked working tree is not clean before R5.16-D:\n" + dirty
        )

    output = build_audit(root, branch, head)
    OUTPUT_PATH.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(f"WROTE {OUTPUT_PATH}")
    print(f"SOURCE_COMMIT = {EXPECTED_SOURCE_COMMIT}")
    print(f"NEGATIVE_RESULTS_PRESERVED = {output.get('negative_results_preserved')}")
    print(
        "HUMAN_LINEAGE_GOVERNANCE_PRESERVED = "
        f"{output.get('human_lineage_governance_preserved')}"
    )
    print(
        "OPEN_NEGATIVE_OR_GOVERNANCE_GAPS = "
        f"{output.get('open_negative_or_governance_gap_count')}"
    )
    print(f"STATUS = {output.get('status')}")

    if output.get("status") != "PASS_R516_NEGATIVE_RESULT_AND_HUMAN_GOVERNANCE_AUDIT":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
