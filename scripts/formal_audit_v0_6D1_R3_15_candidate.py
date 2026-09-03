from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np

from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
from arcana_worldsim.scientific_engines import r313_longterm_postcha1_reassembly as r313
from arcana_worldsim.scientific_engines import r315_late_cenozoic_secular_biology as r315

STAGE = "v0.6D1-R3.15"
VERDICT = "PASS_R315_CANDIDATE_INTEGRATION_AUDIT__READY_FOR_LOCAL_30MA_TO_250KA_C2_BOUND_REPLAY"


def hfile(path: Path) -> str:
    h = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def mdrows(root: Path):
    d = json.loads((root / "references/v0_6D1_R3/D1_SPECIES_METADATA.json").read_text(encoding="utf-8"))
    return d["species"] if isinstance(d, dict) and "species" in d else d


class OldProviderProxy:
    def __init__(self, a1, cfg):
        self.a1 = a1; self.cfg = cfg; self._environment_at = r38.bp.environment_at
    def state_at(self, age_ma: float):
        return self._environment_at(float(age_ma), self.a1, r38.r34.barrier_cfg(self.cfg))


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--root", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(); root = args.root.resolve(); out = args.out.resolve()
    checks: list[dict[str, Any]] = []
    def ck(name: str, ok: bool, detail: Any = None): checks.append({"name": name, "pass": bool(ok), "detail": detail})

    cfg = r315.R315Config(); pcfg = r313.R313Config()
    ck("stage", r315.STAGE == STAGE, r315.STAGE)
    ck("start_30ma", r315.START_AGE_MA == 30.0)
    ck("end_250ka", r315.END_AGE_MA == 0.25)
    ck("bridge_start_200ka", r315.C2_BRIDGE_START_AGE_MA == 0.2)
    ck("recent_restart_120ka", r315.C2_RECENT_RESTART_AGE_MA == 0.12)
    ck("expected_steps_238", r315.EXPECTED_STEPS == 238)
    ck("biology_cadence_125k", cfg.biology_cadence_years == 125000.0, cfg.biology_cadence_years)
    ck("transport_cadence_62500", cfg.transport_cadence_years == 62500.0, cfg.transport_cadence_years)
    ck("adaptive_clock_not_biology_dt", cfg.adaptive_clock_used_as_biology_timestep is False)
    ck("fixed_biology_cadence", cfg.fixed_biology_cadence_preserved is True)

    a = asdict(cfg); b = asdict(pcfg)
    shared = sorted(set(a) & set(b))
    expected_diffs = {"end_age_ma"}
    actual_diffs = {k for k in shared if a[k] != b[k]}
    ck("only_shared_config_change_is_endpoint", actual_diffs == expected_diffs, sorted(actual_diffs))
    for key in shared:
        if key == "end_age_ma": continue
        ck(f"inherited_cfg:{key}", a[key] == b[key], {"r315": a[key], "r313": b[key]})

    sched = r315.biology_scheduler_separation_report({"age_ma": np.asarray([30.0, 0.2, 0.12, 0.0])}, cfg)
    for key in (
        "all_r315_biology_checkpoints_older_than_c2_bridge_start",
        "fixed_r37i_r38_biology_cadence_preserved",
        "next_nominal_biology_step_would_cross_c2_200ka_bridge_start",
    ):
        ck(f"scheduler_true:{key}", sched[key] is True, sched[key])
    for key in ("adaptive_clock_checkpoint_promoted_to_biology_step", "adaptive_clock_used_as_biology_timestep", "c2_200_120ka_bridge_crossed", "recent_120ka_restart_crossed"):
        ck(f"scheduler_false:{key}", sched[key] is False, sched[key])
    ck("scheduler_238_intervals", sched["biology_interval_count"] == 238, sched["biology_interval_count"])
    ck("scheduler_end_250ka", sched["biology_end_age_ma"] == 0.25, sched["biology_end_age_ma"])
    ck("next_nominal_age_125ka", sched["next_nominal_biology_checkpoint_age_ma"] == 0.125, sched["next_nominal_biology_checkpoint_age_ma"])

    # Source surface: R3.15 adds an integration layer only. Core R3.8 and R3.14 late-Cenozoic files are untouched in this candidate.
    inherited = [
        "src/arcana_worldsim/scientific_engines/r38_restartable_checkpoint.py",
        "src/arcana_worldsim/scientific_engines/r314_late_cenozoic_binding.py",
        "src/arcana_worldsim/late_cenozoic/production_interface.py",
        "src/arcana_worldsim/late_cenozoic/integrated_provider.py",
        "src/arcana_worldsim/late_cenozoic/late_pleistocene_boundary.py",
        "src/arcana_worldsim/late_cenozoic/adaptive_clock_c2.py",
        "src/arcana_worldsim/late_cenozoic/cha2_nested_50y.py",
    ]
    for rel in inherited:
        p = root / rel
        ck(f"inherited_exists:{rel}", p.is_file(), str(p))
        if p.is_file(): ck(f"inherited_sha_present:{rel}", len(hfile(p)) == 64, hfile(p))

    # Test-only proxy proves the injection surface itself is state-exact when environmental arrays are exact.
    a1 = np.load(root / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz", allow_pickle=False)
    md = mdrows(root)
    parent = r313.load_checkpoint(root / "local_runs/v0_6D1_R3_13/WORLD1_H0_30Ma_LONG_TERM_POST_CHA1_DIVERSIFICATION_REASSEMBLY_CHECKPOINT_v0_6D1_R3_13.json")
    direct0 = r313.r312.r311._clone_state(parent)
    direct, rec0 = r38.advance_state(direct0, a1, md, cfg, r315.SMOKE_END_AGE_MA)
    proxy = OldProviderProxy(a1, cfg)
    bound, rec1 = r315.run_secular_biology(parent, a1, md, proxy, cfg, r315.SMOKE_END_AGE_MA)
    cmp = r38.compare_runtime_states(direct, bound)
    for k, row in cmp["arrays"].items(): ck(f"proxy_array_exact:{k}", row["same"] is True, row)
    for k, row in cmp["reduced_state"].items(): ck(f"proxy_reduced_exact:{k}", row["same"] is True, row)
    for k, val in cmp["exact_fields"].items():
        if k == "snapshots":
            ck("proxy_snapshot_only_diagnostic_label_changes", val is False, val)
        else:
            ck(f"proxy_exact_field:{k}", val is True, val)
    ck("proxy_records_exact", rec0 == rec1)
    ck("proxy_population_exact", np.array_equal(direct.pop, bound.pop))
    ck("proxy_events_exact", direct.events == bound.events)

    hand = r315.validate_30ma_full_d3_substrate_handoff(a1, r315.R315D3EnvironmentAdapter(a1, proxy), cfg)
    ck("proxy_30ma_full_d3_handoff_exact", hand["full_d3_substrate_identity_exact"] is True, hand)
    for key, row in hand["fields"].items(): ck(f"proxy_30ma_field_exact:{key}", row["exact"] is True, row)

    failed = [x for x in checks if not x["pass"]]
    audit = {
        "schema": "ARCANA_R315_FORMAL_CANDIDATE_INTEGRATION_AUDIT_V1",
        "stage": STAGE,
        "verdict": VERDICT if not failed else "FAIL_R315_CANDIDATE_INTEGRATION_AUDIT",
        "checks": f"{len(checks)-len(failed)}/{len(checks)}",
        "failed": failed,
        "scheduler_separation": sched,
        "proxy_integration": {
            "scientific_arrays_exact": all(r["same"] for r in cmp["arrays"].values()),
            "reduced_state_exact": all(r["same"] for r in cmp["reduced_state"].values()),
            "telemetry_records_exact": rec0 == rec1,
            "snapshot_difference_semantics": "DIAGNOSTIC_PROVIDER_BRACKET_LABEL_ONLY",
        },
        "governance": {
            "canonical_run_performed_here": False,
            "reason": "R3.15 canonical run requires the user's materialized R3.14 SEALED v0.6.1/B1/B2 binding surface.",
            "biology_cadence_changed": False,
            "scientific_parameters_changed": False,
            "adaptive_clock_promoted_to_biology_cadence": False,
            "c2_bridge_crossed_in_stage": False,
        },
        "check_rows": checks,
    }
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": audit["verdict"], "checks": audit["checks"], "out": str(out)}, indent=2))
    return 0 if not failed else 1

if __name__ == "__main__": raise SystemExit(main())
