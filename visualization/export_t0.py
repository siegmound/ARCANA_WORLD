"""VIEW-1B static T0 NPY export. No model, interpolation or HistoryStore access."""
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
import importlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import tempfile
from typing import Any
import zipfile

import numpy as np
from numpy.typing import NDArray

from visualization import audit

Json = dict[str, Any]
SOURCE_IDS = ('external://R6_INITIAL_PHYSICAL_GEOGRAPHY.npz',
              'external://R6_T0_VECTOR_PLATE_PARTITION.npz')
# Preserved VIEW-1A review anchors. Do not replace a failed pin with current bytes.
VIEW1A_PINS = {
    'source-lock.json': 'b0c2f795d3014ea127156ae39be3039d4ac74a389eb50c92cf72dedd36c6f801',
    'source-inventory.json': '16d0290c483b1937e94ea57019746f9bb7e6965caf7b53a17ed2b3a0da49459a',
    'export-dataset.schema.json': '1a7d7c905dcbac174775e8ce2f7c22589c7168433e1c04fe24ed8d035967f7b3',
    'proposed-layers.json': '5b393619b8adfc1bf17adb46e2901b8df1e01a1c7f2ea7b366d93cda2b0de8e9',
    'audit.py': '61f7b3c288e6cca3e82be78c800b7da25d0494a1de1f54c97a7c0b0816ca5c2f',
    'layer-contract.ts': '5f18339b28521e6c18f6894046d901edae9f7425da722b7f56ce59e31d9fc6a0',
}


class ExportError(ValueError):
    """Fail-closed export/prepublication integrity failure."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ExportError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(document: Json) -> bytes:
    return (json.dumps(document, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')


def identity(path: str, data: bytes) -> Json:
    return {'path': path, 'sha256': digest(data), 'bytes': len(data)}


def authenticate(path: Path, pin: Json) -> bytes:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ExportError(f'INPUT_UNAVAILABLE: {path}') from exc
    require(len(data) == pin['bytes'], f'SIZE_MISMATCH: {path}')
    require(digest(data) == pin['sha256'], f'SHA_MISMATCH: {path}')
    return data  # authenticated immutable snapshot, before any array consumption


def validate_schema(schema: Json, instance: Json) -> None:
    # jsonschema's official Draft202012Validator includes the 2020-12 metaschema.
    validator = importlib.import_module('jsonschema').Draft202012Validator
    try:
        validator.check_schema(schema)
        validator(schema).validate(instance)
    except Exception as exc:
        raise ExportError(f'INVALID_CONTRACT: {exc}') from exc


def decode_npy(data: bytes) -> NDArray[Any]:
    try:
        array = np.load(io.BytesIO(data), allow_pickle=False)
    except (ValueError, OSError) as exc:
        raise ExportError('UNSUPPORTED_NPY') from exc
    require(isinstance(array, np.ndarray), 'expected NPY array')
    require(array.dtype.str in audit.DTYPES and not array.dtype.hasobject, 'UNSUPPORTED_DTYPE')
    require(array.flags.c_contiguous, 'UNSUPPORTED_ARRAY_ORDER')
    return array


def encode_npy(array: NDArray[Any]) -> bytes:
    require(array.dtype.str in audit.DTYPES and not array.dtype.hasobject, 'UNSUPPORTED_DTYPE')
    require(array.flags.c_contiguous, 'UNSUPPORTED_ARRAY_ORDER')
    stream = io.BytesIO()
    np.lib.format.write_array(stream, array, version=(2, 0), allow_pickle=False)
    return stream.getvalue()


def same_bits(left: NDArray[Any], right: NDArray[Any]) -> bool:
    return (left.shape == right.shape and left.dtype.str == right.dtype.str and
            left.tobytes(order='C') == right.tobytes(order='C'))


def read_arrays(data: bytes, fields: Json) -> dict[str, NDArray[Any]]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) and set(names) == {f'{f}.npy' for f in fields},
                'INVALID_ARRAY_MEMBERSHIP')
        arrays = {}
        for field, meta in fields.items():
            name = field + '.npy'
            require(archive.getinfo(name).file_size <= 8_000_000, 'ARRAY_BUDGET_EXCEEDED')
            array = decode_npy(archive.read(name))
            require(list(array.shape) == meta['shape'] and array.dtype.str == meta['npy_descr'],
                    f'SHAPE_DTYPE_MISMATCH: {field}')
            require(meta['order'] == 'C', 'UNSUPPORTED_ARRAY_ORDER')
            array.flags.writeable = False
            arrays[field] = array
    return arrays


@dataclass
class PreparedExport:
    manifest: Json
    files: dict[str, bytes]
    arrays: dict[str, NDArray[Any]]
    inputs: dict[Path, Json]
    manifest_schema: Json
    dataset_schema: Json


def prepare(repo: Path, external_root: Path | None = None) -> PreparedExport:
    repo = repo.resolve()
    visual = repo / 'visualization'
    inputs: dict[Path, Json] = {}
    documents: dict[str, Json] = {}
    for name, pin in VIEW1A_PINS.items():
        path = visual / name
        data = path.read_bytes()
        require(digest(data) == pin, f'VIEW1A_SHA_MISMATCH: {name}')
        inputs[path] = identity('visualization/' + name, data)
        if name.endswith('.json'):
            documents[name] = json.loads(data)
    lock = documents['source-lock.json']
    inventory = documents['source-inventory.json']
    proposal = documents['proposed-layers.json']
    dataset_schema = documents['export-dataset.schema.json']
    validate_schema(dataset_schema, proposal)  # full original proposal, including excluded layers
    require(inventory['status'] == 'VERIFIED', 'INVALID_SOURCE_INVENTORY')
    pins = {e['path']: e for e in lock['sources']}
    observed = {s['source_id']: s for s in inventory['sources']}
    original_documents: dict[str, Json] = {}
    for name in ('R6_INITIAL_WORLD_PHYSICAL_SPECIFICATION.json',
                 'R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json',
                 'R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json'):
        path = repo / name
        data = authenticate(path, pins[name])
        inputs[path] = identity(name, data)
        original_documents[name] = json.loads(data)
    audit.validate_grid(original_documents['R6_INITIAL_WORLD_PHYSICAL_SPECIFICATION.json'],
                        original_documents['R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json'],
                        original_documents['R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json'])
    payloads: dict[str, dict[str, NDArray[Any]]] = {}
    simple_arrays: dict[str, Json] = {}
    for source_id in SOURCE_IDS:
        entry, observation = pins[source_id], observed[source_id]
        require(observation['status'] == 'VERIFIED' and observation['sha256'] == entry['sha256'] and
                observation['bytes'] == entry['bytes'], 'INVENTORY_PIN_MISMATCH')
        path = external_root / entry['external_relative_path'] if external_root else Path(entry['recorded_path'])
        data = authenticate(path, entry)
        inputs[path.resolve()] = identity(source_id, data)
        payloads[source_id] = read_arrays(data, observation['fields'])
        # VIEW-1A structural checks only; their Python floats never feed the writer.
        simple_arrays[source_id] = audit.npz_arrays(io.BytesIO(data))
    geography = simple_arrays[SOURCE_IDS[0]]
    declarations = original_documents['R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json']['payload']['fields']
    audit.validate_geography(geography, declarations)
    audit.validate_partition(simple_arrays[SOURCE_IDS[1]], geography)
    dataset = copy.deepcopy(proposal)
    dataset['layers'] = [l for l in dataset['layers'] if l['source']['path'] in SOURCE_IDS]
    require(len(dataset['layers']) == 30, 'INVALID_T0_LAYER_MEMBERSHIP')
    require(len({l['id'] for l in dataset['layers']}) == 30, 'DUPLICATE_LAYER_ID')
    files: dict[str, bytes] = {}
    exported_arrays: dict[str, NDArray[Any]] = {}
    records = []
    for layer in dataset['layers']:
        source_id, field = layer['source']['path'], layer['field']
        source = layer['source']
        require(source['sha256'] == pins[source_id]['sha256'] and source['bytes'] == pins[source_id]['bytes'],
                'LAYER_SOURCE_MISMATCH')
        require(layer['temporal'] == {'originMa': 210.0, 'elapsedYears': [0.0], 'interpolation': 'NONE'},
                'INVALID_TEMPORAL_SUPPORT')
        require(layer['authority'] in {'NONE', 'AUTHORIAL_SYNTHETIC_INITIALIZATION', 'MODEL_DERIVED_FROM_CANONICAL_T0'},
                'UNSUPPORTED_AUTHORITY')
        array = payloads[source_id][field]
        require(list(array.shape) == layer['shape'] and str(array.dtype) == layer['dtype'], 'LAYER_ARRAY_MISMATCH')
        require(layer['authority'] != 'NONE' or (field.endswith('_unknown_mask') and array.dtype == np.dtype('bool')),
                'UNKNOWN_DOMAIN_NUMERIC_VALUES_FORBIDDEN')
        relative = 'arrays/' + layer['id'].replace('/', '__') + '.npy'
        raw = encode_npy(array)
        require(same_bits(array, decode_npy(raw)), 'NPY_BIT_PATTERN_MISMATCH')
        files[relative], exported_arrays[relative] = raw, array
        layer['numeric'] = identity(relative, raw)
        record = {'layerId': layer['id'], 'file': layer['numeric'],
                  'npyVersion': [2, 0], 'dtypeDescr': array.dtype.str,
                  'order': 'C', 'shape': list(array.shape),
                  'dataSha256': digest(array.tobytes(order='C')),
                  'sourceStateId': layer['stateId']}
        record['exportArrayId'] = 'viewarray_' + digest(canonical(record))
        records.append(record)
    require(len(files) == 30, 'DUPLICATE_OUTPUT_PATH')
    validate_schema(dataset_schema, dataset)
    for name in ('export_t0.py', 'export-manifest.schema.json'):
        data = (visual / name).read_bytes()
        inputs[visual / name] = identity('visualization/' + name, data)
    manifest_schema = json.loads((visual / 'export-manifest.schema.json').read_bytes())
    runtime = {'python': platform.python_version(), 'numpy': np.__version__,
               'jsonschema': importlib.metadata.version('jsonschema'),
               'platform': sys.platform, 'implementation': platform.python_implementation(),
               'machine': platform.machine(), 'serialization': 'NPY_V2_ALLOW_PICKLE_FALSE'}
    manifest: Json = {'schema': 'ARCANA_VIEW_STATIC_T0_EXPORT_V1', 'version': 1,
        'dataset': dataset, 'arrays': records, 'runtime': runtime,
        'provenance': {'inputs': sorted(inputs.values(), key=lambda x: x['path']),
                       'sourceBaseline': lock['baseline'], 'scope': 'VIEW1B_STATIC_T0_ONLY',
                       'excluded': ['engineering trajectories', 'plate kinematics JSON',
                                    'numeric bathymetry', 'numeric Deep', 'numeric climate', 'numeric hydrology']},
        'governance': {'scientificAuthorityPromoted': False, 'worldHistoryWritten': False,
                       'numericalEvolutionExecuted': False, 'temporalInterpolation': False}}
    manifest['exportId'] = 'viewexport_' + digest(canonical(manifest))
    validate_schema(manifest_schema, manifest)
    return PreparedExport(manifest, files, exported_arrays, inputs, manifest_schema, dataset_schema)


def recheck_inputs(prepared: PreparedExport) -> None:
    for path, pin in prepared.inputs.items():
        authenticate(path, pin)


def validate_export(directory: Path, prepared: PreparedExport) -> None:
    require(not directory.is_symlink(), 'SYMLINK_EXPORT_DIRECTORY')
    actual = {str(p.relative_to(directory)).replace('\\', '/') for p in directory.rglob('*') if p.is_file()}
    require(actual == set(prepared.files) | {'manifest.json'}, 'EXPORT_FILE_MEMBERSHIP_MISMATCH')
    manifest_bytes = (directory / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    validate_schema(prepared.manifest_schema, manifest)
    validate_schema(prepared.dataset_schema, manifest['dataset'])
    require(manifest_bytes == canonical(prepared.manifest), 'MANIFEST_INTEGRITY_MISMATCH')
    for name, expected in prepared.files.items():
        path = directory / name
        require(not path.is_symlink(), 'SYMLINK_EXPORT_FILE')
        raw = path.read_bytes()
        require(raw == expected, f'OUTPUT_SHA_OR_BYTE_MISMATCH: {name}')
        require(same_bits(decode_npy(raw), prepared.arrays[name]), f'OUTPUT_NUMERICAL_MISMATCH: {name}')


def export(repo: Path, destination: Path, external_root: Path | None = None) -> Json:
    repo, destination = repo.resolve(), destination.absolute()
    require(os.name == 'nt', 'UNSUPPORTED_PUBLICATION_PLATFORM: Windows no-clobber rename required')
    require(destination.resolve().is_relative_to(repo / 'visualization'), 'OUTPUT_OUTSIDE_VISUALIZATION')
    require(not destination.exists() and not destination.is_symlink(), 'OUTPUT_ALREADY_EXISTS')
    require(destination.parent.is_dir() and not destination.parent.is_symlink(), 'OUTPUT_PARENT_MUST_EXIST')
    prepared = prepare(repo, external_root)
    stage = Path(tempfile.mkdtemp(prefix='.' + destination.name + '.tmp-', dir=destination.parent)).resolve()
    published = False
    try:
        (stage / 'arrays').mkdir()
        for name, raw in prepared.files.items():
            with (stage / name).open('xb') as f:
                f.write(raw)
                f.flush()
                os.fsync(f.fileno())
        with (stage / 'manifest.json').open('xb') as f:
            f.write(canonical(prepared.manifest))
            f.flush()
            os.fsync(f.fileno())
        validate_export(stage, prepared)
        recheck_inputs(prepared)
        # Windows rename fails if *any* destination already exists; no replace/retry.
        os.rename(stage, destination)
        published = True
    finally:
        if not published:
            # Only the exact directory created above is owned by this invocation.
            require(stage.parent == destination.parent.resolve() and stage.name.startswith('.' + destination.name + '.tmp-'),
                    'CLEANUP_OWNERSHIP_MISMATCH')
            if stage.exists():
                shutil.rmtree(stage)
    return prepared.manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--external-root', type=Path)
    parser.add_argument('--output', type=Path, required=True, help='Fresh directory under visualization; parent must exist')
    args = parser.parse_args()
    try:
        manifest = export(args.repo, args.output, args.external_root)
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as exc:
        print(json.dumps({'status': 'FAIL_CLOSED', 'error': str(exc)}))
        return 1
    print(json.dumps({'status': 'VERIFIED', 'exportId': manifest['exportId'], 'arrays': len(manifest['arrays'])}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
