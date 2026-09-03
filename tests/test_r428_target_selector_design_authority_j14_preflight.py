from arcana_worldsim.scientific_engines.r428_target_selector_design_authority_j14_preflight import (
    _schema_inventory, build_selector_preflight, implement_target_design_authorities,
    build_semantic_repair_preflight, build_j14_preflight,
)

def test_schema_inventory_is_exact_not_fuzzy():
    b={"parser_family":"READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR","schema":{"schema_paths":["a.value","b"]}}
    assert _schema_inventory(b)==["a.value","b"]

def test_selector_preflight_never_auto_authorizes():
    static={"records":[{
        "window_id":f"W{i}","domain":"connectivity","static_implementation_valid":True,
        "selector_execution_authorized_in_r427":False,
        "source_bindings":[{"source":f"s{i}.json","parser_family":"READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR","expected_sha256":"x","observed_sha256":"x","hash_match":True,"parser_supported":True,"static_schema_valid":True,"schema":{"schema_paths":["canonical_value"]}}]
    } for i in range(44)]}
    protocols={"records":[{"window_id":f"W{i}","domain":"connectivity","protocol":{"canonical_quantity":"x"}} for i in range(44)]}
    o=build_selector_preflight(static,protocols)
    assert o["selector_authority_preflight_ready_count"]==44
    assert o["selector_authorized_count"]==0
    assert all(r["selector_selection_policy"]=="EXPLICIT_EXACT_FIELD_FREEZE_ONLY" for r in o["records"])

def test_target_design_implementation_is_nonnumeric():
    reqs={"requests":[{"window_id":f"W{i}","domain":"range_shift_rate","scientific_construct":"C","required_canonical_observables":["A","B","C"],"permitted_unit_families":["U"],"required_governance":["G"],"forbidden_shortcuts":["X"]} for i in range(12)]}
    adj={"records":[{"window_id":f"W{i}","domain":"range_shift_rate","authority_definition_implementation_authorized_in_r428":True} for i in range(12)]}
    o=implement_target_design_authorities(adj,reqs)
    assert o["authority_definition_implemented_count"]==12
    assert o["numeric_target_materialization_authorized_count"]==0

def test_semantic_repair_scope_stays_narrow():
    s={"semantic_repair_records":[{"window_id":"W","domain":"population_persistence","static_validation_pass":True,"failed_validation_keys_frozen":["eligible_primary_row_count"]}]}
    o=build_semantic_repair_preflight(s)
    assert o["review_preflight_ready_count"]==1
    assert o["records"][0]["mapping_class_upgrade_authorized"] is False

def test_j14_preflight_does_not_authorize_execution():
    adj={"spatial_authority_implementation_preflight_authorized_in_r428":True}
    req={"request_kind":"NEW_ENGINE_INDEPENDENT_CANONICAL_SPATIAL_REPLAY_AUTHORITY","new_namespace_required_if_authority_is_later_approved":True,"required_temporal_support":{"start_age_ma":3.0,"end_age_ka":200.0},"r42_j14_mutation_authorized":False,"job_id":"R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"}
    geo={"records":[{"job_id":"R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS","canonical_spatial_sources_audited":[{},{}],"r327_macro_state_is_spatial":False,"window_start_3000ka_explicit_spatial_state_present":False}]}
    o=build_j14_preflight(adj,req,geo)
    assert o["implementation_preflight_ready"] is True
    assert o["canonical_spatial_replay_execution_authorized_in_r428"] is False
    assert o["geonomics_execution_authorized_in_r428"] is False

def test_selector_preflight_allows_explicit_no_inventory_deferral_without_selector_synthesis():
    records=[]
    protocols=[]
    for i in range(44):
        schema_paths=["canonical_value"] if i < 38 else []
        records.append({
            "window_id":f"W{i}","domain":"connectivity","static_implementation_valid":True,
            "selector_execution_authorized_in_r427":False,
            "source_bindings":[{
                "source":f"s{i}.json","parser_family":"READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR",
                "expected_sha256":"x","observed_sha256":"x","hash_match":True,
                "parser_supported":True,"static_schema_valid":True,
                "schema":{"schema_paths":schema_paths},
            }],
        })
        protocols.append({"window_id":f"W{i}","domain":"connectivity","protocol":{"canonical_quantity":"x"}})
    o=build_selector_preflight({"records":records},{"records":protocols})
    assert o["selector_authority_preflight_ready_count"] == 38
    assert o["selector_authority_preflight_deferred_no_exact_inventory_count"] == 6
    assert o["selector_authority_preflight_terminal_count"] == 44
    assert o["selector_authority_preflight_blocked_count"] == 0
    assert o["status"] == "R428_TARGET_SELECTOR_AUTHORITY_IMPLEMENTATION_PREFLIGHT_COMPLETE"
    deferred=[r for r in o["records"] if r["selector_authority_preflight_disposition"] == "DEFERRED_NO_EXACT_SCHEMA_SELECTOR_INVENTORY"]
    assert len(deferred)==6
    assert all(r["selector_authorized_in_r428"] is False for r in deferred)
    assert all(r["result_selected_selector_authorized"] is False for r in deferred)


def test_selector_preflight_still_fails_closed_when_domain_protocol_is_missing():
    static={"records":[{
        "window_id":f"W{i}","domain":"connectivity","static_implementation_valid":True,
        "selector_execution_authorized_in_r427":False,
        "source_bindings":[{
            "source":f"s{i}.json","parser_family":"READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR",
            "expected_sha256":"x","observed_sha256":"x","hash_match":True,
            "parser_supported":True,"static_schema_valid":True,
            "schema":{"schema_paths":["canonical_value"]},
        }],
    } for i in range(44)]}
    protocols={"records":[{"window_id":f"W{i}","domain":"connectivity","protocol":{"canonical_quantity":"x"}} for i in range(43)]}
    o=build_selector_preflight(static, protocols)
    assert o["selector_authority_preflight_blocked_count"] == 1
    assert o["status"].startswith("BLOCKED_R428")
