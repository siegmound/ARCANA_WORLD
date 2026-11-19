#!/usr/bin/env python3
"""L1 opt-in launcher. Preparing a contract never advances the solver.

Numerical operators, R2 and REC1 are imported unchanged. B0 publication remains
coupled to full checkpoints; journal-only fsync never grants resume authority.
"""
import argparse
from collections import defaultdict
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import statistics
import sys
import time
import uuid

from r6_int10k_runtime_r1 import INPUT, SOURCE_HASHES, load_verified_r6_initial_columns
from arcana_worldsim.r6 import int10k_runtime_compact as compact
from arcana_worldsim.r6.runtime_recovery import RecoveryController, file_sha
from arcana_worldsim.r6.runtime_run_plan import AnnualUpliftPlan
from arcana_worldsim.r6.geological_surface_microdomain import SUPPORTS

WORK = Path(__file__).resolve().parents[1]
SCHEMA = 'ARCANA_R6_L1_LAUNCH_CONTRACT_V1'


class LauncherError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise LauncherError(message)


def encode(value):
    return compact.regional._canonical(value)


def sha(value):
    return hashlib.sha256(encode(value)).hexdigest()


def save(path, value):
    with path.open('xb') as stream:
        stream.write(encode(value) + b'\n'); stream.flush(); os.fsync(stream.fileno())


def source_pins():
    paths = sorted((WORK/'src/arcana_worldsim/r6').glob('*.py'))
    paths += [Path(__file__).resolve(), WORK/'scripts/r6_int10k_runtime_r1.py']
    return {str(p.relative_to(WORK)): file_sha(p) for p in paths}


def validate_contract(contract, *, authenticate=True):
    fields = {'schema', 'planned_years', 'external_step_years', 'uplift', 'source_sha256',
              'input_root', 'input_sha256', 'archive_service', 'query_years',
              'journal_fsync_interval_years', 'journal_commit_interval_years', 'checkpoint_interval_years'}
    require(type(contract) is dict and set(contract) == fields and contract['schema'] == SCHEMA,
            'CONTRACT_FIELDS_OR_SCHEMA_INVALID')
    for key in ('planned_years', 'journal_fsync_interval_years', 'journal_commit_interval_years', 'checkpoint_interval_years'):
        require(type(contract[key]) is int and contract[key] > 0, 'CONTRACT_POSITIVE_INTEGER_REQUIRED')
    require(contract['external_step_years'] == 1, 'ANNUAL_ADVANCE_REQUIRED')
    require(contract['journal_commit_interval_years'] == contract['checkpoint_interval_years'],
            'INDEPENDENT_JOURNAL_PUBLICATION_UNQUALIFIED')
    require(contract['archive_service'] in ('compact_query', 'legacy_full'), 'ARCHIVE_SERVICE_INVALID')
    query = contract['query_years']
    require(type(query) is list and len(set(query)) == len(query)
            and all(type(y) is int and 0 <= y <= contract['planned_years'] for y in query), 'QUERY_YEAR_INVALID')
    plan = AnnualUpliftPlan(contract['planned_years'], contract['uplift']['annual_uplift_m_by_support'])
    require(plan.to_dict() == contract['uplift'], 'UPLIFT_CONTRACT_INVALID')
    require(contract['input_sha256'] == SOURCE_HASHES, 'E0_EXPECTED_PINS_CHANGED')
    root = Path(contract['input_root'])
    require(root.is_absolute() and root.is_dir(), 'E0_ROOT_INVALID')
    if authenticate:
        require(contract['source_sha256'] == source_pins(), 'LAUNCHER_SOURCE_IDENTITY_MISMATCH')
        for name, digest in SOURCE_HASHES.items():
            p = root/name
            require(p.is_file() and not p.is_symlink() and file_sha(p) == digest, 'E0_INPUT_IDENTITY_MISMATCH')
    return plan


def make_contract(*, planned_years, checkpoint_interval_years, journal_fsync_interval_years,
                  journal_commit_interval_years, archive_service, query_years, input_root=INPUT):
    plan = AnnualUpliftPlan(planned_years, {SUPPORTS[0]: 0.0001, SUPPORTS[1]: 0.0})
    value = {'schema': SCHEMA, 'planned_years': planned_years, 'external_step_years': 1,
             'uplift': plan.to_dict(), 'source_sha256': source_pins(), 'input_root': str(Path(input_root).resolve()),
             'input_sha256': dict(SOURCE_HASHES), 'archive_service': archive_service,
             'query_years': list(query_years), 'checkpoint_interval_years': checkpoint_interval_years,
             'journal_fsync_interval_years': journal_fsync_interval_years,
             'journal_commit_interval_years': journal_commit_interval_years}
    validate_contract(value)
    return value


def read_contract(path, expected_sha):
    require(path.is_file() and not path.is_symlink() and file_sha(path) == expected_sha, 'CONTRACT_FILE_SHA_MISMATCH')
    contract = json.loads(path.read_bytes())
    validate_contract(contract)
    return contract


def context():
    cgroup = Path('/proc/self/cgroup').read_text()
    group = Path('/sys/fs/cgroup')/cgroup.split('::', 1)[1].strip().lstrip('/')
    return {'hostname': os.uname().nodename, 'affinity': sorted(os.sched_getaffinity(0)),
            'cgroup': cgroup, 'effective_cgroup': {name: (group/name).read_text().strip()
                for name in ('cpu.max', 'memory.max', 'memory.current', 'memory.peak', 'cpuset.cpus.effective')
                if (group/name).exists()},
            'thread_environment': {k: v for k, v in os.environ.items() if k.startswith(('OMP_', 'MKL_', 'OPENBLAS_', 'SLURM_', 'PBS_'))},
            'limits': Path('/proc/self/limits').read_text(), 'account_quota': 'UNKNOWN_NOT_EXPOSED'}


def usage():
    value = resource.getrusage(resource.RUSAGE_SELF)
    return value.ru_utime, value.ru_stime


def memory():
    status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    own = {key: status[key].strip() for key in ('VmRSS', 'VmHWM', 'Threads')}
    # Observed descendants, not cgroup memory. This launcher spawns no solvers.
    children = Path(f'/proc/self/task/{os.getpid()}/children')
    own['direct_child_pids'] = children.read_text().split() if children.exists() else []
    group = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().split('::', 1)[1].strip().lstrip('/')
    own['shared_cgroup_bytes'] = {key: (group/key).read_text().strip()
                                 for key in ('memory.current', 'memory.peak') if (group/key).exists()}
    tree = 0; pending = [str(os.getpid())]; seen = set()
    while pending:
        pid = pending.pop()
        if pid in seen: continue
        seen.add(pid)
        try:
            values = dict(line.split(':', 1) for line in Path(f'/proc/{pid}/status').read_text().splitlines() if ':' in line)
            tree += int(values.get('VmRSS', '0 kB').split()[0])
            pending.extend(Path(f'/proc/{pid}/task/{pid}/children').read_text().split())
        except (OSError, ValueError):
            pass  # a sampled descendant may exit between reads
    own['sampled_process_tree_rss_kib'] = tree
    own['sampled_process_tree_pids'] = sorted(seen)
    return own


def disk(root):
    result = {}
    for name in ('chunks', 'frontiers', 'b0', 'active', 'invocations'):
        paths = [p for p in (root/name).rglob('*') if p.is_file()] if (root/name).exists() else []
        result[name] = {'files': len(paths), 'logical_bytes': sum(p.stat().st_size for p in paths),
                        'allocated_bytes': sum(p.stat().st_blocks*512 for p in paths)}
    return result


@contextmanager
def phases(controller):
    """Disjoint timings; operator groups retain scans/bookkeeping. Restore always."""
    totals = defaultdict(float); stack = []; originals = []
    def wrap(obj, name, label):
        original = getattr(obj, name); originals.append((obj, name, original))
        def timed(*args, **kwargs):
            frame = [time.perf_counter(), 0.0]; stack.append(frame)
            try:
                return original(*args, **kwargs)
            finally:
                elapsed = time.perf_counter()-frame[0]; stack.pop()
                totals[label] += elapsed-frame[1]
                if stack: stack[-1][1] += elapsed
        setattr(obj, name, timed)
    for obj, name, label in (
        (compact.unified, 'run_unified_microdomain', 'unified_operator_other_s'),
        (compact.unified, 'continue_unified_microdomain', 'unified_operator_other_s'),
        (compact.regional, 'advance_region', 'regional_operator_other_s'),
        (compact._CompactOwner, 'frame', 'compact_frame_s'),
        (compact.CompactRuntime, '_emit', 'compact_copy_encode_hash_s'),
    ): wrap(obj, name, label)
    # Instance wrapper: CompactRuntime retained a bound consumer at construction.
    original_consumer = controller.runtime._consumer
    def consumer(kind, payload):
        frame = [time.perf_counter(), 0.0]; stack.append(frame)
        try: return original_consumer(kind, payload)
        finally:
            elapsed = time.perf_counter()-frame[0]; stack.pop(); totals['writer_encode_write_s'] += elapsed-frame[1]
            if stack: stack[-1][1] += elapsed
    controller.runtime._consumer = consumer
    try:
        yield totals
    finally:
        controller.runtime._consumer = original_consumer
        for obj, name, original in reversed(originals): setattr(obj, name, original)


def _owned_committed_rows(controller):
    """Private synchronous serializer buffer. Never return it to a public reader.

    REC1 verifies the complete pinned lineage first. Reuse its authenticated rows;
    apply new deposits once, without detaching every unrequested historical state.
    The caller must finish encoding each row before requesting the next one.
    """
    chain, _ = controller._load_chain()
    snapshot = None
    for _, descriptor, _ in chain:
        for kind, payload in controller._rows(descriptor):
            if kind == 'REGIONAL_SNAPSHOT':
                snapshot = payload
            elif kind == 'REGIONAL_DELTA':
                snapshot = compact._apply_owned(snapshot, payload)
                kind, payload = 'REGIONAL_SNAPSHOT', snapshot
            yield kind, payload


def services(controller, invocation, contract):
    """Only B0-committed full context is eligible. Uncommitted tail is ignored."""
    wanted = {y for y in contract['query_years'] if y <= controller.last_native['time_year']}
    tick = time.perf_counter(); found = set(); rows = 0; nulls = 0; snapshots_encoded = 0
    legacy = (invocation/'LEGACY_HISTORY.jsonl').open('xb') if contract['archive_service'] == 'legacy_full' else None
    index = (invocation/'LEGACY_INDEX.jsonl').open('xb') if legacy else None
    try:
        if wanted or legacy:
            for kind, payload in _owned_committed_rows(controller):
                rows += 1
                nulls += int(kind == 'REGIONAL_EVENT' and payload.get('time_year') is None)
                if legacy:
                    snapshots_encoded += int(kind == 'REGIONAL_SNAPSHOT')
                    payload_sha = sha(payload)
                    event_year = payload.get('time_year', payload.get('detected_at_year'))
                    envelope = {'sequence': rows-1, 'kind': kind,
                        'time_year': payload.get('time_year', payload.get('elapsed_years', event_year)),
                        'payload_sha256': payload_sha, 'payload': payload}
                    line = encode(envelope)+b'\n'
                    index.write(encode({'sequence': rows-1, 'kind': kind, 'offset': legacy.tell(),
                        'length': len(line), 'time_year': envelope['time_year'], 'payload_sha256': payload_sha})+b'\n')
                    legacy.write(line)
                if kind == 'REGIONAL_SNAPSHOT' and payload['time_year'] in wanted:
                    snapshots_encoded += 1
                    save(invocation/f"SNAPSHOT_{payload['time_year']:05d}.json", payload); found.add(payload['time_year'])
            require(found == wanted, 'COMMITTED_QUERY_COVERAGE_MISSING')
        if legacy:
            for stream in (legacy, index): stream.flush(); os.fsync(stream.fileno())
    finally:
        if legacy: legacy.close()
        if index: index.close()
    return {'wall_s': time.perf_counter()-tick, 'full_history_payloads_visited': rows,
            'null_event_times_visited': nulls, 'query_years_emitted': sorted(found),
            'full_snapshot_serializations': snapshots_encoded,
            'deferred_query_years': sorted(set(contract['query_years'])-wanted),
            'legacy_full': bool(legacy), 'memory_after': memory()}


def execute(contract, root, *, advanced_segment_years, resume=False, fault=None):
    plan = validate_contract(contract)
    require(type(advanced_segment_years) is int and advanced_segment_years > 0, 'SEGMENT_POSITIVE_INTEGER_REQUIRED')
    root = Path(root).absolute()
    require(not any(p.is_symlink() for p in [root, *root.parents]), 'OUTPUT_SYMLINK_REJECTED')
    if resume:
        require(root.is_dir() and (root/'RUN_CONTRACT.json').is_file()
                and not (root/'RUN_CONTRACT.json').is_symlink(), 'RESUME_ROOT_INVALID')
        require(json.loads((root/'RUN_CONTRACT.json').read_bytes()) == contract, 'RESUME_LAUNCH_CONTRACT_MISMATCH')
    else:
        root.mkdir(parents=True, exist_ok=False)
        save(root/'RUN_CONTRACT.json', contract)
    lock = (root/'LAUNCHER.lock').open('a+b')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close(); raise LauncherError('LAUNCHER_WRITER_ALREADY_ACTIVE')
    invocation = root/'invocations'/uuid.uuid4().hex
    invocation.mkdir(parents=True)
    started = time.perf_counter(); u0 = usage(); controller = None
    try:
        raw, source = load_verified_r6_initial_columns(Path(contract['input_root']))
        states = {support: compact.unified._state_from_payload(raw[support]) for support in SUPPORTS}
        controller = RecoveryController(root, states, source,
            config=compact.regional.RegionalConfig(duration_years=contract['planned_years']),
            run_plan=plan, run_id='L1_'+sha(contract), fault=fault)
        tick = time.perf_counter()
        if resume:
            recovered = controller.recover()
            require(recovered is not None, 'NO_COMMITTED_PAIR_TO_RESUME')
        else:
            controller.start(); recovered = None
        recovery_s = time.perf_counter()-tick
        first = controller.runtime.time_year
        require(first+advanced_segment_years <= contract['planned_years'], 'SEGMENT_EXCEEDS_PLANNED_HORIZON')
        save(invocation/'INVOCATION.json', {'contract_sha256': sha(contract), 'source_identity': source,
             'context': context(), 'resume': recovered, 'start_year': first, 'advanced_segment_years': advanced_segment_years})
        annual = []; fsyncs = []
        entries_bytes = sum(map(len, controller.runtime._entries))
        frames_bytes = sum(map(len, controller.runtime._frames))
        with (invocation/'ANNUAL.jsonl').open('xb') as telemetry, phases(controller) as phase:
            for _ in range(advanced_segment_years):
                before = dict(phase); cpu0 = usage(); step_started = tick = time.perf_counter()
                entries_before = len(controller.runtime._entries); frames_before = len(controller.runtime._frames)
                controller.advance(1); advance_s = time.perf_counter()-tick
                year = controller.runtime.time_year; fsync_s = 0.0
                if year % contract['journal_fsync_interval_years'] == 0:
                    tick = time.perf_counter(); controller.writer.flush(); fsync_s = time.perf_counter()-tick
                    fsyncs.append({'year': year, 'wall_s': fsync_s, 'resume_authority': False})
                commit = None
                if year % contract['checkpoint_interval_years'] == 0 or year == first+advanced_segment_years:
                    controller.commit(); commit = controller.metrics[-1]
                cpu1 = usage(); wall = time.perf_counter()-step_started
                entries_bytes += sum(len(controller.runtime._entries[i]) for i in range(entries_before, len(controller.runtime._entries)))
                frames_bytes += sum(len(controller.runtime._frames[i]) for i in range(frames_before, len(controller.runtime._frames)))
                sample = {'year': year, 'advance_with_compact_s': advance_s, 'journal_fsync_s': fsync_s,
                    'commit': commit, 'observed_step_service_s': wall,
                    'cpu_user_s': cpu1[0]-cpu0[0], 'cpu_system_s': cpu1[1]-cpu0[1],
                    'equivalent_cores': sum(cpu1[i]-cpu0[i] for i in (0, 1))/wall,
                    'exclusive_phases_s': {key: value-before.get(key, 0) for key, value in phase.items()},
                    'memory': memory(), 'structural_metrics': controller.runtime.metrics,
                    'runtime_entries_bytes': entries_bytes,
                    'runtime_frames_bytes': frames_bytes,
                    'deposit_count': sum(len(cell['deposits']) for cell in controller.runtime._owner.region['cells']),
                    'disk': disk(root) if year % 100 == 0 or commit else None}
                telemetry.write(encode(sample)+b'\n'); telemetry.flush(); annual.append(sample)
        service = services(controller, invocation, contract)
        controller.close(); cpu1 = usage()
        windows = []
        for bucket in sorted({(r['year']-1)//100 for r in annual}):
            values = [r for r in annual if (r['year']-1)//100 == bucket]
            timings = sorted(r['observed_step_service_s'] for r in values)
            windows.append({'start': values[0]['year'], 'end': values[-1]['year'], 'complete_100y': len(values) == 100,
                'wall_s': sum(timings), 'cpu_user_s': sum(r['cpu_user_s'] for r in values),
                'cpu_system_s': sum(r['cpu_system_s'] for r in values),
                'p50_s': statistics.median(timings), 'p95_s': timings[max(0, (95*len(timings)+99)//100-1)],
                'max_s': max(timings)})
        result = {'status': 'PASS_COMPLETED_REQUESTED_SEGMENT', 'start_year': first,
            'end_year': controller.last_native['time_year'], 'committed_records': controller.global_count,
            'checkpoint_id': controller.last_id, 'checkpoint_sha256': sha(controller.last_native),
            'initialization_or_recovery_s': recovery_s, 'commit_metrics': controller.metrics,
            'journal_fsyncs': fsyncs, 'window100': windows, 'services': service,
            'wall_pre_receipt_s': time.perf_counter()-started, 'cpu_user_s': cpu1[0]-u0[0],
            'cpu_system_s': cpu1[1]-u0[1], 'memory': memory(), 'disk_pre_receipt': disk(root),
            'source_contract_sha256': sha(contract), 'invocation': str(invocation)}
        save(invocation/'RESULT.json', result)
        return result
    except BaseException as exc:
        save(invocation/'FAILURE.json', {'type': type(exc).__name__, 'message': str(exc),
             'wall_s': time.perf_counter()-started, 'memory': memory()})
        raise
    finally:
        if controller is not None: controller.close()
        fcntl.flock(lock, fcntl.LOCK_UN); lock.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('prepare', help='Write an exclusive contract; no numerical advance')
    for name in ('planned-years', 'checkpoint-interval-years', 'journal-fsync-interval-years', 'journal-commit-interval-years'):
        prepare.add_argument('--'+name, type=int, required=True)
    prepare.add_argument('--archive-service', choices=('compact_query', 'legacy_full'), required=True)
    prepare.add_argument('--query-years', type=int, nargs='*', required=True)
    prepare.add_argument('--input-root', type=Path, required=True)
    prepare.add_argument('--output-contract', type=Path, required=True)
    run = commands.add_parser('run', help='Explicit numerical execution; requires separate operator authorization')
    run.add_argument('--runtime-r2-rec1', action='store_true', required=True)
    run.add_argument('--contract', type=Path, required=True); run.add_argument('--contract-sha256', required=True)
    run.add_argument('--output-root', type=Path, required=True)
    run.add_argument('--advanced-segment-years', type=int, required=True)
    run.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.command == 'prepare':
        value = make_contract(planned_years=args.planned_years, checkpoint_interval_years=args.checkpoint_interval_years,
            journal_fsync_interval_years=args.journal_fsync_interval_years,
            journal_commit_interval_years=args.journal_commit_interval_years, archive_service=args.archive_service,
            query_years=args.query_years, input_root=args.input_root)
        save(args.output_contract, value)
        print(json.dumps({'status': 'PREPARED_NOT_EXECUTED', 'contract_file_sha256': file_sha(args.output_contract)}))
    else:
        print(json.dumps(execute(read_contract(args.contract, args.contract_sha256), args.output_root,
            advanced_segment_years=args.advanced_segment_years, resume=args.resume), sort_keys=True))


if __name__ == '__main__':
    main()
