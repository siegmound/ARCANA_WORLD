"""Offline CLI/control tests; no real R4 kernel execution, no Windows B0 writes."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import json
import io
import subprocess
import sys

import pytest

import r6_int2c_replay_launcher as launch
import r6_int2c_replay_adapter as adapter
from arcana_worldsim.r6.replay import ReplayExecutionOutput
from r6_int2c_checkpoint_attest import TechnicalAttestation
from test_r6_int2c_replay_adapter import synthetic, validated_fixture, MemoryReadFixture


@pytest.fixture
def closed(synthetic, monkeypatch):
    cp, recipe = validated_fixture(synthetic)
    p = replace(synthetic, checkpoint=cp, recipe=recipe)
    a = TechnicalAttestation(synthetic, p, ())
    store = MemoryReadFixture(p, cp)
    store.checkpoints.update({str(x.checkpoint_id): x.to_dict() for x in
                             (synthetic.original_checkpoint, synthetic.checkpoint)})
    recipes = {str(x.recipe_id): x for x in (synthetic.original_recipe, synthetic.recipe, recipe)}
    store.read_replay_recipe = lambda key: recipes[key]
    monkeypatch.setattr(launch, "EXPECTED_CHECKPOINT", str(cp.checkpoint_id))
    monkeypatch.setattr(launch, "EXPECTED_RECIPE", str(recipe.recipe_id))
    monkeypatch.setattr(launch, "EXPECTED_STATE", str(p.expected.state_id))
    sides = adapter.thaw_json(p.expected.value)["side_states"]
    monkeypatch.setattr(launch, "EXPECTED_PAYLOAD", launch.digest(launch._json_bytes(sides[0])))
    monkeypatch.setattr(adapter.kernel, "pure_shear_thermal_step",
                        lambda *a, **k: pytest.fail("real kernel prohibited"))
    return a, store


def test_closed_records_and_transparent_capture(closed):
    a, store = closed
    inputs = launch.validate_store(store, a)
    assert inputs.base_states == (a.prepared.initial,)
    calls = []
    output = ReplayExecutionOutput(a.prepared.expected)
    def synthetic_runner(recipe, resolved):
        calls.append((recipe, resolved))
        return output
    result, state = launch.replay_result(a.prepared, store, synthetic_runner)
    assert len(calls) == 1
    assert state == output.state.to_dict()
    assert result["b0_verification"]["status"] == "VERIFIED"
    assert len(result["per_support_payload_sha256"]) == 2
    assert result["status"] == "VERIFIED"


@pytest.mark.parametrize("defect", ["missing_checkpoint", "wrong_checkpoint", "altered_forcing"])
def test_persisted_records_fail_before_dispatch(closed, defect):
    a, store = closed
    if defect == "missing_checkpoint":
        store.checkpoints.clear()
    elif defect == "wrong_checkpoint":
        store.checkpoints[str(a.prepared.checkpoint.checkpoint_id)]["validation_status"] = "CANDIDATE_NONCANONICAL"
    else:
        store.forcings[str(a.prepared.forcing.forcing_id)]["value"]["signed_Ux_m_per_year"] = 12.0
    with pytest.raises((ValueError, KeyError)):
        launch.validate_store(store, a)


def test_numerical_mismatch_preserves_computed_state(closed):
    a, store = closed
    result, state = launch.replay_result(a.prepared, store,
                                        lambda *args: ReplayExecutionOutput(a.prepared.initial))
    assert result["status"] == "MISMATCH"
    assert state == a.prepared.initial.to_dict()
    assert result["computed_state_id"] != result["expected_state_id"]


def test_preflight_child_never_dispatches_kernel(closed, tmp_path, monkeypatch):
    a, store = closed
    source = tmp_path/"original"
    source.mkdir()
    out = tmp_path/"evidence"
    out.mkdir()
    monkeypatch.setattr(launch.sys, "stdin", io.StringIO("START\n"))
    monkeypatch.setattr(launch, "runtime_check", lambda: {"scope":"SYNTHETIC_FIXTURE_ONLY"})
    monkeypatch.setattr(launch, "source_check", lambda *args: {})
    monkeypatch.setattr(launch, "attest_r4", lambda *args: a)
    monkeypatch.setattr(launch, "copy_store", lambda *args: {})
    # The storage constructor is a test double; typed transaction parsing remains real.
    parser = launch.HistoryStore._transaction_record
    class StoreDouble:
        _transaction_record = staticmethod(parser)
        def __new__(cls, *args):
            return store
    monkeypatch.setattr(launch, "HistoryStore", StoreDouble)
    monkeypatch.setattr(launch, "replay_result", lambda *args: pytest.fail("no dispatch in preflight"))
    args = SimpleNamespace(repository="/synthetic",bundle="/synthetic",store=str(source),
                           output=str(out),source_commit="a"*40,execute_authorized=False)
    assert launch.child(args) == 0
    result = json.loads((out/"REPLAY_RESULT.json").read_bytes())
    assert result["numerical_execution_started"] is False
    assert result["status"] == "PREFLIGHT_PASS_NO_NUMERICAL_EXECUTION"


def test_pinned_checkpoint_identity_required(closed, monkeypatch):
    a, store = closed
    monkeypatch.setattr(launch, "EXPECTED_CHECKPOINT", "r6checkpoint_wrong")
    with pytest.raises(ValueError, match="PINNED_TECHNICAL_IDENTITY"):
        launch.validate_store(store, a)


def test_exact_child_command_and_no_runtime_fallback():
    a = SimpleNamespace(repository="/repo", bundle="/r4", store=launch.STORE,
                        output="/new", source_commit="a"*40, execute_authorized=False)
    command = launch.child_command(a)
    assert command[:2] == [sys.executable, "-u"]
    assert "--execute-authorized" not in command
    assert command[command.index("--store")+1] == launch.STORE
    a.execute_authorized = True
    assert launch.child_command(a)[-1] == "--execute-authorized"


@pytest.mark.parametrize("defect", ["collision", "missing", "overlap", "canonical"])
def test_path_preflight(tmp_path, defect):
    repo, bundle, store = [tmp_path/x for x in ("repo", "r4", "store")]
    for path in (repo, bundle, store):
        path.mkdir()
    output = tmp_path/"new"
    if defect == "collision":
        output.mkdir()
    elif defect == "missing":
        bundle = tmp_path/"absent"
    elif defect == "overlap":
        output = store/"new"
    else:
        output = tmp_path/"WORLD_HISTORY"/"new"
    with pytest.raises(ValueError):
        launch.check_paths(repo, bundle, store, output)


def test_source_commit_and_dirty_worktree_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(launch.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout=b"wrong"))
    with pytest.raises(ValueError, match="SOURCE_COMMIT_MISMATCH"):
        launch.source_check(tmp_path, "a"*40)
    monkeypatch.setattr(launch.subprocess, "run", lambda args, **k: SimpleNamespace(
        stdout=(b"a"*40 if args[1] == "rev-parse" else b" M scripts/altered.py")))
    with pytest.raises(ValueError, match="NOT_CLEAN"):
        launch.source_check(tmp_path, "a"*40)


def test_runtime_failure_prevents_supervisor(tmp_path, monkeypatch):
    for name in ("repo", "r4", "store"):
        (tmp_path/name).mkdir()
    monkeypatch.setattr(launch, "source_check", lambda *a: {})
    monkeypatch.setattr(launch, "runtime_check", lambda: {})
    monkeypatch.setattr(launch, "attest_r4", lambda *a: (_ for _ in ()).throw(
        adapter.ReplayBindingError("CODE_OR_RUNTIME_IDENTITY_MISMATCH")))
    monkeypatch.setattr(launch, "supervise", lambda *a: pytest.fail("must not launch"))
    with pytest.raises(ValueError, match="RUNTIME"):
        launch.main(["--repository",str(tmp_path/"repo"),"--bundle",str(tmp_path/"r4"),
                     "--store",str(tmp_path/"store"),"--output",str(tmp_path/"new"),
                     "--source-commit","a"*40])
    assert not (tmp_path/"new").exists()


def test_isolated_runtime_rejects_external_numpy_or_python(monkeypatch, tmp_path):
    monkeypatch.setattr(launch, "RUNTIME", tmp_path/"isolated")
    with pytest.raises(ValueError, match="EXACT_ISOLATED_RUNTIME"):
        launch.runtime_check()


def test_store_copy_is_exact_and_original_unchanged(tmp_path):
    source, copied = tmp_path/"store", tmp_path/"copied"
    source.mkdir()
    for i in range(16):
        (source/str(i)).write_bytes(b"x"*(78930 if i == 0 else 1))
    before = launch.inventory(source)
    assert launch.copy_store(source, copied) == before
    assert launch.inventory(source) == launch.inventory(copied) == before


def test_copy_rejects_wrong_c2_inventory(tmp_path):
    source = tmp_path/"store"
    source.mkdir()
    (source/"unexpected").write_bytes(b"no substitute for C2")
    with pytest.raises(ValueError, match="INVENTORY"):
        launch.copy_store(source, tmp_path/"copy")
    assert not (tmp_path/"copy").exists()


def test_proc_tree_descendants_orphans_and_pid_reuse():
    known = {5: 50, 8: 80}
    rows = {5:(1,5,50,100), 6:(5,5,60,200), 7:(6,7,70,300),
            8:(1,8,81,9999), 9:(1,5,90,400)}
    members, rss = launch.process_tree(5, rows, known)
    assert set(members) == {5,6,7,9} and rss == 1000
    assert members[7] == 70


def test_proc_stat_layout(tmp_path, monkeypatch):
    p = tmp_path/"42"
    p.mkdir()
    fields = ["S", "12", "42"] + ["0"]*19
    fields[19], fields[21] = "123456", "7"
    (p/"stat").write_text("42 (python with spaces) " + " ".join(fields))
    monkeypatch.setattr(launch.os, "sysconf", lambda *a: 4096, raising=False)
    assert launch.proc_rows(tmp_path)[42] == (12,42,123456,7*4096)


def test_linux_required_without_launch(tmp_path):
    if sys.platform == "linux":
        pytest.skip("Windows platform rejection test")
    with pytest.raises(ValueError, match="LINUX"):
        launch.supervise([sys.executable], tmp_path/"new")
    assert not (tmp_path/"new").exists()


@pytest.mark.parametrize("reason,code,expected", [("NATURAL_EXIT",7,7),
                         ("CHILD_SIGNAL_EXIT",-15,143),("WALL_TIME_LIMIT",-9,124)])
def test_supervisor_exit_classification(reason, code, expected):
    assert launch.supervisor_exit_status({"stop_reason":reason,"child_exit_code":code}) == expected


@pytest.mark.skipif(sys.platform != "linux", reason="Linux /proc/process-group runtime required")
@pytest.mark.parametrize("scenario", ["exit", "time", "memory", "output", "descendant", "signal"])
def test_linux_synthetic_supervision_only(tmp_path, scenario):
    # No ARCANA/provider/kernel import in these small subprocesses.
    code = "import sys; sys.exit(7)"
    limits = (3.0, 256*1024**2, 1024**2)
    if scenario == "time":
        code = "import time; time.sleep(20)"
        limits = (0.3, limits[1], limits[2])
    elif scenario == "memory":
        code = "import time; x=bytearray(32*1024**2); time.sleep(20)"
        limits = (3.0, 20*1024**2, limits[2])
    elif scenario == "output":
        code = "import time; print('x'*20000,flush=True); time.sleep(20)"
        limits = (3.0, limits[1], 10000)
    elif scenario == "descendant":
        code = "import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(20)']); print('DESCENDANT',p.pid,flush=True); time.sleep(20)"
        limits = (0.5, limits[1], limits[2])
    elif scenario == "signal":
        code = "import os,signal; os.kill(os.getpid(),signal.SIGTERM)"
    out = tmp_path/scenario
    code = "import sys; assert sys.stdin.readline().strip()=='START'; " + code
    result = launch.supervise([sys.executable,"-u","-c",code], out, limits=limits)
    if scenario == "exit":
        assert result["stop_reason"] == "NATURAL_EXIT" and result["child_exit_code"] == 7
    elif scenario == "signal":
        assert result["stop_reason"] == "CHILD_SIGNAL_EXIT" and result["child_exit_code"] == -15
        assert launch.supervisor_exit_status(result) == 143
    else:
        expected = {"time":"WALL_TIME_LIMIT", "memory":"PROCESS_TREE_RSS_LIMIT",
                    "output":"OUTPUT_BYTES_LIMIT", "descendant":"WALL_TIME_LIMIT"}
        assert result["stop_reason"] == expected[scenario]
        assert result["child_exit_code"] != 0
    assert result["identity"]["pid"] > 0
    assert result["peak_sampled_process_tree_rss_bytes"] > 0
    if scenario == "descendant":
        pid = int((out/"stdout.log").read_text().split()[1])
        assert pid in result["observed_process_start_ticks"]
        stat = Path(f"/proc/{pid}/stat")
        assert not stat.exists() or stat.read_text().rsplit(")",1)[1].split()[0] == "Z"
    manifest = json.loads((out/"ARTIFACT_MANIFEST.json").read_bytes())
    for name, record in manifest["artifacts"].items():
        raw=(out/name).read_bytes()
        assert len(raw)==record["bytes"] and launch.digest(raw)==record["sha256"]
