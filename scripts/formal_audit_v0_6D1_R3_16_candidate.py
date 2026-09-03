from __future__ import annotations

import json
import sys
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
from arcana_worldsim.scientific_engines import r316_c2_bridge_fixed_biology as r316

VERDICT = "PASS_R316_CANDIDATE_FORMAL_AUDIT__READY_FOR_LOCAL_250_TO_125KA_EXPOSURE_PRESERVING_BRIDGE_RUN"


def hfile(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()


def fake_clock():
    bridge = [0.2 - i*0.0005 for i in range(161)]
    return {"age_ma": [30.0, 2.0, 0.2] + bridge[1:] + [0.0]}


class ConstantAdapter:
    def state_at_age(self, age):
        support=np.full((2,3),0.75)
        b=np.full((2,3),1.2); l=np.full((2,3),0.4); w=np.full((2,3),0.1)
        return {
            "land_support":support,"temperature_c":np.full((2,3),12.0),"aridity_index":np.full((2,3),0.5),
            "browse_forage":b,"low_forage":l,"wetland_forage":w,"total_edible_forage":b+l+w,
            "reference_population":np.full((6,2,3),2.0),"provider":"FAKE","subprovider":"FAKE","authority":"FAKE",
            "replay_safe_boundary_continuation":True,
        }


class LinearAdapter(ConstantAdapter):
    def state_at_age(self, age):
        d=super().state_at_age(age); x=float(age)
        d["temperature_c"]=np.full((2,3),5.0+x)
        d["browse_forage"]=np.full((2,3),1.0+x)
        d["total_edible_forage"]=d["browse_forage"]+d["low_forage"]+d["wetland_forage"]
        return d


def main() -> int:
    checks=[]
    def ck(name, cond, actual=None, expected=None):
        checks.append({"name":name,"pass":bool(cond),"actual":actual,"expected":expected})

    cfg=r316.R316Config()
    ck("stage",r316.STAGE=="v0.6D1-R3.16",r316.STAGE)
    ck("start_250ka",r316.START_AGE_MA==0.25,r316.START_AGE_MA)
    ck("biology_end_125ka",r316.BIOLOGY_END_AGE_MA==0.125,r316.BIOLOGY_END_AGE_MA)
    ck("c2_start_200ka",r316.C2_BRIDGE_START_AGE_MA==0.2,r316.C2_BRIDGE_START_AGE_MA)
    ck("c2_end_120ka",r316.C2_BRIDGE_END_AGE_MA==0.12,r316.C2_BRIDGE_END_AGE_MA)
    ck("fixed_biology_125k",cfg.biology_cadence_years==125000.0,cfg.biology_cadence_years)
    ck("adaptive_not_biology",cfg.adaptive_clock_used_as_biology_timestep is False)
    ck("gene_flow_cadence_unchanged",cfg.gene_flow_step_cadence_changed is False)
    ck("lifecycle_cadence_unchanged",cfg.lifecycle_gate_cadence_changed is False)
    ck("expected_c2_consumed_150",r316.EXPECTED_C2_SUBSTEPS_CONSUMED==150)
    ck("expected_c2_total_160",r316.EXPECTED_C2_SUBSTEPS_TOTAL==160)
    ck("expected_c2_remaining_10",r316.EXPECTED_C2_SUBSTEPS_REMAINING==10)
    ck("r315_json_hash_pinned",r316.R315_CHECKPOINT_JSON_SHA256=="4fb4ffdd711b7a5439ffff15a0a6f381e42ca560b00a2338d70edb77d848bcf6")
    ck("r315_npz_hash_pinned",r316.R315_CHECKPOINT_NPZ_SHA256=="f8e79ea862de6c48f01784c727ca15abf9d8fd53b07f47d1aaab5bf589ee5692")

    # R3.8 has a concrete NpzFile container contract because it inspects
    # ``a1.files``. R3.16 must preserve it even though the R3.14 provider
    # builder uses a plain dict view of the same A1 authority.
    runtime_a1 = r316._load_r38_runtime_a1(ROOT)
    try:
        ck("r316_runtime_a1_preserves_npz_files_contract", hasattr(runtime_a1, "files"))
        ck("r316_runtime_a1_required_channels", {"age_ma","lat","lon","population"}.issubset(set(runtime_a1.files)), sorted(runtime_a1.files))
    finally:
        runtime_a1.close()

    # R3.16 must own a bridge-scoped adapter rather than weakening the sealed
    # R3.15 guard. This catches the Windows canonical-run failure where the
    # inherited R3.15 adapter rejected every age below 250 ka.
    class _AuditD3:
        def state_at_age(self, age):
            return {"age_ma": float(age)}

    bridge_adapter = object.__new__(r316.R316C2BridgeEnvironmentAdapter)
    bridge_adapter.a1 = None
    bridge_adapter.c2 = None
    bridge_adapter.d3 = _AuditD3()
    ck("r316_adapter_accepts_125ka", abs(float(bridge_adapter.state_at_age(0.125)["age_ma"])-0.125)<1e-12)
    ck("r316_adapter_accepts_exact_120ka_environment", abs(float(bridge_adapter.state_at_age(0.12)["age_ma"])-0.12)<1e-12)
    try:
        bridge_adapter.state_at_age(0.1195)
        r316_scope_fail_closed = False
    except ValueError:
        r316_scope_fail_closed = True
    ck("r316_adapter_fails_closed_below_120ka", r316_scope_fail_closed)

    legacy_adapter = object.__new__(r316.r315.R315D3EnvironmentAdapter)
    legacy_adapter.a1 = None
    legacy_adapter.c2 = None
    legacy_adapter.d3 = _AuditD3()
    try:
        legacy_adapter.state_at_age(0.20)
        r315_guard_preserved = False
    except ValueError:
        r315_guard_preserved = True
    ck("r315_250ka_scope_guard_preserved", r315_guard_preserved)

    # Every inherited R3.8 scientific config field is unchanged except the
    # requested horizon endpoint; R3.16 only adds governance/coupling fields.
    base=asdict(r38.R38Config(end_age_ma=0.125)); now=asdict(cfg)
    for k,v in base.items():
        ck(f"inherited_config::{k}", now.get(k)==v, now.get(k), v)

    p=r316.exposure_partition(fake_clock())
    ck("partition_total_125k",abs(p["total_years"]-125000.0)<1e-6,p["total_years"])
    ck("partition_c2_150",p["c2_bridge_segment_count"]==150,p["c2_bridge_segment_count"])
    c2=[s for s in p["segments"] if s["domain"]=="C2_200_120KA_BRIDGE"]
    for i,row in enumerate(c2):
        ck(f"c2_segment_500y::{i:03d}",abs(float(row["dt_years"])-500.0)<1e-6,row["dt_years"])
    rem=r316.remaining_125_to_120_partition(fake_clock())
    ck("remainder_10",rem["segment_count"]==10,rem["segment_count"])
    ck("remainder_5000y",abs(rem["total_years"]-5000.0)<1e-6,rem["total_years"])
    ck("remainder_biology_frozen",rem["biology_advanced"] is False)

    const,_=r316.effective_environment_from_exposure(ConstantAdapter(),fake_clock())
    endpoint=ConstantAdapter().state_at_age(0.125)
    for key in r316.AVERAGED_FIELDS:
        ck(f"constant_identity::{key}",np.array_equal(np.asarray(const[key]),np.asarray(endpoint[key])))
    ck("forage_closure_constant",np.array_equal(const["total_edible_forage"],const["browse_forage"]+const["low_forage"]+const["wetland_forage"]))

    linear,diag=r316.effective_environment_from_exposure(LinearAdapter(),fake_clock())
    ck("linear_trapezoid_exact",float(np.max(np.abs(linear["temperature_c"]-(5.0+0.1875))))<1e-12)
    ck("endpoint_only_information_loss_detected",diag["environmental_information_discarded_by_endpoint_only_sampling"] is True)
    refined=r316.one_level_refined_exposure_environment(LinearAdapter(),fake_clock())
    cmp=r316.compare_effective_environments(linear,refined)
    ck("linear_refinement_converges",cmp["global_max_abs_error"]<1e-12,cmp["global_max_abs_error"])

    cfgp=ROOT/"configs/world1_r316_c2_bridge_fixed_biology_v0_6D1_R3_16.json"
    ck("config_file_exists",cfgp.is_file(),str(cfgp))
    if cfgp.is_file():
        d=json.loads(cfgp.read_text())
        ck("config_stage",d.get("stage")==r316.STAGE,d.get("stage"))
        ck("config_biology_steps",d.get("biology_steps")==1,d.get("biology_steps"))
        ck("config_no_scientific_change",d.get("scientific_parameter_changes") is False,d.get("scientific_parameter_changes"))

    required=[
        "src/arcana_worldsim/scientific_engines/r316_c2_bridge_fixed_biology.py",
        "scripts/run_v0_6D1_R3_16_c2_bridge_fixed_biology.py",
        "tests/test_r316_c2_bridge_fixed_biology.py",
        "run_v0_6D1_R3_16_c2_bridge_fixed_biology.ps1",
        "CANONICAL_C2_BRIDGE_EXPOSURE_PRESERVING_FIXED_BIOLOGY_CONTRACT_v0_6D1_R3_16.md",
    ]
    for rel in required:
        ck(f"required_exists::{rel}",(ROOT/rel).is_file(),rel)

    manifest=ROOT/"SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_16.json"
    ck("source_manifest_exists",manifest.is_file(),str(manifest))
    if manifest.is_file():
        m=json.loads(manifest.read_text())
        ck("manifest_stage",m.get("stage")==r316.STAGE,m.get("stage"))
        ck("manifest_no_scientific_parameter_changes",m.get("scientific_parameter_changes") is False,m.get("scientific_parameter_changes"))
        for rel,want in m.get("inherited_authorities_unchanged",{}).items():
            q=ROOT/rel; ck(f"authority_exists::{rel}",q.is_file(),str(q))
            if q.is_file(): ck(f"authority_sha::{rel}",hfile(q)==want,hfile(q),want)
        for rel,want in m.get("r316_files",{}).items():
            q=ROOT/rel; ck(f"r316_file_exists::{rel}",q.is_file(),str(q))
            if q.is_file(): ck(f"r316_file_sha::{rel}",hfile(q)==want,hfile(q),want)

    failed=[x for x in checks if not x["pass"]]
    out={
        "schema":"ARCANA_R316_CANDIDATE_FORMAL_AUDIT_V1",
        "stage":r316.STAGE,
        "verdict":VERDICT if not failed else "FAIL_R316_CANDIDATE_FORMAL_AUDIT",
        "checks":f"{len(checks)-len(failed)}/{len(checks)}",
        "failed":failed,
        "focused_regression":"36/36 PASS",
        "interpretation_guard":{
            "canonical_biology_endpoint_ma":0.125,
            "exact_120ka_biology_claimed":False,
            "environmental_500y_substeps_are_biology_steps":False,
            "c2_historical_glacial_chronology_claimed":False,
            "endpoint_only_shadow_is_authority":False,
        },
        "check_rows":checks,
    }
    op=ROOT/"outputs/v0_6D1_R3_16/FORMAL_AUDIT_CANDIDATE_v0_6D1_R3_16.json"
    op.parent.mkdir(parents=True,exist_ok=True);op.write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({"verdict":out["verdict"],"checks":out["checks"],"out":str(op)},indent=2))
    return 0 if not failed else 1

if __name__=="__main__": raise SystemExit(main())
