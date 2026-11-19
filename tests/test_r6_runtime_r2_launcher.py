"""L1 launcher contracts and real E0 bounded CLI/recovery parity."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0, str(SCRIPTS))
import r6_runtime_r2_launcher as l1
from r6_int10k_runtime_r1 import ORACLE


def contract(years=10000, service='legacy_full', interval=4):
    return l1.make_contract(planned_years=years, checkpoint_interval_years=interval,
        journal_fsync_interval_years=1, journal_commit_interval_years=interval,
        archive_service=service, query_years=[0, 3, 10])


def cli(path, c, years, resume=False):
    contract_path=path.parent/(path.name+'.contract.json')
    if not contract_path.exists():l1.save(contract_path,c)
    args=[sys.executable,str(SCRIPTS/'r6_runtime_r2_launcher.py'),'run','--runtime-r2-rec1',
          '--contract',str(contract_path),'--contract-sha256',l1.file_sha(contract_path),
          '--output-root',str(path),'--advanced-segment-years',str(years)]
    if resume:args.append('--resume')
    result=subprocess.run(args,cwd=l1.WORK,env={**os.environ,'PYTHONPATH':'src','PYTHONNOUSERSITE':'1',
                    'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize('years,split,planned',[(3,1,1000),(10,5,1000),(3,1,10000),(10,5,10000)])
def test_process_exit_resume_full_causal_parity(tmp_path,years,split,planned):
    c=contract(planned)
    direct=cli(tmp_path/'direct',c,years)
    cli(tmp_path/'split',c,split)
    resumed=cli(tmp_path/'split',c,years-split,True)
    assert direct['checkpoint_sha256']==resumed['checkpoint_sha256']
    assert direct['committed_records']==resumed['committed_records']==1+61*years
    a=Path(direct['invocation'])/'LEGACY_HISTORY.jsonl'
    b=Path(resumed['invocation'])/'LEGACY_HISTORY.jsonl'
    assert a.read_bytes()==b.read_bytes()
    ai=a.with_name('LEGACY_INDEX.jsonl');bi=b.with_name('LEGACY_INDEX.jsonl')
    assert ai.read_bytes()==bi.read_bytes()
    rows=[json.loads(line) for line in a.open()]
    if planned==1000:
        expected=[]
        with (ORACLE/'INDEX.jsonl').open() as source:
            for _ in range(len(rows)):
                row=json.loads(next(source));expected.append((row['kind'],row['payload_sha256']))
        assert [(v['kind'],l1.sha(v['payload'])) for v in rows]==expected
        index_rows=[json.loads(line) for line in ai.open()]
        with (ORACLE/'INDEX.jsonl').open('rb') as original:
            assert ai.read_bytes()==b''.join(next(original) for _ in rows)
        with (ORACLE/'HISTORY.jsonl').open('rb') as original:
            assert a.read_bytes()==original.read(index_rows[-1]['offset']+index_rows[-1]['length'])
    assert sum(v['kind']=='REGIONAL_EVENT' and v['payload'].get('time_year') is None for v in rows)==8*years
    assert all(row['advance_with_compact_s']>0 for row in map(json.loads,(Path(resumed['invocation'])/'ANNUAL.jsonl').open()))


@pytest.mark.parametrize('change,message',[
    ({'journal_commit_interval_years':1},'INDEPENDENT_JOURNAL'),
    ({'external_step_years':2},'ANNUAL_ADVANCE'),
    ({'planned_years':-1},'POSITIVE_INTEGER'),
    ({'query_years':[10001]},'QUERY_YEAR'),
    ({'archive_service':'lossy'},'SERVICE_INVALID'),
    ({'unknown':True},'FIELDS_OR_SCHEMA')])
def test_invalid_contract_before_output(tmp_path,change,message):
    c=contract();c.update(change)
    with pytest.raises(l1.LauncherError,match=message):l1.execute(c,tmp_path/'out',advanced_segment_years=1)
    assert not (tmp_path/'out').exists()


def test_source_contract_input_and_path_identity(tmp_path):
    c=contract();c['source_sha256']['scripts/r6_runtime_r2_launcher.py']='0'*64
    with pytest.raises(l1.LauncherError,match='SOURCE_IDENTITY'):l1.execute(c,tmp_path/'bad',advanced_segment_years=1)
    p=tmp_path/'contract.json';l1.save(p,contract())
    with pytest.raises(l1.LauncherError,match='FILE_SHA'):l1.read_contract(p,'0'*64)
    c=contract();c['input_sha256'][next(iter(c['input_sha256']))]='0'*64
    with pytest.raises(l1.LauncherError,match='E0_EXPECTED'):l1.validate_contract(c)
    root=tmp_path/'occupied';root.mkdir()
    with pytest.raises(FileExistsError):l1.execute(contract(),root,advanced_segment_years=1)
    link=tmp_path/'link';link.symlink_to(root,target_is_directory=True)
    with pytest.raises(l1.LauncherError,match='SYMLINK'):l1.execute(contract(),link,advanced_segment_years=1)


def test_resume_config_and_corrupt_committed_history(tmp_path):
    c=contract();root=tmp_path/'run';l1.execute(c,root,advanced_segment_years=3)
    with pytest.raises(l1.LauncherError,match='CONTRACT_MISMATCH'):
        l1.execute(contract(1000),root,advanced_segment_years=1,resume=True)
    blob=next((root/'chunks').glob('*.jsonl'));blob.write_bytes(blob.read_bytes()[:-9])
    with pytest.raises(ValueError,match='COMMITTED_RECOVERY_INVALID'):
        l1.execute(c,root,advanced_segment_years=1,resume=True)


def test_compact_service_and_safe_segment_bound(tmp_path):
    c=contract(service='compact_query')
    result=l1.execute(c,tmp_path/'run',advanced_segment_years=3)
    invocation=Path(result['invocation'])
    assert not (invocation/'LEGACY_HISTORY.jsonl').exists()
    assert (invocation/'SNAPSHOT_00003.json').exists()
    assert result['services']['deferred_query_years']==[10]
    assert result['services']['full_snapshot_serializations']==2
    with pytest.raises(l1.LauncherError,match='HORIZON'):
        l1.execute(c,tmp_path/'run',advanced_segment_years=10000,resume=True)


def test_launcher_writer_lock(tmp_path):
    import fcntl
    c=contract(service='compact_query');root=tmp_path/'run'
    l1.execute(c,root,advanced_segment_years=1)
    with (root/'LAUNCHER.lock').open('a+b') as held:
        fcntl.flock(held,fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(l1.LauncherError,match='WRITER_ALREADY_ACTIVE'):
            l1.execute(c,root,advanced_segment_years=1,resume=True)
