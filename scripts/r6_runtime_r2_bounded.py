#!/usr/bin/env python3
"""R2 bounded qualification: 3/10Y, saved anchors and read-only offline oracle.

No 1000Y/10k numerical mode exists. Full archive conversion is read-only physics.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict
import cProfile
import hashlib
import json
import os
from pathlib import Path
import pstats
import resource
import statistics
import subprocess
import sys
import time

from r6_int10k_runtime_r1 import (
    BASE, EVIDENCE, INPUT, ORACLE, MANIFEST_SHA, WORK, canonical, digest,
    file_sha, git, initial, save,
)
from arcana_worldsim.r6.int10k_runtime_compact import (
    CompactRuntime, FRAME_SCHEMA, STREAM_SCHEMA, make_delta, apply_delta,
)
from arcana_worldsim.r6.regional_geological_evolution import RegionalConfig, run_regional_segment

ROOT = EVIDENCE / "RUNTIME_R2_STRUCTURAL_20261030_01"


def refs_by_year():
    refs = defaultdict(list)
    year = 0
    for line in (ORACLE/'INDEX.jsonl').open():
        row = json.loads(line)
        if row['kind'] == 'UNIFIED_STEP':
            year = int(row['time_year'])
        refs[year].append((row['kind'], row['payload_sha256']))
    return refs


def encode_entry(entries, head, kind, payload):
    body = {'schema': STREAM_SCHEMA, 'sequence': len(entries), 'parent_sha256': head,
            'kind': kind, 'payload': payload}
    sha = digest(body)
    entries.append(canonical({**body, 'sha256': sha}))
    return sha


class ReferenceSink:
    """R1 producer adapted to the SAME requested compact representation."""
    def __init__(self, cp, source):
        region = cp['regional_checkpoint']['regional_state']
        self.root = {'time_year': cp['time_year'], 'cells': region['cells']}
        self.head = digest({'snapshot_sha256': digest(self.root), 'source': source,
                            'configuration': cp['configuration']})
        self.entries = []
        self.full_rows = []
        self.counts = [len(c['deposits']) for c in region['cells']]

    def emit(self, kind, payload):
        self.full_rows.append((kind, payload))
        if kind == 'REGIONAL_SNAPSHOT':
            year = payload['time_year']
            frame = {'schema': FRAME_SCHEMA, 'parent_year': year-1, 'year': year,
                     'parent_snapshot_sha256': None, 'target_snapshot_sha256': None,
                     'canonical_sha_status': 'DEFERRED_UNTIL_MATERIALIZATION',
                     'snapshot_fields': {'time_year': year},
                     'cells': [{'fields': {k:v for k,v in c.items() if k != 'deposits'},
                                'start': start, 'delete': 0, 'values': c['deposits'][start:]}
                               for c,start in zip(payload['cells'],self.counts)]}
            self.counts = [len(c['deposits']) for c in payload['cells']]
            kind, payload = 'REGIONAL_DELTA', frame
        self.head = encode_entry(self.entries, self.head, kind, payload)


def dump_legacy(path, rows, expected):
    seen = []
    with path.open('xb') as stream:
        for kind, payload in rows:
            seen.append((kind, digest(payload)))
            stream.write(canonical({'kind':kind,'payload':payload})+b'\n')
        stream.flush()
    assert seen == expected, ('ORDERED_ORACLE_MISMATCH', path.name)


def rss_status():
    return {k:v.strip() for k,v in (line.split(':',1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
            if k in ('VmRSS','VmHWM','Threads')}


def execute(mode, year, span, out, repetition, states, identity, cp, reference):
    name = f'{mode}_y{year}_n{span}_r{repetition}'
    tick = time.perf_counter()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    if mode == 'r1':
        sink = ReferenceSink(cp, identity)
        before = None
    else:
        sink = CompactRuntime(states, identity, config=RegionalConfig(duration_years=1000),
                              checkpoint=cp, runtime_compact_history=True)
        before = sink.metrics
    imported = time.perf_counter()-tick
    start = time.perf_counter()
    if mode == 'r1':
        checkpoint = cp
        for _ in range(span):
            result = run_regional_segment(states,identity,config=RegionalConfig(duration_years=1000),
                    segment_years=1,checkpoint=checkpoint,history_independent_continuation=True,
                    runtime_copy_optimization=True,history_consumer=sink.emit)
            checkpoint = result['checkpoint']
        entries = sink.entries
        operation_metrics = None
    else:
        sink.advance(span)
        entries = sink.entries
        operation_metrics = {k:sink.metrics[k]-before[k] for k in before}
        assert operation_metrics['deposit_rows_frozen'] == operation_metrics['deposit_rows_exported'] == 11*span
        assert operation_metrics['old_deposit_rows_copied_per_step'] == operation_metrics['full_snapshots_built_per_step'] == 0
    engine_and_compact_ingest = time.perf_counter()-start
    write_tick = time.perf_counter()
    compact_path = out/(name+'.compact.jsonl')
    with compact_path.open('xb') as stream:
        for encoded in entries:
            stream.write(encoded+b'\n')
        stream.flush()
    compact_write = time.perf_counter()-write_tick
    compact_total = time.perf_counter()-tick
    query_tick = time.perf_counter()
    if mode == 'r1':
        snap = json.loads(canonical(result['state']['snapshots'][-1]))
    else:
        snap = sink.snapshot()
    query_wall = time.perf_counter()-query_tick
    assert snap['time_year'] == year+span-1
    legacy_tick = time.perf_counter()
    legacy_path = out/(name+'.legacy.jsonl')
    dump_legacy(legacy_path, sink.full_rows if mode=='r1' else sink.legacy_history(), reference)
    legacy_wall = time.perf_counter()-legacy_tick
    cp_tick = time.perf_counter()
    if mode != 'r1':
        checkpoint = sink.checkpoint()
    cp_bytes = canonical(checkpoint)
    with (out/(name+'.checkpoint.json')).open('xb') as stream:
        stream.write(cp_bytes)
        stream.flush()
    checkpoint_wall = time.perf_counter()-cp_tick
    complete_wall = time.perf_counter()-tick
    end_usage = resource.getrusage(resource.RUSAGE_SELF)
    frame_bytes = sum(len(e)+1 for e in entries if json.loads(e)['kind']=='REGIONAL_DELTA')
    return {'import_or_sink_setup_s':imported,'engine_and_compact_ingest_s':engine_and_compact_ingest,
            'compact_write_s':compact_write,'compact_total_s':compact_total,
            'query_s':query_wall,'legacy_materialize_and_write_s':legacy_wall,
            'checkpoint_export_and_write_s':checkpoint_wall,'full_service_total_s':complete_wall,
            'cpu_user_s':end_usage.ru_utime-usage.ru_utime,'cpu_system_s':end_usage.ru_stime-usage.ru_stime,
            'checkpoint_sha256':hashlib.sha256(cp_bytes).hexdigest(),'query_sha256':digest(snap),
            'compact_bytes':compact_path.stat().st_size,'legacy_bytes':legacy_path.stat().st_size,
            'compact_sha256':file_sha(compact_path),'legacy_sha256':file_sha(legacy_path),
            'delta_frame_bytes':frame_bytes,'operation_metrics':operation_metrics,**rss_status()}


def worker(mode, year, span, out):
    states,identity = initial()
    cp = json.loads((ORACLE/f'CHECKPOINT_{year-1:04d}.json').read_bytes())
    refs = refs_by_year()
    reference = [row for y in range(year,year+span) for row in refs[y]]
    assert len(reference) == 61*span
    samples=[]
    for repetition in range(8):
        row=execute(mode,year,span,out,repetition,states,identity,cp,reference)
        if repetition:
            samples.append(row)
    for field in ['checkpoint_sha256','query_sha256','compact_sha256','legacy_sha256']:
        assert len({s[field] for s in samples}) == 1, field
    # Separate CPU profile, never used as unprofiled speedup evidence.
    profile=cProfile.Profile()
    if mode=='r2':
        session=CompactRuntime(states,identity,config=RegionalConfig(duration_years=1000),checkpoint=cp,runtime_compact_history=True)
        profile.runcall(session.advance,1)
    else:
        sink=ReferenceSink(cp,identity)
        profile.runcall(run_regional_segment,states,identity,config=RegionalConfig(duration_years=1000),
                       segment_years=1,checkpoint=cp,history_independent_continuation=True,
                       runtime_copy_optimization=True,history_consumer=sink.emit)
    profile.dump_stats(str(out/f'{mode}_y{year}_n{span}.pstats'))
    stats=pstats.Stats(profile)
    exclusive=[{'file':filename,'line':line,'function':function,'exclusive_cpu_s':values[2]}
               for (filename,line,function),values in stats.stats.items()]
    return {'mode':mode,'year':year,'span':span,'samples':samples,
            'medians':{field:statistics.median(s[field] for s in samples) for field in [
                'import_or_sink_setup_s','engine_and_compact_ingest_s','compact_write_s','compact_total_s',
                'query_s','legacy_materialize_and_write_s','checkpoint_export_and_write_s','full_service_total_s']},
            'profile_top_exclusive_cpu':sorted(exclusive,key=lambda r:r['exclusive_cpu_s'],reverse=True)[:35],
            'rss_scope':'fresh worker per mode/case; VmHWM includes setup, seven repetitions, queries and profiling',
            'durability_scope':'scratch files with flush, no fsync or B0 transactions'}


def short_oracle():
    states,identity=initial()
    refs=refs_by_year()
    report=[]
    for years,split in [(3,1),(10,5)]:
        def new(cp=None):
            return CompactRuntime(states,identity,config=RegionalConfig(duration_years=1000),checkpoint=cp,runtime_compact_history=True)
        direct=new();direct.advance(years)
        prefix=new();prefix.advance(split)
        resumed=new(prefix.checkpoint());resumed.advance(years-split)
        expected=defaultdict(list)
        for year in range(years+1):
            for kind,sha in refs[year]:expected[kind].append(sha)
        def hashes(sessions):
            found=defaultdict(list)
            for session in sessions:
                for kind,payload in session.legacy_history():found[kind].append(digest(payload))
            return dict(found)
        assert hashes([direct])==hashes([prefix,resumed])==dict(expected)
        r1=run_regional_segment(states,identity,config=RegionalConfig(duration_years=1000),segment_years=years,
              history_independent_continuation=True,runtime_copy_optimization=True,history_consumer=lambda k,p:None)
        assert canonical(direct.checkpoint())==canonical(resumed.checkpoint())==canonical(r1['checkpoint'])
        assert canonical(direct.balances())==canonical(resumed.balances())==canonical(r1['balances'])
        report.append({'years':years,'split':split,'status':'EXACT_ORIGINAL_ORACLE_AND_R1_PASS',
                       'items':sum(map(len,expected.values()))})
    return report


def offline(out):
    """New R2 codec over authentic source; no numerical evolution occurs."""
    parent=None;count=0;nulls=0;snapshots=0;head='0'*64;sequence=0
    timings=defaultdict(float)
    target=out/'OFFLINE_R2_COMPACT.jsonl'
    started=time.perf_counter()
    with (ORACLE/'HISTORY.jsonl').open('rb') as history,(ORACLE/'INDEX.jsonl').open() as index,target.open('xb') as stream:
        for text in index:
            reference=json.loads(text)
            line=history.read(reference['length'])
            envelope=json.loads(line)
            kind,payload=envelope['kind'],envelope['payload']
            assert envelope['sequence']==count and reference['offset']==history.tell()-len(line)
            assert kind==reference['kind'] and digest(payload)==reference['payload_sha256']
            if kind=='REGIONAL_SNAPSHOT':
                snapshots+=1
                if parent is None:
                    stored=payload
                else:
                    tick=time.perf_counter();delta=make_delta(parent,payload)
                    timings['sealed_codec_generation_s']+=time.perf_counter()-tick
                    tick=time.perf_counter();rebuilt=apply_delta(parent,delta)
                    assert digest(rebuilt)==reference['payload_sha256']
                    timings['reconstruction_and_validation_s']+=time.perf_counter()-tick
                    kind,stored='REGIONAL_DELTA',delta
                parent=payload
                if payload['time_year'] % 100 == 0:
                    print('OFFLINE_SNAPSHOT_YEAR='+str(payload['time_year']),flush=True)
            else:
                stored=payload
                if kind=='REGIONAL_EVENT' and envelope['time_year'] is None:nulls+=1
            tick=time.perf_counter()
            body={'schema':STREAM_SCHEMA,'sequence':sequence,'parent_sha256':head,'kind':kind,'payload':stored}
            head=digest(body)
            stream.write(canonical({**body,'sha256':head})+b'\n')
            timings['encode_hash_write_s']+=time.perf_counter()-tick
            count+=1;sequence+=1
        assert history.read()==b''
        stream.flush()
    assert count==61001 and snapshots==1001 and nulls==8000
    assert sum(len(c['deposits']) for c in parent['cells'])==11000
    return {'status':'PASS_ALL_ORIGINAL_ENVELOPES_AND_NEW_R2_SEALED_CODEC',
            'items':count,'snapshots':snapshots,'null_event_timestamps':nulls,
            'wall_s':time.perf_counter()-started,'phase_wall_s':dict(timings),
            'compact_bytes':target.stat().st_size,'compact_sha256':file_sha(target),'head':head,
            'scope':'read-only original trajectory conversion; bounded new numerical generation proved separately; not R2 1000Y evolution'}


def main():
    assert git('branch','--show-current')=='r6/runtime-copy-r1-fair' and git('rev-parse','HEAD')==BASE
    assert file_sha(ORACLE/'MANIFEST.json')==MANIFEST_SHA
    out=ROOT/'qualification';assert not out.exists();out.mkdir()
    paths=[*sorted((WORK/'src/arcana_worldsim/r6').glob('*.py')),Path(__file__),WORK/'tests/test_r6_runtime_compact_r2.py']
    sources={str(p.relative_to(WORK)):file_sha(p) for p in paths}
    save(out/'SOURCE_SHA256.json',sources)
    report={'schema':'ARCANA_RUNTIME_R2_BOUNDED_REPORT_V1','status':'RUNNING',
            'base_head':BASE,'git_status':git('status','--porcelain','--untracked-files=all'),
            'short_oracle':short_oracle(),'benchmarks':[],'python':sys.version,
            'r1_historical_1000y_loop_s':214.12557185068727,
            'R2_1000Y_NUMERICAL_RUN':'NOT_AUTHORIZED_NOT_RUN','R2_10000Y_NUMERICAL_RUN':'NOT_AUTHORIZED_NOT_RUN'}
    save(out/'REPORT.json',report)
    for year,span in [(101,1),(501,1),(751,1),(751,5)]:
        pair={}
        for mode in (['r1','r2'] if year!=501 else ['r2','r1']):
            dest=out/f'{mode}_y{year}_n{span}_REPORT.json'
            subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',mode,'--year',str(year),
                            '--span',str(span),'--output',str(out),'--report',str(dest)],check=True)
            pair[mode]=json.loads(dest.read_text())
        for field in ['checkpoint_sha256','query_sha256','compact_sha256','legacy_sha256','compact_bytes','legacy_bytes']:
            assert pair['r1']['samples'][0][field]==pair['r2']['samples'][0][field],(year,span,field)
        row={'year':year,'span':span,**pair,
             'hot_step_speedup':pair['r1']['medians']['engine_and_compact_ingest_s']/pair['r2']['medians']['engine_and_compact_ingest_s'],
             'compact_total_speedup':pair['r1']['medians']['compact_total_s']/pair['r2']['medians']['compact_total_s'],
             'full_service_speedup':pair['r1']['medians']['full_service_total_s']/pair['r2']['medians']['full_service_total_s']}
        report['benchmarks'].append(row);save(out/'REPORT.json',report)
        print('ANCHOR',year,'SPAN',span,'HOT',row['hot_step_speedup'],'COMPACT_TOTAL',row['compact_total_speedup'],'FULL_SERVICE',row['full_service_speedup'],flush=True)
    report['offline']=offline(out)
    assert sources=={name:file_sha(WORK/name) for name in sources},'SOURCE_DRIFT'
    assert file_sha(ORACLE/'MANIFEST.json')==MANIFEST_SHA
    report['status']='PASS_BOUNDED_EXACT_RECONSTRUCTION_AND_STRUCTURAL_ELIMINATION'
    report['limits']=['Canonical full snapshot SHA is deferred in hot frames; sealed codec costs are separate.',
                      'All original numerical scans and growing annual provenance arrays remain.',
                      'Fresh one-year initialization and checkpoint export remain O(D); report combined costs.',
                      'Scratch adapter is not B0 durability/atomic publication or production retention.']
    save(out/'REPORT.json',report)
    save(out/'MANIFEST.json',{'members':[{'path':p.name,'bytes':p.stat().st_size,'sha256':file_sha(p)} for p in sorted(out.iterdir()) if p.is_file()]})
    print('R2_BOUNDED='+report['status'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',choices=['r1','r2'])
    parser.add_argument('--year',type=int,choices=[101,501,751])
    parser.add_argument('--span',type=int,choices=[1,5],default=1)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    try:
        if args.worker:
            assert args.span==1 or args.year==751
            save(args.report,worker(args.worker,args.year,args.span,args.output))
        else:
            main()
    except BaseException:
        import traceback
        (ROOT/'BLOCKED_TRACEBACK.txt').write_text(traceback.format_exc())
        print('R2_BOUNDED=BLOCKED',flush=True)
        raise
