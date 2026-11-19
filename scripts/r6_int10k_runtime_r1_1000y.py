#!/usr/bin/env python3
"""Explicitly authorized one-off 1000Y candidate qualification; no resource caps.

No 10k mode, solver launch, source mutation or original evidence writes.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import resource
import statistics
import sys
import threading
import time
import traceback

from r6_int10k_runtime_r1 import (
    BASE, EVIDENCE, INPUT, MANIFEST_SHA, ORACLE, SOURCE_HASHES, WORK,
    canonical, file_sha, git, initial, save,
)
from arcana_worldsim.r6.regional_geological_evolution import RegionalConfig, run_regional_segment
from arcana_worldsim.r6.int10k_history_independent import verify_history_independent_checkpoint
import hashlib

PRIOR = EVIDENCE / "RUNTIME_R1_COPY_AUDIT_20261030_03"
MILESTONES = (100, 250, 500, 750, 1000)


def proc_status():
    fields = {}
    for line in Path('/proc/self/status').read_text().splitlines():
        key, _, value = line.partition(':')
        if key in ('VmRSS', 'VmHWM', 'Threads', 'Cpus_allowed_list'):
            fields[key] = value.strip()
    return fields


class Writer:
    def __init__(self, out, reference):
        self.history = (out / 'HISTORY.jsonl').open('xb', buffering=1024*1024)
        self.index = (out / 'INDEX.jsonl').open('xb', buffering=1024*1024)
        self.reference = iter(reference)
        self.sequence = 0
        self.counts = Counter()
        self.null_events = 0
        self.costs = Counter()
        self.history_hash = hashlib.sha256()
        self.index_hash = hashlib.sha256()

    def emit(self, kind, record):
        tick = time.perf_counter()
        payload = canonical(record)
        self.costs['payload_encode_s'] += time.perf_counter()-tick
        tick = time.perf_counter()
        sha = hashlib.sha256(payload).hexdigest()
        self.costs['payload_hash_s'] += time.perf_counter()-tick
        event_year = record.get('time_year', record.get('detected_at_year'))
        envelope = {'sequence': self.sequence, 'kind': kind,
                    'time_year': record.get('time_year', record.get('elapsed_years', event_year)),
                    'payload_sha256': sha, 'payload': record}
        tick = time.perf_counter()
        line = canonical(envelope) + b'\n'
        row = {'sequence': self.sequence, 'kind': kind, 'offset': self.history.tell(),
               'length': len(line), 'time_year': envelope['time_year'], 'payload_sha256': sha}
        index_line = canonical(row) + b'\n'
        self.costs['envelope_index_encode_s'] += time.perf_counter()-tick
        tick = time.perf_counter()
        expected = next(self.reference)
        if row != expected:
            raise ValueError(f'EXACT_ORACLE_INDEX_MISMATCH:{self.sequence}:{kind}')
        self.costs['oracle_compare_s'] += time.perf_counter()-tick
        tick = time.perf_counter()
        self.history.write(line)
        self.index.write(index_line)
        self.history_hash.update(line)
        self.index_hash.update(index_line)
        self.costs['write_and_stream_hash_s'] += time.perf_counter()-tick
        self.sequence += 1
        self.counts[kind] += 1
        if kind == 'REGIONAL_EVENT' and envelope['time_year'] is None:
            self.null_events += 1

    def flush(self):
        tick = time.perf_counter()
        for stream in (self.history, self.index):
            stream.flush()
            os.fsync(stream.fileno())
        self.costs['flush_fsync_s'] += time.perf_counter()-tick

    def close(self):
        try:
            self.flush()
        finally:
            self.history.close()
            self.index.close()


def main(out):
    start = time.perf_counter()
    assert git('rev-parse', 'HEAD') == BASE
    assert git('branch', '--show-current') == 'r6/runtime-copy-r1-fair'
    prior_sources = json.loads((PRIOR / 'SOURCE_SHA256.json').read_text())
    for name, expected in prior_sources.items():
        assert file_sha(WORK / name) == expected, ('QUALIFIED_CANDIDATE_DRIFT', name)
    assert file_sha(ORACLE / 'MANIFEST.json') == MANIFEST_SHA
    original_manifest = json.loads((ORACLE / 'MANIFEST.json').read_text())
    members = {row['path']: row for row in original_manifest['members']}
    for name, row in members.items():
        assert (ORACLE/name).stat().st_size == row['byte_length']
        assert file_sha(ORACLE/name) == row['sha256'], name
    sources = {**prior_sources, str(Path(__file__).resolve().relative_to(WORK)): file_sha(Path(__file__))}
    save(out/'SOURCE_SHA256.json', sources)
    for name in sources:
        target = out/'source'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((WORK/name).read_bytes())
    save(out/'AUTHORIZATION.json', {
        'user_authorization': 'non imporre limiti ma fa partire la simulazione',
        'scope': 'one candidate 1000Y annual-call qualification; no 10k',
        'application_resource_caps': None, 'site_policy_applies': True,
        'source_base': BASE, 'branch': git('branch', '--show-current'),
        'git_status': git('status', '--porcelain', '--untracked-files=all'),
        'python': sys.version, 'process': proc_status(),
        'original_manifest_sha256': MANIFEST_SHA,
        'prior_bounded_report_sha256': file_sha(PRIOR/'REPORT.json')})
    states, identity = initial()
    refs = [json.loads(line) for line in (ORACLE/'INDEX.jsonl').open()]
    assert len(refs) == 61001
    writer = Writer(out, refs)
    stop = threading.Event()
    sampler_errors = []
    def sample():
        try:
            with (out/'RESOURCE_SAMPLES.jsonl').open('x') as stream:
                while not stop.is_set():
                    stream.write(json.dumps({'elapsed_s': time.perf_counter()-start,
                                             **proc_status()})+'\n')
                    stream.flush()
                    stop.wait(1.0)
        except Exception:
            sampler_errors.append(traceback.format_exc())
    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    configuration = None
    checkpoint = None
    rows = []
    checkpoint_checks = []
    loop_start = time.perf_counter()
    cpu_start = resource.getrusage(resource.RUSAGE_SELF)
    try:
        with (out/'YEAR_METRICS.jsonl').open('xb') as metrics:
            for year in range(1, 1001):
                tick = time.perf_counter()
                cpu_before = resource.getrusage(resource.RUSAGE_SELF)
                engine_tick = time.perf_counter()
                result = run_regional_segment(
                    states, identity, config=RegionalConfig(duration_years=1000),
                    segment_years=1, checkpoint=checkpoint,
                    history_independent_continuation=True, history_consumer=writer.emit,
                    runtime_copy_optimization=True)
                engine_wall = time.perf_counter()-engine_tick
                assert result['state']['time_years'] == year
                assert len(result['state']['records']) == 1
                assert len(result['subsurface_unified_result']['steps']) == 1
                record = result['state']['records'][0]
                assert record['time_year'] == year
                for branch, tolerance in (('water_balance_m3', 'roundoff_tolerance'),
                                          ('solid_mass_balance_kg', 'roundoff_tolerance_kg')):
                    balance = record[branch]
                    assert math.isfinite(balance['residual']) and math.isfinite(balance[tolerance])
                    assert abs(balance['residual']) <= balance[tolerance], (year, branch)
                checkpoint = result['checkpoint']
                if configuration is None:
                    configuration = checkpoint['configuration']
                assert canonical(configuration) == canonical(checkpoint['configuration'])
                check_tick = time.perf_counter()
                verify_history_independent_checkpoint(checkpoint, source_identity=identity,
                                                       configuration=configuration)
                verify_wall = time.perf_counter()-check_tick
                assert checkpoint['history_high_water_mark'] == year
                assert checkpoint['history_prefix_required'] is False
                encode_tick = time.perf_counter()
                checkpoint_bytes = canonical(checkpoint)
                checkpoint_encode_wall = time.perf_counter()-encode_tick
                if year in MILESTONES:
                    writer.flush()
                    name = f'CHECKPOINT_{year:04d}.json'
                    sha = hashlib.sha256(checkpoint_bytes).hexdigest()
                    assert sha == members[name]['sha256'], ('CHECKPOINT_ORACLE_MISMATCH', year)
                    with (out/name).open('xb') as stream:
                        stream.write(checkpoint_bytes)
                        stream.flush()
                        os.fsync(stream.fileno())
                    checkpoint_checks.append({'year': year, 'sha256': sha, 'status': 'EXACT_PASS'})
                cpu_after = resource.getrusage(resource.RUSAGE_SELF)
                row = {'year': year, 'wall_step_s': time.perf_counter()-tick,
                       'engine_with_consumer_wall_s': engine_wall,
                       'outer_verify_wall_s': verify_wall,
                       'checkpoint_encode_wall_s': checkpoint_encode_wall,
                       'cpu_user_s': cpu_after.ru_utime-cpu_before.ru_utime,
                       'cpu_system_s': cpu_after.ru_stime-cpu_before.ru_stime,
                       'checkpoint_bytes': len(checkpoint_bytes),
                       'history_bytes': writer.history.tell(), 'index_bytes': writer.index.tell(),
                       'water_residual_m3': record['water_balance_m3']['residual'],
                       'solid_residual_kg': record['solid_mass_balance_kg']['residual'],
                       **proc_status()}
                rows.append(row)
                metrics.write(canonical(row)+b'\n')
                if year % 100 == 0 or year in MILESTONES:
                    print(f'YEAR={year} WALL_S={row["wall_step_s"]:.6f} HISTORY_BYTES={row["history_bytes"]} VmHWM={row["VmHWM"]} ORACLE=EXACT_PASS', flush=True)
                del result, checkpoint_bytes
            metrics.flush()
            os.fsync(metrics.fileno())
    finally:
        writer.close()
        stop.set()
        thread.join()
    loop_wall = time.perf_counter()-loop_start
    cpu_end = resource.getrusage(resource.RUSAGE_SELF)
    assert writer.sequence == len(refs) and next(writer.reference, None) is None
    assert len(checkpoint_checks) == 5 and not sampler_errors, sampler_errors
    for name, expected in sources.items():
        assert file_sha(WORK/name) == expected, ('SOURCE_DRIFT', name)
    for name, expected in SOURCE_HASHES.items():
        assert file_sha(INPUT/name) == expected
    for name, running_sha in (('HISTORY.jsonl', writer.history_hash), ('INDEX.jsonl', writer.index_hash)):
        assert file_sha(out/name) == running_sha.hexdigest() == members[name]['sha256'], name
        assert (out/name).stat().st_size == members[name]['byte_length'], name
    assert file_sha(ORACLE/'MANIFEST.json') == MANIFEST_SHA
    cpu_user = cpu_end.ru_utime-cpu_start.ru_utime
    cpu_system = cpu_end.ru_stime-cpu_start.ru_stime
    report = {'status': 'PASS_1000Y_CANDIDATE_EXACT_ORACLE',
              'classification': 'NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY',
              'source_base': BASE, 'measured_source_sha256': sources,
              'years': 1000, 'planned_years': 1000, 'segment_years': 1,
              'exact_ordered_payloads': writer.sequence, 'counts': dict(writer.counts),
              'null_timestamp_events': writer.null_events, 'checkpoint_oracle': checkpoint_checks,
              'history_and_index_whole_file_sha': 'EXACT_ORIGINAL_BYTES',
              'loop_wall_s': loop_wall, 'cpu_user_s': cpu_user, 'cpu_system_s': cpu_system,
              'equivalent_utilized_cores': (cpu_user+cpu_system)/loop_wall,
              'writer_wall_components_s': dict(writer.costs),
              'engine_with_consumer_wall_s': sum(r['engine_with_consumer_wall_s'] for r in rows),
              'outer_verify_wall_s': sum(r['outer_verify_wall_s'] for r in rows),
              'checkpoint_encode_wall_s': sum(r['checkpoint_encode_wall_s'] for r in rows),
              'resource_status_final': proc_status(),
              'annual_wall_median_s': statistics.median(r['wall_step_s'] for r in rows),
              'annual_wall_p95_s': sorted(r['wall_step_s'] for r in rows)[949],
              'annual_wall_max_s': max(r['wall_step_s'] for r in rows),
              'windows_100y': [{'first_year': start_year+1, 'last_year': start_year+100,
                               'wall_s': sum(r['wall_step_s'] for r in rows[start_year:start_year+100])}
                              for start_year in range(0, 1000, 100)],
              'end_to_end_before_final_manifest_wall_s': time.perf_counter()-start,
              'application_resource_caps': None, 'world_history_production_authorized': False,
              'int10k_authorized': False,
              'comparison_limit': 'One full candidate trajectory; historical baseline environment and verification overhead differ. Controlled speedup evidence remains the seven-repeat anchored audit.'}
    save(out/'REPORT.json', report)
    save(out/'MANIFEST.json', {'members': [
        {'path': str(p.relative_to(out)), 'byte_length': p.stat().st_size, 'sha256': file_sha(p)}
        for p in sorted(out.rglob('*')) if p.is_file()]})
    print('R6_RUNTIME_R1_1000Y=PASS_EXACT_ORIGINAL_HISTORY_INDEX_AND_FIVE_CHECKPOINTS', flush=True)
    print(f'LOOP_WALL_S={loop_wall:.6f} CPU_USER_S={cpu_user:.6f} CPU_SYSTEM_S={cpu_system:.6f}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert not output.exists() and not output.is_relative_to(WORK)
    output.mkdir(parents=True)
    print('OUTPUT='+str(output), flush=True)
    try:
        main(output)
    except BaseException:
        (output/'BLOCKED_TRACEBACK.txt').write_text(traceback.format_exc())
        print('R6_RUNTIME_R1_1000Y=BLOCKED', flush=True)
        raise
