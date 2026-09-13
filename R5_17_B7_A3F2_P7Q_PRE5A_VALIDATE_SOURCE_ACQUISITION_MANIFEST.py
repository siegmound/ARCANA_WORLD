"""Validate PRE5-A metadata-only source manifest."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MAN=ROOT/"R5_17_B7_A3F2_P7Q_PRE5A_SOURCE_ACQUISITION_MANIFEST.json"
ADJ=ROOT/"R5_17_B7_A3F2_P7Q_PRE5A_SOURCE_ACQUISITION_AND_BINDING_ADJUDICATION.json"
def main():
    m=json.loads(MAN.read_text(encoding="utf-8")); d=json.loads(ADJ.read_text(encoding="utf-8"))
    assert m["stage"]=="P7Q-PRE5-A" and d["stage"]=="P7Q-PRE5-A"
    assert d["repository"]["basis_synchronized"] and not d["constraints"]["p7q_reopened"]
    assert d["constraints"]["full_scientific_payload_downloads"] is False and not d["constraints"]["simulation_performed"] and not d["constraints"]["materialization_performed"] and not d["constraints"]["provider_runtime_installed"]
    by={x["provider_id"]:x for x in m["bindings"]}
    assert by["GUM_V1"]["doi_or_reference"].startswith("10.1594/PANGAEA.884822") and by["GLIM_V1"]["doi_or_reference"].startswith("10.1594/PANGAEA.788537")
    assert "10.1002/2015MS000526" in by["PELLETIER_ORNL_1304"]["doi_or_reference"] and "10.3334/ORNLDAAC/1304" in by["PELLETIER_ORNL_1304"]["doi_or_reference"]
    assert by["SOILGRIDS_2_0"]["semantic_role"]=="OPTIONAL_MODERN_ENDPOINT_CALIBRATION"
    assert by["RESIDUAL_BEDROCK_CLASSIFIER"]["acquisition_status"]=="NO_PROVIDER_AUTHORIZED" and by["TEXTURE_TRANSFORM"]["acquisition_status"] if "TEXTURE_TRANSFORM" in by else True
    assert d["texture_transform_status"]=="NOT_AUTHORIZED" and d["profile_contract_status"]=="NOT_AUTHORIZED"
    for p in ("CRYOSPHERE_DRIVER","WIND_DRIVER","VOLCANISM_DRIVER"): assert by[p]["acquisition_status"]=="NO_PROVIDER_AUTHORIZED"
    assert all(x["acquisition_status"] in {"NOT_ACQUIRED","NO_PROVIDER_AUTHORIZED"} for x in m["bindings"])
    assert d["plan_path"] and (ROOT/d["plan_path"]).is_file() and d["source_binding_schema_path"]
    assert d["final_scientific_decision"]=="AUTHORIZE_P7Q_PRE5B_BOUNDED_SOURCE_SAMPLE_ACQUISITION_GATE"
    assert d["pass_verdict"]=="PASS_P7Q_PRE5A_SOURCE_ACQUISITION_AND_BINDING_ADJUDICATED"
    print("P7Q-PRE5-A validation passed")
if __name__=="__main__": raise SystemExit(main())
