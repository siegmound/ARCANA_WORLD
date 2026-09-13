"""Validate the non-materializing P7Q-PRE4 schema gate."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
EVIDENCE=ROOT/"R5_17_B7_A3F2_P7Q_PRE4_HYBRID_TEMPORAL_PARENT_STATE_ADAPTER_SCHEMA_ADJUDICATION.json"
def main():
    d=json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert d["stage"]=="P7Q-PRE4" and d["repository"]["basis_synchronized"]
    assert d["pre3_inheritance"]["decision"]=="AUTHORIZE_P7Q_PRE4_HYBRID_TEMPORAL_PARENT_STATE_ADAPTER_SCHEMA_GATE"
    assert d["canonical_snapshots"]==[200,125,120,20,15,14,13,12,11,10,5,0]
    assert d["register_preflight"]["classification"]=="SCHEMA_DESIGN_ONLY" and not d["register_preflight"]["p7q_reopened"]
    for k in ("state_schema_path","rule_registry_path","source_binding_schema_path"): assert (ROOT/d[k]).is_file()
    assert "UNKNOWN" in d["support_state_vocabulary"] and d["rule_contract_summary"]["gum_no_data_to_bedrock"]=="FORBIDDEN"
    assert d["pre3_inheritance"]["backward_inversion"]=="FORBIDDEN" and d["rule_contract_summary"]["eligibility_to_occurrence"]=="FORBIDDEN" and d["rule_contract_summary"]["proxy_to_direct_physical"]=="FORBIDDEN"
    assert d["rule_contract_summary"]["production_authorized_rules"]==0 and d["validation_contract"]["promotion_level"]=="L0_SCHEMA_ONLY"
    assert d["pass_verdict"]=="PASS_P7Q_PRE4_HYBRID_TEMPORAL_PARENT_STATE_ADAPTER_SCHEMA_ADJUDICATED"
    print("P7Q-PRE4 validation passed")
if __name__=="__main__": raise SystemExit(main())
