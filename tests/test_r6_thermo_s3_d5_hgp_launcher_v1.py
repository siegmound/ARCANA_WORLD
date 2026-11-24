"""Launcher governance unit checks. No real or mocked engine invocation."""
import copy
import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_s3_d5_hgp_fair as h

HEAD = "a"*40


@pytest.fixture
def auth():
    return {"schema":"R6_HGP_OPERATOR_EXPLORE_AUTH_V1", "source_sha":HEAD,
            "receipt_git_blob":h.RECEIPT_BLOB, "scope":"EARTH_BL691_ONLY",
            "stage":"AB", "evidence_id":"R6_THERMO_S3_D5_HGP_AB_NEW01",
            "site_policy_basis":"synthetic test only",
            "address_space_limit_bytes":1000, "file_size_limit_bytes":100,
            "retained_bytes_stop_threshold":1000, "walltime_s":150,
            "operator_authorizes_explore":True}


def test_valid_auth(auth):
    assert h.validate_authorization(auth, HEAD) == auth


@pytest.mark.parametrize("key,value", [
    ("operator_authorizes_explore", False), ("operator_authorizes_explore", 1),
    ("source_sha","b"*40), ("receipt_git_blob","bad"),
    ("scope","ARCANA"), ("stage","AB+C"), ("evidence_id","../old"),
    ("evidence_id","R6_THERMO_S3_D5_HGP_C_NEW01"), ("site_policy_basis"," "),
    ("address_space_limit_bytes",None), ("file_size_limit_bytes",True),
    ("retained_bytes_stop_threshold",0), ("walltime_s",151),
    ("walltime_s",0), ("file_size_limit_bytes",1001)])
def test_invalid_auth(auth,key,value):
    auth[key] = value
    with pytest.raises(h.prep.HGPError):
        h.validate_authorization(auth,HEAD)


def test_extra_auth(auth):
    auth["physical_T1"] = True
    with pytest.raises(h.prep.HGPError):
        h.validate_authorization(auth,HEAD)


def test_conditional_scope(auth):
    auth["stage"] = "C"
    auth["evidence_id"] = "R6_THERMO_S3_D5_HGP_C_NEW01"
    assert h.validate_authorization(auth,HEAD)["stage"] == "C"


def test_receipt_pin():
    r = h.read_receipt()
    assert r["tests_passed"] == 153 and r["run_authorized"] is False


def sample_preparation(r):
    return {"original_input_sha256":r["original_input_sha256"],
            "runtime":{k:r[k] for k in ("binary_sha256","archive_sha256","s2_manifest_sha256")},
            "reference":{"prn_sha256":r["reference_prn_sha256"]},
            "cases":[{"case":k,"input_sha256":v} for k,v in r["cases"].items()]}


def test_receipt_parity():
    r = h.read_receipt()
    h.check_preparation(sample_preparation(r),r)


def test_receipt_drift():
    r = h.read_receipt()
    current = copy.deepcopy(sample_preparation(r))
    current["cases"][0]["input_sha256"]["hp62ver.dat"] = "other"
    with pytest.raises(h.prep.HGPError):
        h.check_preparation(current,r)


def test_inventory_and_retention(tmp_path):
    (tmp_path/"a").write_bytes(b"abc")
    assert h.retained_bytes(tmp_path) == 3
    assert h.inventory(tmp_path)["a"]["bytes"] == 3
    (tmp_path/"link").symlink_to(tmp_path/"a")
    with pytest.raises(h.prep.HGPError):
        h.inventory(tmp_path)
