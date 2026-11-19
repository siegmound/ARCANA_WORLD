#!/usr/bin/env python3
"""One explicitly authorized fresh R2 1000Y trajectory and exact disk qualification.

No 10k mode, timeout, memory/output/thread cap, physics edit or automatic retry.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import statistics
import subprocess
import sys
import threading
import time
import traceback

from r6_int10k_runtime_r1 import (
    BASE, EVIDENCE, INPUT, MANIFEST_SHA, ORACLE, SOURCE_HASHES, WORK,
    canonical, digest, file_sha, git, initial, save,
)
from r6_int10k_runtime_r1_1000y import proc_status
from arcana_worldsim.r6 import int10k_runtime_compact as compact
from arcana_worldsim.r6 import regional_geological_evolution as regional
from arcana_worldsim.r6 import unified_multiphysics_microdomain as unified
from arcana_worldsim.r6.int10k_history_independent import verify_history_independent_checkpoint

PRIOR = EVIDENCE/'RUNTIME_R2_STRUCTURAL_20261030_01'
PREFLIGHT = EVIDENCE/'RUNTIME_R2_1000Y_PREFLIGHT_20261030_01'
MILESTONES = (100, 250, 500, 750, 1000)
REPLAY_BASES = (100, 250, 500, 750, 999)
WITNESSES = (101, 251, 501, 751)
PASS = 'R2_1000Y=PASS_FRESH_TRAJECTORY_EXACT_RECONSTRUCTION_AND_MEASURED_RESOURCE_PROFILE'


class GateError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise GateError(reason)


def usage():
    r = resource.getrusage(resource.RUSAGE_SELF)
    return r.ru_utime, r.ru_stime


def disk_stats(folder):
    paths = [p for p in folder.rglob('*') if p.is_file()]
    return {'files': len(paths), 'logical_bytes': sum(p.stat().st_size for p in paths),
            'allocated_bytes': sum(p.stat().st_blocks*512 for p in paths)}


class DiskJournal:
    def __init__(self, folder):
        self.stream = (folder/'COMPACT.jsonl').open('xb', buffering=1024*1024)
        self.pending = []
        self.initial_head = self.head = None
        self.sequence = 0
        self.counts = Counter()
        self.null_events = 0
        self.file_hash = hashlib.sha256()
        self.callback_wall = 0.0
        self.flush_wall = 0.0
        self.kind_bytes = Counter()

    def bind(self, initial_head):
        self.initial_head = self.head = initial_head
        for kind, payload in self.pending:
            self.emit(kind, payload)
        self.pending.clear()

    def emit(self, kind, payload):
        if self.head is None:
            self.pending.append((kind, json.loads(canonical(payload))))
            return
        tick = time.perf_counter()
        body = {'schema': compact.STREAM_SCHEMA, 'sequence': self.sequence,
                'parent_sha256': self.head, 'kind': kind, 'payload': payload}
        sha = digest(body)
        encoded = canonical({**body, 'sha256': sha})+b'\n'
        self.stream.write(encoded)
        self.file_hash.update(encoded)
        self.head = sha
        self.sequence += 1
        self.counts[kind] += 1
        self.kind_bytes[kind] += len(encoded)
        if kind == 'REGIONAL_EVENT' and payload.get('time_year', payload.get('detected_at_year')) is None:
            self.null_events += 1
        self.callback_wall += time.perf_counter()-tick

    def flush(self):
        tick = time.perf_counter()
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.flush_wall += time.perf_counter()-tick

    def close(self):
        try:
            self.flush()
        finally:
            self.stream.close()


def new_runtime(states, identity, writer=None, checkpoint=None):
    runtime = compact.CompactRuntime(states, identity, config=regional.RegionalConfig(duration_years=1000),
            runtime_compact_history=True, checkpoint=checkpoint,
            consumer=writer.emit if writer else None)
    if writer:
        writer.bind(runtime.initial_head)
        require(writer.head == runtime.head, 'INITIAL_JOURNAL_HEAD_MISMATCH')
    return runtime


def source_index():
    return [json.loads(line) for line in (ORACLE/'INDEX.jsonl').open()]


def logical_rows(path, initial_head, final_head):
    """Owned serializer buffer; consumers finish encoding before next mutation."""
    snapshot = None
    with path.open('rb') as stream:
        for kind, payload in compact.verify_entries(stream, initial_head, final_head):
            if kind == 'REGIONAL_SNAPSHOT':
                require(snapshot is None and payload['time_year'] == 0, 'ROOT_SNAPSHOT_INVALID')
                snapshot = payload
            elif kind == 'REGIONAL_DELTA':
                require(payload['schema'] == compact.FRAME_SCHEMA
                        and payload['parent_snapshot_sha256'] is None
                        and payload['target_snapshot_sha256'] is None
                        and payload['canonical_sha_status'] == 'DEFERRED_UNTIL_MATERIALIZATION',
                        'UNSEALED_FRAME_MISLABELED')
                snapshot = compact._apply_owned(snapshot, payload)
                kind, payload = 'REGIONAL_SNAPSHOT', snapshot
            yield kind, payload


def reconstruct(folder, metadata, refs, destination):
    """Materialize fresh disk stream to authentic legacy bytes and indexed SHA."""
    destination.mkdir()
    tick = time.perf_counter(); before = usage()
    counts = Counter(); snapshots = nulls = 0
    hh = hashlib.sha256(); ih = hashlib.sha256()
    with (destination/'HISTORY.jsonl').open('xb', buffering=1024*1024) as history, \
         (destination/'INDEX.jsonl').open('xb', buffering=1024*1024) as index:
        for sequence, ((kind, payload), expected) in enumerate(zip(
                logical_rows(folder/'COMPACT.jsonl', metadata['initial_head'], metadata['head']), refs, strict=True)):
            sha = digest(payload)
            require((sequence, kind, sha) == (expected['sequence'], expected['kind'], expected['payload_sha256']),
                    f'PAYLOAD_ORACLE_MISMATCH_{sequence}')
            event_year = payload.get('time_year', payload.get('detected_at_year'))
            envelope = {'sequence': sequence, 'kind': kind,
                        'time_year': payload.get('time_year', payload.get('elapsed_years', event_year)),
                        'payload_sha256': sha, 'payload': payload}
            line = canonical(envelope)+b'\n'
            row = {'sequence': sequence, 'kind': kind, 'offset': history.tell(), 'length': len(line),
                   'time_year': envelope['time_year'], 'payload_sha256': sha}
            require(row == expected, f'RECONSTRUCTED_INDEX_MISMATCH_{sequence}')
            iline = canonical(row)+b'\n'
            history.write(line); index.write(iline); hh.update(line); ih.update(iline)
            counts[kind] += 1
            if kind == 'REGIONAL_SNAPSHOT':
                snapshots += 1
                require(len(payload['cells']) == 9, 'CELL_COVERAGE_INVALID')
                if payload['time_year'] % 250 == 0:
                    print('RECONSTRUCTION_YEAR='+str(payload['time_year']), flush=True)
                deposits = sum(len(c['deposits']) for c in payload['cells'])
            if kind == 'REGIONAL_EVENT' and envelope['time_year'] is None:
                nulls += 1
        for stream in (history, index):
            stream.flush(); os.fsync(stream.fileno())
    after = usage()
    return {'wall_s': time.perf_counter()-tick, 'cpu_user_s': after[0]-before[0],
            'cpu_system_s': after[1]-before[1], 'records': sum(counts.values()), 'counts': dict(counts),
            'snapshots': snapshots, 'null_event_timestamps': nulls, 'final_deposits': deposits,
            'history_sha256': hh.hexdigest(), 'index_sha256': ih.hexdigest(), **disk_stats(destination)}


class PhaseObserver:
    """Disjoint nested wall timers; instrumented cost is included in the run."""
    def __init__(self):
        self.times = Counter(); self.stack = []; self.saved = []

    def add(self, module, name, phase):
        original = getattr(module, name)
        self.saved.append((module, name, original))
        def wrapped(*args, **kwargs):
            frame = [time.perf_counter(), 0.0]; self.stack.append(frame)
            try:
                return original(*args, **kwargs)
            finally:
                elapsed = time.perf_counter()-frame[0]; self.stack.pop()
                self.times[phase] += elapsed-frame[1]
                if self.stack:
                    self.stack[-1][1] += elapsed
        setattr(module, name, wrapped)

    def start(self):
        for module, name, phase in [
            (regional, 'advance_region', 'regional_other_including_stock_scans'),
            (regional, '_geologic_load', 'geologic_load_scans'),
            (regional, '_hydraulic_radius_m', 'hydraulic_numeric'),
            (regional, '_canonical', 'json_encoding'),
            (unified, 'solve_layered_interface_increment', 'kernel_mechanics'),
            (unified, 'pure_shear_thermal_step', 'kernel_thermal'),
            (unified, '_new_hydrology_state', 'kernel_hydrology'),
            (unified, '_advance_reservoirs', 'kernel_deep'),
            (unified, 'seal_unified_checkpoint', 'unified_checkpoint'),
            (unified, 'verify_unified_checkpoint', 'unified_checkpoint'),
            (compact, '_copy', 'nonhistorical_copy_decode'),
            (compact, '_sha', 'compact_hash_other'),
            (compact._CompactOwner, 'frame', 'delta_creation_other'),
            (compact.CompactRuntime, '_emit', 'compact_ingest_other'),
            (DiskJournal, 'emit', 'disk_journal_other'),
        ]:
            self.add(module, name, phase)

    def close(self):
        for module, name, original in reversed(self.saved):
            setattr(module, name, original)


class Sampler:
    def __init__(self, folder):
        self.folder = folder; self.stop = threading.Event(); self.errors = []
        self.peak_tree_rss_kib = 0

    def run(self):
        try:
            with (self.folder/'RESOURCE_SAMPLES.jsonl').open('x') as stream:
                while not self.stop.is_set():
                    children = Path(f'/proc/self/task/{os.getpid()}/children').read_text().split()
                    statuses = {str(os.getpid()): proc_status()}
                    for pid in children:
                        try:
                            statuses[pid] = {k:v.strip() for k,v in (x.split(':',1) for x in Path(f'/proc/{pid}/status').read_text().splitlines() if ':' in x)
                                             if k in ('VmRSS','VmHWM','Threads')}
                        except FileNotFoundError:
                            pass
                    tree = sum(int(s.get('VmRSS','0 kB').split()[0]) for s in statuses.values())
                    self.peak_tree_rss_kib = max(self.peak_tree_rss_kib, tree)
                    stream.write(json.dumps({'monotonic':time.perf_counter(),'processes':statuses,'tree_rss_kib':tree})+'\n')
                    stream.flush(); self.stop.wait(1.0)
        except BaseException:
            self.errors.append(traceback.format_exc())


def preflight(out):
    started = time.perf_counter()
    require(git('branch','--show-current') == 'r6/runtime-copy-r1-fair' and git('rev-parse','HEAD') == BASE,
            'SOURCE_OR_ORACLE_MISMATCH')
    source = json.loads((PRIOR/'qualification/SOURCE_SHA256.json').read_text())
    r1_backup = json.loads((PRIOR/'R1_BACKUP_MANIFEST.json').read_text())['files']
    for name in ['scripts/r6_int10k_runtime_r1.py','scripts/r6_int10k_runtime_r1_1000y.py',
                 'tests/test_r6_runtime_copy_r1.py','docs/arcana/R6_RUNTIME_COPY_R1_FAIR_20261030.md']:
        require(file_sha(WORK/name) == r1_backup[name], 'R1_PRESERVED_SOURCE_MISMATCH')
        source[name] = r1_backup[name]
    for name, sha in source.items():
        require(file_sha(WORK/name) == sha, 'SOURCE_OR_ORACLE_MISMATCH_'+Path(name).name)
    for name, sha in [('R1_TRACKED.patch','1c868b243da5375bb5c948d3bbc9c57290828a5cb367a35e08b117ab35467c67'),
                      ('R2_AGAINST_PRESERVED_R1.patch','965f463559a618e100af85950513f97832714608169ef682e9c5103163371c9a'),
                      ('QUALIFICATION_SUMMARY.json','40e38ae967c8b396c8433fe677717d0445a139c6e5f2fc257fb3f8025cb04642')]:
        require(file_sha(PRIOR/name) == sha, 'PRIOR_QUALIFICATION_MISMATCH')
    require(file_sha(ORACLE/'MANIFEST.json') == MANIFEST_SHA, 'SOURCE_OR_ORACLE_MISMATCH')
    manifest = json.loads((ORACLE/'MANIFEST.json').read_text())
    for row in manifest['members']:
        require(file_sha(ORACLE/row['path']) == row['sha256'], 'SOURCE_OR_ORACLE_MISMATCH_'+row['path'])
    require(file_sha(EVIDENCE/'RUNTIME_R1_CANDIDATE_1000Y_20261030_01/MANIFEST.json') ==
            '3142804095c065f46c740a7ab0a21ff32160ac00b73053f8eaf78d6a2db1840b', 'R1_EVIDENCE_MISMATCH')
    context = json.loads((PREFLIGHT/'SITE_CONTEXT_APPROVED.json').read_text())
    require(context['current_session'] == Path('/proc/self/cgroup').read_text().strip()
            and context['operator_interactive_authorization'] is True, 'SITE_CONTEXT_NOT_APPROVED')
    states, identity = initial()
    source[str(Path(__file__).resolve().relative_to(WORK))] = file_sha(Path(__file__))
    save(out/'SOURCE_SHA256.json', source)
    save(out/'AUTHORIZATION_AND_SITE_CONTEXT.json', context)
    save(out/'GIT_PROVENANCE.json', {'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),
                                    'status':git('status','--porcelain','--untracked-files=all')})
    for name in source:
        p = out/'source'/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes((WORK/name).read_bytes())
    tests = ['tests/test_r6_runtime_compact_r2.py','tests/test_r6_runtime_copy_r1.py',
             'tests/test_r6_int10k_e2c1_r3_excluded_history_validation.py','tests/test_r6_int10k_e2c1_frontier_projection.py',
             'tests/test_r6_int10k_history_independent.py','tests/test_r6_regional_geological_evolution.py',
             'tests/test_r6_int10k_frontier_checkpoint.py','tests/test_r6_int10k_full_history_oracle.py',
             'tests/test_r6_int10k_short_reference.py','tests/test_r6_int10k_source_provenance.py',
             'tests/test_r6_int10k_surface_small_uplift_precision.py','tests/test_r6_unified_multiphysics_microdomain.py']
    tested = subprocess.run([sys.executable,'-m','pytest','-q','-p','no:cacheprovider',*tests],
                            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (out/'P0_TESTS.log').write_text(tested.stdout)
    require(tested.returncode == 0 and '168 passed' in tested.stdout, 'PREFLIGHT_TESTS_FAILED')
    refs = source_index()
    smoke = out/'P0_SMOKE'; smoke.mkdir()
    writer = DiskJournal(smoke)
    try:
        runtime = new_runtime(states,identity,writer)
        runtime.advance(3)
        require(writer.head == runtime.head, 'SMOKE_CHAIN_MISMATCH')
        cp = runtime.checkpoint()
        expected = json.loads((ORACLE/'CHECKPOINT_0100.json').read_text())['configuration']
        require(canonical(cp['configuration']) == canonical(expected), 'PHYSICAL_CONFIGURATION_MISMATCH')
    finally:
        writer.close()
    metadata = {'initial_head':writer.initial_head,'head':writer.head}
    smoke_result = reconstruct(smoke,metadata,refs[:184],smoke/'LEGACY')
    require(smoke_result['records']==184, 'SMOKE_COVERAGE_INVALID')
    save(out/'P0_SMOKE.json',smoke_result)
    print('P0=PASS_SOURCE_INTEGRITY_168_TESTS_CONFIG_AND_FRESH_3Y_DISK_SMOKE',flush=True)
    return states,identity,source,refs,manifest,time.perf_counter()-started


def execute(out):
    started = time.perf_counter()
    states,identity,sources,refs,oracle_manifest,p0_wall = preflight(out)
    archive = out/'archive'; archive.mkdir()
    writer = DiskJournal(archive)
    observer = PhaseObserver(); observer.start()
    setup_tick = time.perf_counter()
    runtime = new_runtime(states,identity,writer)
    cold_setup = time.perf_counter()-setup_tick
    sampler = Sampler(out); thread = threading.Thread(target=sampler.run,daemon=True); thread.start()
    rows=[]; checkpoints=[]; witnesses={}
    loop_tick=time.perf_counter(); cpu_before=usage()
    try:
        with (out/'YEAR_METRICS.jsonl').open('xb') as metrics:
            for year in range(1,1001):
                before=usage(); tick=time.perf_counter(); phases=observer.times.copy()
                old_metrics=runtime.metrics
                runtime.advance()
                hot=time.perf_counter()-tick; after=usage()
                phase_delta={k:observer.times[k]-phases[k] for k in observer.times}
                require(runtime.time_year==year and writer.head==runtime.head, 'LIVE_CLOCK_OR_CHAIN_MISMATCH')
                require(runtime.metrics['deposit_rows_exported']-old_metrics['deposit_rows_exported']==11,
                        'NONINCREMENTAL_DEPOSIT_EXPORT')
                balances=runtime.balances()
                for key,tolerance in [('water','roundoff_tolerance'),('solid_mass_kg','roundoff_tolerance_kg')]:
                    b=balances[key]
                    require(math.isfinite(b['residual']) and math.isfinite(b[tolerance])
                            and abs(b['residual'])<=b[tolerance], 'BALANCE_FAILED_'+key)
                cp_wall=0.0
                if year in MILESTONES or year in WITNESSES or year==999:
                    ct=time.perf_counter(); cp=runtime.checkpoint()
                    verify_history_independent_checkpoint(cp,source_identity=identity,configuration=cp['configuration'])
                    encoded=canonical(cp); sha=hashlib.sha256(encoded).hexdigest()
                    name=f'CHECKPOINT_{year:04d}.json'
                    if year in MILESTONES or year==999:
                        with (archive/name).open('xb') as stream:
                            stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
                    if year in MILESTONES:
                        require(sha==file_sha(ORACLE/name), 'CHECKPOINT_ORACLE_MISMATCH_'+str(year))
                    witnesses[str(year)]=sha
                    cp_wall=time.perf_counter()-ct
                    checkpoints.append({'year':year,'wall_s':cp_wall,'bytes':len(encoded),'sha256':sha,
                                        'persisted':year in MILESTONES or year==999,'original_milestone':year in MILESTONES})
                    writer.flush()
                row={'year':year,'hot_advance_compact_wall_s':hot,'cpu_user_s':after[0]-before[0],
                     'cpu_system_s':after[1]-before[1],'checkpoint_service_wall_s':cp_wall,
                     'phase_exclusive_wall_s':phase_delta,'compact_bytes':writer.stream.tell(),
                     'structural_metrics':runtime.metrics,'water_residual':balances['water']['residual'],
                     'solid_residual':balances['solid_mass_kg']['residual'],**proc_status()}
                rows.append(row);metrics.write(canonical(row)+b'\n')
                if year%100==0 or year in MILESTONES:
                    print(f'YEAR={year} HOT_S={hot:.6f} COMPACT_BYTES={writer.stream.tell()} VmHWM={row["VmHWM"]}',flush=True)
            metrics.flush();os.fsync(metrics.fileno())
    finally:
        observer.close(); writer.close()
    loop_wall=time.perf_counter()-loop_tick; cpu_after=usage()
    metadata={'schema':compact.STREAM_SCHEMA,'initial_head':writer.initial_head,'head':writer.head,
              'records':writer.sequence,'counts':dict(writer.counts),'null_event_timestamps':writer.null_events,
              'source_identity':identity,'planned_years':1000,'external_step_years':1,'segment_years':1,
              'compact_sha256':writer.file_hash.hexdigest(),'checkpoint_witnesses':witnesses,
              'full_snapshot_sha_status':'DEFERRED_UNTIL_MATERIALIZATION',
              'native_checkpoint_schema':'ORIGINAL_HISTORY_INDEPENDENT_CHECKPOINT_V1'}
    save(archive/'STREAM_METADATA.json',metadata)
    require(writer.sequence==61001 and writer.null_events==8000 and writer.counts==Counter({
        'REGIONAL_SNAPSHOT':1,'REGIONAL_DELTA':1000,'REGIONAL_EVENT':58000,'REGIONAL_YEAR_RECORD':1000,'UNIFIED_STEP':1000}),
        'COMPACT_COVERAGE_INVALID')
    require(file_sha(archive/'COMPACT.jsonl')==writer.file_hash.hexdigest(), 'COMPACT_DISK_HASH_MISMATCH')
    report={'status':'FRESH_TRAJECTORY_COMPLETE_DOWNSTREAM_PENDING','p0_wall_s':p0_wall,
            'cold_setup_s':cold_setup,'loop_with_checkpoint_observation_wall_s':loop_wall,
            'hot_advance_compact_wall_s':sum(r['hot_advance_compact_wall_s'] for r in rows),
            'loop_cpu_user_s':cpu_after[0]-cpu_before[0],'loop_cpu_system_s':cpu_after[1]-cpu_before[1],
            'disk_journal_callback_wall_s':writer.callback_wall,'flush_fsync_wall_s':writer.flush_wall,
            'checkpoints':checkpoints,'phase_hot_exclusive_wall_s':dict(sum_counters(rows)),
            'hot_annual_median_s':statistics.median(r['hot_advance_compact_wall_s'] for r in rows),
            'hot_annual_p95_s':sorted(r['hot_advance_compact_wall_s'] for r in rows)[949],
            'hot_annual_max_s':max(r['hot_advance_compact_wall_s'] for r in rows),
            'windows_100y':[{'first':i+1,'last':i+100,'hot_wall_s':sum(r['hot_advance_compact_wall_s'] for r in rows[i:i+100]),
                            'cpu_user_s':sum(r['cpu_user_s'] for r in rows[i:i+100]),
                            'cpu_system_s':sum(r['cpu_system_s'] for r in rows[i:i+100])} for i in range(0,1000,100)],
            'loop_end_status':proc_status(),'archive_bytes_before_downstream':disk_stats(archive),
            'compact_bytes_by_kind':dict(writer.kind_bytes),'restart_checks':[]}
    save(out/'REPORT_IN_PROGRESS.json',report)
    try:
        reconstruction=reconstruct(archive,metadata,refs,out/'LEGACY_RECONSTRUCTED')
        require(reconstruction['records']==61001 and reconstruction['snapshots']==1001
                and reconstruction['null_event_timestamps']==8000 and reconstruction['final_deposits']==11000,
                'RECONSTRUCTION_COVERAGE_INVALID')
        original={r['path']:r for r in oracle_manifest['members']}
        readback_tick=time.perf_counter(); readback_cpu=usage()
        for name in ['HISTORY.jsonl','INDEX.jsonl']:
            require(file_sha(out/'LEGACY_RECONSTRUCTED'/name)==original[name]['sha256'], 'LEGACY_DISK_READBACK_MISMATCH_'+name)
        readback_after=usage()
        report['legacy_full_disk_readback']={'wall_s':time.perf_counter()-readback_tick,
            'cpu_user_s':readback_after[0]-readback_cpu[0],'cpu_system_s':readback_after[1]-readback_cpu[1],
            'status':'WHOLE_HISTORY_AND_INDEX_SHA_EXACT_ORIGINAL'}
        report['reconstruction']=reconstruction
        report['restart_checks']=restart_checks(archive,witnesses,states,identity,refs)
        report['historical_queries']=historical_queries(archive,metadata,refs,out)
        for name,sha in sources.items():
            require(file_sha(WORK/name)==sha, 'SOURCE_CHANGED_DURING_RUN')
        for name,sha in SOURCE_HASHES.items():
            require(file_sha(INPUT/name)==sha, 'INPUT_CHANGED_DURING_RUN')
        require(file_sha(ORACLE/'MANIFEST.json')==MANIFEST_SHA, 'ORIGINAL_MANIFEST_CHANGED')
        for entry in oracle_manifest['members']:
            require(file_sha(ORACLE/entry['path'])==entry['sha256'], 'ORIGINAL_EVIDENCE_CHANGED')
    finally:
        sampler.stop.set();thread.join()
    require(not sampler.errors, 'RESOURCE_SAMPLER_FAILED')
    report.update({'status':PASS.split('=',1)[1],'marker':PASS,'end_to_end_before_manifest_s':time.perf_counter()-started,
                       'process_status':proc_status(),'sampled_peak_process_tree_rss_kib':sampler.peak_tree_rss_kib,
                       'archive_bytes':disk_stats(archive),'legacy_bytes':disk_stats(out/'LEGACY_RECONSTRUCTED'),
                       'all_output_before_report_manifest':disk_stats(out),'source_sha256':sources,
                       'application_resource_caps':None,'int10k_execution_authorized':False,
                       'world_history_production_authorized':False,'geodyn_2b_arcana_forward_authorized':False,
                       'f2b_solver_execution_authorized':False,'arcana_si1_mechanics_qualified':False,
                       'measurement_scope':'Instrumented run; named kernels are a subset. Compact-only differs from historical R1 full-output service. No repeated full-run speedup claim.'})
    save(out/'REPORT.json',report)
    save(out/'MANIFEST.json',{'members':[{'path':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':file_sha(p)}
                                       for p in sorted(out.rglob('*')) if p.is_file()]})
    print(PASS,flush=True)


def sum_counters(rows):
    result=Counter()
    for row in rows:
        result.update(row['phase_exclusive_wall_s'])
    return result


def restart_checks(archive,witnesses,states,identity,refs):
    results=[]
    # Each independent runtime imports a serialized checkpoint; master is not advanced.
    for base in REPLAY_BASES:
        tick=time.perf_counter();before=usage()
        cp=json.loads((archive/f'CHECKPOINT_{base:04d}.json').read_bytes())
        resumed=new_runtime(states,identity,checkpoint=cp)
        resumed.advance()
        expected=[(r['kind'],r['payload_sha256']) for r in refs[1+base*61:1+(base+1)*61]]
        actual=[(kind,digest(payload)) for kind,payload in resumed.legacy_history()]
        require(actual==expected,'RESTART_PAYLOAD_MISMATCH_'+str(base))
        require(digest(resumed.checkpoint())==witnesses[str(base+1)],'RESTART_FRONTIER_MISMATCH_'+str(base))
        after=usage();results.append({'base_year':base,'target_year':base+1,'status':'EXACT_PAYLOADS_AND_CONTINUOUS_CHECKPOINT',
              'wall_s':time.perf_counter()-tick,'cpu_user_s':after[0]-before[0],'cpu_system_s':after[1]-before[1]})
    terminal=new_runtime(states,identity,checkpoint=json.loads((archive/'CHECKPOINT_1000.json').read_bytes()))
    require(digest(terminal.checkpoint())==witnesses['1000'],'TERMINAL_RESTORE_MISMATCH')
    try:
        terminal.advance()
    except compact.CompactError:
        pass
    else:
        raise GateError('TERMINAL_HORIZON_NOT_ENFORCED')
    save(archive/'RESTART_CHECKS.json',{'checks':results,'terminal_restore':'EXACT_PASS',
          'terminal_continuation':'999->1000 verified; advancing 1000->1001 correctly rejected under planned horizon 1000'})
    return results


def historical_queries(archive,metadata,refs,out):
    results=[]
    for year in [0,101,501,751,1000]:
        tick=time.perf_counter();before=usage();answer=None;deep=None
        # Full chain validation is included even after the requested year.
        for kind,payload in logical_rows(archive/'COMPACT.jsonl',metadata['initial_head'],metadata['head']):
            if kind=='UNIFIED_STEP' and payload['step']==year:
                deep=json.loads(canonical(payload['deep']))
            if kind=='REGIONAL_SNAPSHOT' and payload['time_year']==year:
                require(digest(payload)==next(r['payload_sha256'] for r in refs if r['kind']=='REGIONAL_SNAPSHOT' and r['time_year']==year),
                        'HISTORICAL_QUERY_SNAPSHOT_MISMATCH')
                cell=next(c for c in payload['cells'] if c.get('support_id'))
                answer={'time_year':year,'cell':json.loads(canonical(cell))}
        require(answer is not None,'HISTORICAL_QUERY_MISSING')
        if year:
            with (ORACLE/'HISTORY.jsonl').open('rb') as stream:
                ix=next(r for r in refs if r['kind']=='UNIFIED_STEP' and r['time_year']==year)
                stream.seek(ix['offset']);old=json.loads(stream.read(ix['length']))['payload']['deep']
            require(canonical(deep)==canonical(old),'HISTORICAL_DEEP_QUERY_MISMATCH')
            answer['deep']=deep
        after=usage();results.append({'year':year,'status':'EXACT_CELL_MATERIAL_SNAPSHOT_AND_DEEP' if year else 'EXACT_T0_CELL_NO_UNIFIED_STEP_AT_ZERO',
                  'wall_s':time.perf_counter()-tick,'cpu_user_s':after[0]-before[0],'cpu_system_s':after[1]-before[1],
                  'answer_sha256':digest(answer),'method':'cold whole closed stream scan and chain verification; no query index'})
    save(out/'HISTORICAL_QUERIES.json',results)
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve()
    require(not out.exists() and not out.is_relative_to(WORK),'OUTPUT_MUST_BE_NEW_EXTERNAL_DIRECTORY')
    out.mkdir(parents=True)
    print('OUTPUT='+str(out),flush=True)
    try:
        execute(out)
    except BaseException as exc:
        marker='R2_1000Y=BLOCKED_'+(str(exc) if isinstance(exc,GateError) else type(exc).__name__)
        (out/'BLOCKED_TRACEBACK.txt').write_text(traceback.format_exc())
        save(out/'REPORT_BLOCKED.json',{'marker':marker,'reason':str(exc),'automatic_retry':False})
        print(marker,flush=True)
        raise
