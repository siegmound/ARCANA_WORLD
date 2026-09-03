from pathlib import Path
import inspect
import numpy as np
import arcana_worldsim.scientific_engines.r437_geonomics_canonical_layer_binding_exact_state_injection_dry_run as m

def test_exact_authorized_partition_149_plus_2(tmp_path):
    records=[]
    for i in range(149):
        p=tmp_path/f"n{i}.npy"; np.save(p,np.array([[0.25]]),allow_pickle=False)
        records.append({"payload_file":p.name,"payload_sha256":m.sha256(p),
                        "layer_family":"producer_support","name":f"v{i}"})
    for name,val in [("temperature_anomaly_c",-5.0),("sea_level_anomaly_m",-100.0)]:
        p=tmp_path/f"{name}.npy"; np.save(p,np.array([[val]]),allow_pickle=False)
        records.append({"payload_file":p.name,"payload_sha256":m.sha256(p),
                        "layer_family":"environment","name":name})
    r=m._payload_range_audit(tmp_path,{"records":records})
    assert r["exact_authorized_representability_partition"] is True
    assert r["native_identity_layer_count"]==149
    assert r["canonical_physical_unit_sidecar_count"]==2
    assert r["automatic_rescaling_performed"] is False
    assert r["result_selected_transform_performed"] is False

def test_unrecognized_out_of_range_field_blocks(tmp_path):
    p=tmp_path/"x.npy"; np.save(p,np.array([[-2.0]]),allow_pickle=False)
    r=m._payload_range_audit(tmp_path,{"records":[{
        "payload_file":"x.npy","payload_sha256":m.sha256(p),
        "layer_family":"environment","name":"invented"
    }]})
    assert r["records"][0]["binding_class"]=="BLOCKED_UNAUTHORIZED_REPRESENTATION"

def test_public_wrapper_compat_shim_is_temporary():
    s=inspect.getsource(m._install_public_add_individuals_149_compat_shim)
    r=inspect.getsource(m._restore_public_add_individuals_149_compat_shim)
    assert 'gmodel.species = source_spp.__class__' in s
    assert 'delattr(gmodel, "species")' in r

def test_no_private_mutation_api_calls_or_runs():
    s=inspect.getsource(m)
    assert "._remove_individuals(" not in s
    assert "._add_individuals(" not in s
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s

def test_expected_binding_count_is_596():
    s=inspect.getsource(m)
    assert 'j21.get("canonical_layer_binding_count") == 596' in s
