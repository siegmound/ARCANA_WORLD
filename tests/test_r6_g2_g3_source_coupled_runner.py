"""SHA/provenance and absent-provider tests for source-connected G2/G3 runner."""
import hashlib
import json
from pathlib import Path

import pytest

from experiments.plate58_deforming_explore_v1.g2_g3_source_coupled_runner import (
    EXPECTED, read_pinned, sha, source_inputs, execute, INPUT_SCHEMA,
)
from experiments.plate58_deforming_explore_v1.g2_g3_coupled_weak_form import (
    CoupledAssemblyError,
)


def one_pinned(tmp_path,owner="nodal"):
    filename,status=EXPECTED[owner]
    directory=tmp_path/owner
    directory.mkdir()
    body={"schema":"SYNTHETIC_TEST_ONLY","status":status,"payload":123}
    (directory/filename).write_text(json.dumps(body))
    digest=hashlib.sha256((directory/filename).read_bytes()).hexdigest()
    manifest={
        "status":status,
        "no_solver_run":True,"no_T1":True,
        "no_canonical_promotion":True,
        "files":{filename:digest},
    }
    (directory/"MANIFEST.json").write_text(json.dumps(manifest))
    return directory


def test_read_pinned_requires_authentic_matching_hash_and_no_solve(tmp_path):
    d=one_pinned(tmp_path)
    obj,digest=read_pinned("nodal",d)
    assert obj["payload"]==123
    assert digest==sha(d/"MANIFEST.json")
    assert len(digest)==64


@pytest.mark.parametrize("change",["bytes","no_T1","status"])
def test_pinned_source_tampering_fails_closed(tmp_path,change):
    d=one_pinned(tmp_path)
    fname=EXPECTED["nodal"][0]
    if change=="bytes":
        (d/fname).write_text('{"status":"tampered"}')
    else:
        path=d/"MANIFEST.json"
        content=json.loads(path.read_text())
        if change=="no_T1":
            content["no_T1"]=False
        else:
            content["status"]="FAKE_PASS"
        path.write_text(json.dumps(content))
    with pytest.raises(CoupledAssemblyError,
                       match="UPSTREAM_AUTHENTIC_SHA_INVALID"):
        read_pinned("nodal",d)


def test_explicit_input_scenario_absent_does_not_write_evidence(tmp_path):
    """No source folders or complete provider document: must never create T1."""
    cand=tmp_path/"in.json"
    cand.write_text(json.dumps({
        "schema":INPUT_SCHEMA,
        "authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
        "physical_source_authority_ratified":False,
        "mechanical_solve_authorized":False,
        "scope_extent_cells":8,
        "candidate_material_by_parent_node":{},
    }))
    target=tmp_path/"new-report"
    with pytest.raises((CoupledAssemblyError,FileNotFoundError)):
        execute(
            multiscale=tmp_path/"nonexistent",
            interface=tmp_path/"nonexistent",
            nodal=tmp_path/"nonexistent",
            force=tmp_path/"nonexistent",
            scenario_path=cand,extent=8,output=target)
    assert not target.exists()
