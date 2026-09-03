from __future__ import annotations

import argparse
import json
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np

ROOT0 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT0 / "src"))

from arcana_worldsim.late_cenozoic.production_interface import D3LateCenozoicSubstrateAdapter
from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
from arcana_worldsim.scientific_engines import r319_phase_aware_transport_closure as r319

STAGE = "v0.6D1-R3.19"
CANONICAL_VERDICT = (
    "PASS_CANONICAL_R319_125KA_TO_0_H0_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY__"
    "0KA_NATURAL_CONTROL_BIOLOGY_CHECKPOINT_READY"
)
SEALED_VERDICT = (
    "PASS_R319_CANONICAL_125KA_TO_0_H0_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY__"
    "0KA_NATURAL_CONTROL_BIOLOGY_BOUNDARY_SEALED"
)
EXPECTED_JSON_SHA256 = "658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71"
EXPECTED_NPZ_SHA256 = "f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406"
EXPECTED_SPECIES = 134
EXPECTED_COMPONENTS = 295
EXPECTED_POP = 1217.2506240828814
EXPECTED_SHADOW_POP = 1217.241447649682
EXPECTED_PEAK_Q = 0.047601695825828454
EXPECTED_Q_CEILING = 0.08
EXPECTED_PHASE_DIVERGENCE = 1.5816467428221057


def hfile(path: Path) -> str:
    h = sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def f_eq(a: Any, b: float, atol: float = 1e-12) -> bool:
    try:
        return abs(float(a) - float(b)) <= atol
    except Exception:
        return False


def metadata_rows(root: Path) -> list[dict[str, Any]]:
    data = json.loads((root / "references/v0_6D1_R3/D1_SPECIES_METADATA.json").read_text(encoding="utf-8"))
    return data["species"] if isinstance(data, dict) and "species" in data else data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seal-out", type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve(); run = args.run_dir.resolve(); out = args.out.resolve(); seal_out = args.seal_out.resolve()

    stem = "WORLD1_H0_0KA_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY_CHECKPOINT_v0_6D1_R3_19"
    jp = run / f"{stem}.json"
    npzp = run / f"{stem}.npz"
    sump = run / "R3_19_H0_PRESENT_BIOLOGY_CLOSURE_SUMMARY.json"

    checks: list[dict[str, Any]] = []
    def ck(name: str, passed: bool, actual: Any = None, expected: Any = None) -> None:
        checks.append({"name": name, "pass": bool(passed), "actual": actual, "expected": expected})

    for label, path in (("checkpoint_json", jp), ("checkpoint_npz", npzp), ("summary", sump)):
        ck(f"{label}_exists", path.is_file(), str(path), "file")
    if not all(p.is_file() for p in (jp, npzp, sump)):
        failed = [x for x in checks if not x["pass"]]
        audit = {"schema":"ARCANA_R319_FORMAL_SEALED_AUDIT_V1","stage":STAGE,"verdict":"FAIL_R319_SEALED_AUDIT","checks":f"{len(checks)-len(failed)}/{len(checks)}","failed":failed,"check_rows":checks}
        out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(audit, indent=2), encoding="utf-8")
        print(json.dumps({"verdict":audit["verdict"],"checks":audit["checks"],"audit":str(out)}, indent=2)); return 1

    summary = json.loads(sump.read_text(encoding="utf-8"))
    meta = json.loads(jp.read_text(encoding="utf-8"))
    json_sha = hfile(jp); npz_sha = hfile(npzp); sum_sha = hfile(sump)

    ck("checkpoint_json_sha_exact", json_sha == EXPECTED_JSON_SHA256, json_sha, EXPECTED_JSON_SHA256)
    ck("checkpoint_npz_sha_exact", npz_sha == EXPECTED_NPZ_SHA256, npz_sha, EXPECTED_NPZ_SHA256)
    ck("summary_stage", summary.get("stage") == STAGE, summary.get("stage"), STAGE)
    ck("summary_verdict", summary.get("verdict") == CANONICAL_VERDICT, summary.get("verdict"), CANONICAL_VERDICT)
    ck("summary_biology_steps_1", summary.get("biology_steps") == 1, summary.get("biology_steps"), 1)
    ck("summary_biology_age_0", f_eq(summary.get("biology_age_ma"), 0.0), summary.get("biology_age_ma"), 0.0)
    ck("summary_species", summary.get("species") == EXPECTED_SPECIES, summary.get("species"), EXPECTED_SPECIES)
    ck("summary_components", summary.get("components") == EXPECTED_COMPONENTS, summary.get("components"), EXPECTED_COMPONENTS)
    ck("summary_population", f_eq(summary.get("population"), EXPECTED_POP, 1e-9), summary.get("population"), EXPECTED_POP)
    ck("summary_peak_q", f_eq(summary.get("peak_q"), EXPECTED_PEAK_Q, 1e-15), summary.get("peak_q"), EXPECTED_PEAK_Q)
    ck("summary_peak_unclipped_q", f_eq(summary.get("peak_unclipped_q"), EXPECTED_PEAK_Q, 1e-15), summary.get("peak_unclipped_q"), EXPECTED_PEAK_Q)
    ck("summary_clipping_zero", summary.get("clipping_steps") == 0, summary.get("clipping_steps"), 0)
    ck("summary_transport_substeps_2", summary.get("transport_substeps") == 2, summary.get("transport_substeps"), 2)
    ck("summary_transport_phase_years", summary.get("transport_phase_years") == [62500.0, 62500.0], summary.get("transport_phase_years"), [62500.0,62500.0])
    ck("summary_phase_aware", summary.get("phase_aware_transport") is True, summary.get("phase_aware_transport"), True)
    ck("summary_constant_forcing_bit_exact", summary.get("constant_forcing_equivalence_bit_exact") is True, summary.get("constant_forcing_equivalence_bit_exact"), True)
    ck("summary_shadow_differs", summary.get("single_environment_shadow_exactly_equal") is False, summary.get("single_environment_shadow_exactly_equal"), False)
    ck("summary_shadow_population", f_eq(summary.get("single_environment_shadow_population"), EXPECTED_SHADOW_POP, 1e-9), summary.get("single_environment_shadow_population"), EXPECTED_SHADOW_POP)
    ck("summary_endpoint_inaccessible_zero", f_eq(summary.get("exact_0ka_inaccessible_population_mass"), 0.0, 0.0), summary.get("exact_0ka_inaccessible_population_mass"), 0.0)
    ck("summary_serialization_identity", summary.get("serialization_identity") is True, summary.get("serialization_identity"), True)
    ck("summary_deep_off", summary.get("deep_biological_coupling") is False, summary.get("deep_biological_coupling"), False)
    ck("summary_science_unchanged", summary.get("scientific_parameter_changes") is False, summary.get("scientific_parameter_changes"), False)
    ck("summary_human_target_off", summary.get("human_lineage_target_used") is False, summary.get("human_lineage_target_used"), False)
    delta = summary.get("event_counts_delta", {})
    expected_delta = {
        "paleogeographic_support_loss_remap": 1,
        "deme_coalescence": 0,
        "deme_fission": 0,
        "speciation": 0,
        "ordinary_background_extinction": 0,
        "CHA1_species_extinction": 0,
        "CHA1_high_resolution_event_bridge_complete": 0,
        "post_CHA1_ordinary_lifecycle_thaw": 0,
    }
    ck("summary_event_delta_exact", delta == expected_delta, delta, expected_delta)

    ck("checkpoint_schema", meta.get("schema") == r319.SCHEMA, meta.get("schema"), r319.SCHEMA)
    ck("checkpoint_stage", meta.get("stage") == STAGE, meta.get("stage"), STAGE)
    ck("checkpoint_age_0", f_eq(meta.get("age_ma"), 0.0), meta.get("age_ma"), 0.0)
    gov = meta.get("governance", {})
    ck("gov_biology_125k", f_eq(gov.get("biology_cadence_years"),125000.0,1e-9), gov.get("biology_cadence_years"),125000.0)
    ck("gov_biology_steps_1", gov.get("biology_steps") == 1, gov.get("biology_steps"),1)
    ck("gov_transport_62500", f_eq(gov.get("transport_cadence_years"),62500.0,1e-9), gov.get("transport_cadence_years"),62500.0)
    ck("gov_transport_substeps_2", gov.get("transport_substeps") == 2, gov.get("transport_substeps"),2)
    ck("gov_phase_aware", gov.get("phase_aware_transport") is True, gov.get("phase_aware_transport"),True)
    for key in ("gene_flow_step_cadence_changed","lifecycle_gate_cadence_changed","adaptive_clock_used_as_biology_timestep","deep_biological_coupling","scientific_parameters_changed","human_lineage_target_used"):
        ck(f"gov_false::{key}", gov.get(key) is False, gov.get(key), False)

    # Canonical checkpoint rehydration and direct invariant audit.
    canonical = r319.load_checkpoint(jp)
    md = metadata_rows(root)
    cfg = r319.R319Config()
    inv = r319.invariant_report(canonical, md, cfg)
    ck("canonical_age_0", f_eq(canonical.age_ma,0.0), canonical.age_ma,0.0)
    ck("canonical_species", len(set(canonical.current_species)) == EXPECTED_SPECIES, len(set(canonical.current_species)),EXPECTED_SPECIES)
    ck("canonical_components", len(canonical.component_ids) == EXPECTED_COMPONENTS, len(canonical.component_ids),EXPECTED_COMPONENTS)
    ck("canonical_population", f_eq(float(canonical.pop.sum()),EXPECTED_POP,1e-9), float(canonical.pop.sum()),EXPECTED_POP)
    ck("canonical_population_nonnegative", float(inv["population_min"]) >= -1e-15, inv["population_min"], ">=0")
    ck("canonical_population_inaccessible_zero", f_eq(inv["population_on_inaccessible_cells"],0.0,0.0), inv["population_on_inaccessible_cells"],0.0)
    ck("canonical_q_under_ceiling", float(inv["q_max"]) <= EXPECTED_Q_CEILING + 1e-12, inv["q_max"], f"<={EXPECTED_Q_CEILING}")
    ck("canonical_q_matches", f_eq(inv["q_max"],EXPECTED_PEAK_Q,1e-15), inv["q_max"],EXPECTED_PEAK_Q)
    ck("canonical_s_symmetric", f_eq(inv["s_symmetry_max_abs"],0.0,0.0), inv["s_symmetry_max_abs"],0.0)
    ck("canonical_s_diagonal_zero", f_eq(inv["s_diagonal_max_abs"],0.0,0.0), inv["s_diagonal_max_abs"],0.0)
    ck("canonical_s_nonnegative", float(inv["s_min"]) >= -1e-15, inv["s_min"], ">=0")

    # Parent authority + full independent production replay.
    parent = r319.validate_parent_r318_authority(root)
    st = parent["state"]; a1 = parent["a1"]; c2 = parent["c2"]; bundle = parent["bundle"]
    ck("parent_age_125ka", f_eq(st.age_ma,.125), st.age_ma,.125)
    ck("parent_species_134", len(set(st.current_species)) == 134, len(set(st.current_species)),134)
    ck("parent_components_295", len(st.component_ids) == 295, len(st.component_ids),295)
    ck("parent_population", f_eq(float(st.pop.sum()),1217.8946033288662,1e-9), float(st.pop.sum()),1217.8946033288662)
    macro_env, _phase_envs = r319.environments_from_r318_bundle(bundle)
    eq = r319.constant_forcing_equivalence(st,a1,md,macro_env,cfg,r319.END_AGE_MA)
    ck("replay_constant_forcing_gate", eq.get("passed") is True, eq.get("passed"),True)
    ck("replay_constant_state_bit_exact", eq.get("state_bit_exact") is True, eq.get("state_bit_exact"),True)
    ck("replay_constant_records_exact", eq.get("records_exact") is True, eq.get("records_exact"),True)
    ck("replay_constant_events_exact", eq.get("events_exact") is True, eq.get("events_exact"),True)
    ck("replay_constant_snapshots_exact", eq.get("snapshots_exact") is True, eq.get("snapshots_exact"),True)

    endpoint0 = D3LateCenozoicSubstrateAdapter(a1,c2).state_at_age(0.0)
    endpoint_access = np.asarray(endpoint0["accessible"], bool)
    replay, records, coupling = r319.run_phase_aware_macrostep(st,a1,md,bundle,cfg,endpoint_accessible=endpoint_access)
    cmp = r38.compare_runtime_states(canonical,replay,atol=0.0)
    ck("independent_replay_state_bit_exact", cmp.get("equivalent") is True, cmp.get("equivalent"),True)
    ck("independent_replay_records_1", len(records) == 1, len(records),1)
    ck("independent_replay_transport_trace_2", len(coupling.get("transport_trace",[])) == 2, len(coupling.get("transport_trace",[])),2)
    ck("independent_replay_transport_dt", all(f_eq(x.get("dt_years"),62500.0,1e-9) for x in coupling.get("transport_trace",[])), [x.get("dt_years") for x in coupling.get("transport_trace",[])], [62500.0,62500.0])
    rec = coupling.get("endpoint_support_reconciliation", {})
    ck("endpoint_reconciliation_applied", rec.get("applied") is True, rec.get("applied"),True)
    ck("endpoint_reconciliation_mass_positive", float(rec.get("remapped_population_mass",0.0)) > 0.0, rec.get("remapped_population_mass"), ">0")
    ck("endpoint_reconciliation_after_zero", f_eq(rec.get("endpoint_inaccessible_population_after"),0.0,0.0), rec.get("endpoint_inaccessible_population_after"),0.0)
    replay_delta = r319.delta_event_counts(st,replay)
    ck("independent_replay_event_delta_exact", replay_delta == expected_delta, replay_delta, expected_delta)
    replay_inv = r319.invariant_report(replay,md,cfg)
    ck("independent_replay_exact_endpoint_support", f_eq(float(np.asarray(replay.pop,float)[:,~endpoint_access].sum()),0.0,0.0), float(np.asarray(replay.pop,float)[:,~endpoint_access].sum()),0.0)
    ck("independent_replay_q_under_ceiling", float(replay_inv["q_max"]) <= EXPECTED_Q_CEILING + 1e-12, replay_inv["q_max"],f"<={EXPECTED_Q_CEILING}")
    ck("independent_replay_no_clipping", all(int(r.get("clipping_count",0)) == 0 for r in records), [r.get("clipping_count",0) for r in records], [0])

    # Verify canonical checkpoint itself round-trips bit-exactly from disk.
    canonical2 = r319.load_checkpoint(jp)
    ser = r38.compare_runtime_states(canonical,canonical2,atol=0.0)
    ck("checkpoint_roundtrip_bit_exact", ser.get("equivalent") is True, ser.get("equivalent"),True)

    failed = [x for x in checks if not x["pass"]]
    verdict = SEALED_VERDICT if not failed else "FAIL_R319_SEALED_AUDIT"
    audit = {
        "schema":"ARCANA_R319_FORMAL_SEALED_AUDIT_V1","stage":STAGE,"verdict":verdict,
        "checks":f"{len(checks)-len(failed)}/{len(checks)}","failed":failed,
        "decision":"H0_NATURAL_CONTROL_210MA_TO_0KA_BIOLOGY_CLOSED__PHASE_AWARE_TWO_TRANSPORT_SUBSTEPS_AND_EXACT_ENDPOINT_TOPOLOGY_SEALED",
        "boundary":{
            "biology_age_ma":0.0,"species":EXPECTED_SPECIES,"components":EXPECTED_COMPONENTS,"population":EXPECTED_POP,
            "biology_cadence_years":125000.0,"transport_cadence_years":62500.0,"transport_substeps":2,
            "phase_aware_transport":True,"constant_forcing_equivalence_bit_exact":True,
            "endpoint_support_reconciliation_event_count":1,"exact_0ka_inaccessible_population_mass":0.0,
            "peak_q":EXPECTED_PEAK_Q,"q_ceiling":EXPECTED_Q_CEILING,"deep_biological_coupling":False,
        },
        "canonical_artifacts":{
            "checkpoint_json":str(jp),"checkpoint_json_sha256":json_sha,
            "checkpoint_npz":str(npzp),"checkpoint_npz_sha256":npz_sha,
            "summary":str(sump),"summary_sha256":sum_sha,
        },
        "parent_authority":{
            "stage":"v0.6D1-R3.18_SEALED","r318_seal_sha256":parent["r318_seal_sha256"],
            "r318_audit_sha256":parent["r318_audit_sha256"],"r318_summary_sha256":parent["r318_summary_sha256"],
            "r318_envelope_sha256":parent["r318_envelope_sha256"],"r318_bundle_sha256":parent["r318_bundle_sha256"],
        },
        "independent_replay":{
            "enabled":True,"state_bit_exact":bool(cmp.get("equivalent")),
            "constant_forcing_r38_equivalence":bool(eq.get("passed")),
            "endpoint_support_reconciliation_applied":bool(rec.get("applied")),
            "endpoint_support_reconciliation_mass":float(rec.get("remapped_population_mass",0.0)),
            "exact_0ka_inaccessible_population_mass":float(np.asarray(replay.pop,float)[:,~endpoint_access].sum()),
        },
        "scientific_parameter_changes":False,"biology_cadence_changes":False,"transport_cadence_changes":False,
        "gene_flow_cadence_changes":False,"lifecycle_gate_cadence_changes":False,"deep_biological_coupling":False,
        "check_rows":checks,
    }
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(audit,indent=2),encoding="utf-8")
    if not failed:
        seal = {
            "schema":"ARCANA_R319_SEAL_SUMMARY_V1","stage":STAGE,"verdict":SEALED_VERDICT,
            "formal_audit":str(out),"formal_audit_sha256":hfile(out),"formal_audit_checks":audit["checks"],
            "boundary":audit["boundary"],"canonical_artifacts":audit["canonical_artifacts"],
            "parent_authority":audit["parent_authority"],"independent_replay":audit["independent_replay"],
            "governance":{
                "h0_natural_control_biology_210ma_to_0ka_closed":True,
                "phase_aware_transport_sealed":True,"exact_endpoint_support_reconciliation_sealed":True,
                "constant_forcing_r38_equivalence_required":True,
                "biology_cadence_changed":False,"transport_cadence_changed":False,"gene_flow_cadence_changed":False,
                "lifecycle_gate_cadence_changed":False,"deep_biological_coupling":False,"scientific_parameter_changes":False,
                "human_lineage_target_used":False,
            },
            "next":"v0.6D1-R3.20 — H0 Natural-Control Final Closure, Present Lineage Registry & Functional-Phenotype Fork Readiness",
        }
        seal_out.write_text(json.dumps(seal,indent=2),encoding="utf-8")
    print(json.dumps({"verdict":verdict,"checks":audit["checks"],"audit":str(out),"seal":str(seal_out) if not failed else None},indent=2))
    try:
        if hasattr(a1,"close"): a1.close()
    except Exception:
        pass
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
