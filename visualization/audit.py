"""VIEW-1A: read-only byte/structure audit. Standard library; no ARCANA imports."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys
import zipfile

RADIUS_M = 6_371_000
SHAPE = (180, 360)
DTYPES = {'|b1': ('?', 'bool'), '|u1': ('B', 'uint8'), '|i1': ('b', 'int8'),
          '<i2': ('h', 'int16'), '<u2': ('H', 'uint16'),
          '<f4': ('f', 'float32'), '<f8': ('d', 'float64')}
AUTHORITIES = {'AUTHORIAL_SYNTHETIC_INITIALIZATION', 'MODEL_DERIVED_FROM_CANONICAL_T0',
               'STOCHASTIC_CANONICAL_MODEL_REALIZATION', 'NONCANONICAL_ENGINEERING',
               'EVIDENCE_ONLY', 'NONE'}


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def checked_cell(row, col):
    if type(row) is not int or type(col) is not int or not (0 <= row < 180 and 0 <= col < 360):
        raise ValueError('cell outside R6 grid')
    return row * 360 + col


def row_col(index):
    if type(index) is not int or not 0 <= index < 64800:
        raise ValueError('index outside R6 grid')
    return divmod(index, 360)


def center(row, col):
    checked_cell(row, col)
    return -89.5 + row, -179.5 + col


def locate(lat, lon):
    """Half-open cells; +180 == -180. North pole assigned terminal row."""
    if not math.isfinite(lat) or not math.isfinite(lon) or not -90 <= lat <= 90:
        raise ValueError('invalid coordinate')
    return min(179, math.floor(lat + 90)), math.floor((lon + 180) % 360)


def authority_allowed(authority, engineering=False):
    if authority not in AUTHORITIES:
        raise ValueError('unrecognized authority; fail closed')
    return authority not in {'NONE', 'EVIDENCE_ONLY'} and (
        authority != 'NONCANONICAL_ENGINEERING' or engineering)


def classify(values, supported, unknown):
    """Keep source values intact; UNKNOWN overrides support, invalid stays distinct."""
    if not len(values) == len(supported) == len(unknown):
        raise ValueError('mask shape mismatch')
    if any(type(v) is not bool for v in [*supported, *unknown]):
        raise ValueError('masks must be boolean')
    return ['UNKNOWN' if u else 'UNSUPPORTED' if not s else
            'INVALID' if not math.isfinite(v) else 'VALID'
            for v, s, u in zip(values, supported, unknown)]


def inspect_file(path, expected, authority):
    authority_allowed(authority)
    result = {'path': str(path), 'expected_sha256': expected['sha256'],
              'authority': authority}
    if not Path(path).is_file():
        return result | {'status': 'INPUT_UNAVAILABLE', 'sha256': None}
    digest = sha256(path)
    result |= {'sha256': digest, 'bytes': Path(path).stat().st_size}
    if not re.fullmatch('[0-9a-f]{64}', expected['sha256']) or digest != expected['sha256']:
        return result | {'status': 'SHA_MISMATCH'}
    if result['bytes'] != expected['bytes']:
        return result | {'status': 'SIZE_MISMATCH'}
    return result | {'status': 'VERIFIED'}


def npz_arrays(path):
    """Read numeric NPY v1/v2 only; reject objects, unsupported types and layouts."""
    arrays = {}
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(set(names)) != len(names):
            raise ValueError('duplicate NPZ member')
        for name in names:
            if '/' in name or not name.endswith('.npy'):
                raise ValueError('unsupported NPZ member')
            with archive.open(name) as f:
                magic = f.read(8)
                if magic not in (b'\x93NUMPY\x01\x00', b'\x93NUMPY\x02\x00'):
                    raise ValueError('unsupported NPY version')
                n = 2 if magic[6] == 1 else 4
                size = int.from_bytes(f.read(n), 'little')
                if size > 65536:
                    raise ValueError('oversized NPY header')
                header = ast.literal_eval(f.read(size).decode('latin1').strip())
                dtype = header['descr']
                shape = header['shape']
                if dtype not in DTYPES or header['fortran_order'] is not False:
                    raise ValueError('unsupported dtype/order')
                if not isinstance(shape, tuple) or any(type(v) is not int or v < 0 for v in shape):
                    raise ValueError('invalid shape')
                fmt, label = DTYPES[dtype]
                count = math.prod(shape)
                if count > 1_000_000:
                    raise ValueError('outside VIEW-1A array budget')
                data = f.read(count * struct.calcsize(fmt) + 1)
                if len(data) != count * struct.calcsize(fmt):
                    raise ValueError('NPY byte count mismatch')
                values = [v[0] for v in struct.iter_unpack('<' + fmt, data)]
                arrays[name[:-4]] = {'shape': list(shape), 'dtype': label,
                                    'npy_descr': dtype, 'order': 'C', 'values': values}
    return arrays


def summaries(arrays):
    result = {}
    for key, a in arrays.items():
        values = a['values']
        finite = [v for v in values if math.isfinite(v)]
        result[key] = {k: v for k, v in a.items() if k != 'values'} | {
            'finite_count': len(finite), 'nan_count': sum(math.isnan(v) for v in values),
            'infinite_count': sum(math.isinf(v) for v in values),
            'min': min(finite) if finite else None, 'max': max(finite) if finite else None}
        if a['dtype'] == 'bool':
            result[key]['true_count'] = sum(values)
        elif a['dtype'].startswith(('int', 'uint')):
            result[key]['counts'] = {str(v): values.count(v) for v in sorted(set(values))}
    return result


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_grid(spec, materialization, partition):
    s, g, p = spec['spatial_contract'], materialization['grid'], partition['parent_grid']
    require(spec['planetary_baseline']['geometry'] == 'SPHERE', 'geometry is not spherical')
    require(spec['planetary_baseline']['mean_radius_m'] == RADIUS_M, 'spec radius mismatch')
    for grid in (g, p):
        require(grid['radius_m'] == RADIUS_M and grid['row_order'] == 'SOUTH_TO_NORTH', 'radius/row mismatch')
        require(grid['latitude_bounds_deg'] == [-90, 90] and grid['longitude_bounds_deg'] == [-180, 180], 'bounds mismatch')
    require(s['shape_lat_lon'] == g['shape_lat_lon'] == p['shape'] == list(SHAPE), 'shape mismatch')
    require(g['column_order'] == 'WEST_TO_EAST_WITH_PERIODIC_LONGITUDE' and p['periodic_longitude'] is True, 'seam mismatch')
    require(g['latitude_centers_first_last_deg'] == [-89.5, 89.5] and
            g['longitude_centers_first_last_deg'] == [-179.5, 179.5], 'centers mismatch')
    area = sum(RADIUS_M ** 2 * math.pi / 180 *
               (math.sin(math.radians(r - 89)) - math.sin(math.radians(r - 90))) * 360
               for r in range(180))
    require(math.isclose(area, 4 * math.pi * RADIUS_M ** 2, rel_tol=1e-14), 'spherical area mismatch')
    return {'status': 'VERIFIED', 'radius_m': RADIUS_M, 'shape': list(SHAPE),
            'row_order': g['row_order'], 'column_order': g['column_order'],
            'sphere_area_m2': area, 'periodic_longitude': True}


def validate_geography(arrays, declarations):
    require(set(arrays) == {f['field'] for f in declarations}, 'geography field membership mismatch')
    for f in declarations:
        a = arrays[f['field']]
        require(a['shape'] == list(SHAPE) and a['dtype'] == f['dtype'], 'geography shape/dtype mismatch')
    a = {k: v['values'] for k, v in arrays.items()}
    land = a['land_ocean_mask']
    require(set(land) <= {0, 1}, 'invalid land/ocean category')
    require(a['elevation_support_mask'] == [bool(v) for v in land], 'elevation support mismatch')
    require(a['synthetic_uncertainty_mask'] == a['elevation_support_mask'], 'synthetic mask mismatch')
    require(a['bathymetry_unknown_mask'] == [not v for v in land], 'bathymetry mask mismatch')
    for name in ('plate_motion', 'deep', 'climate', 'hydrology'):
        require(all(a[name + '_unknown_mask']), 'UNKNOWN mask not preserved')
    require(set(a['boundary_class']) <= {0, 1}, 'boundary category mismatch')
    require(set(a['crust_class']) <= {0, 1, 2}, 'crust category mismatch')
    require(set(a['province_class']) <= {-2, 0, 1, 2, 3}, 'province category mismatch')
    require(set(a['coastline_mask']) <= {0, 1}, 'coast category mismatch')
    require(set(a['plate_id']) == set(range(12)), 'plate identity mismatch')
    for v, is_land in zip(a['land_surface_elevation_m'], land):
        require(math.isfinite(v) and 0 <= v <= 8000 if is_land else math.isnan(v), 'elevation validity mismatch')
    return {'status': 'VERIFIED', 'boundary_unknown_count': a['boundary_class'].count(0),
            'land_cells': sum(land), 'ocean_cells': len(land) - sum(land),
            'ocean_elevation': 'NaN_UNSUPPORTED_NOT_BATHYMETRY'}


def validate_partition(arrays, geography):
    for name, item in arrays.items():
        if name.startswith('boundary_'):
            require(item['shape'] == [1983], 'boundary shape mismatch')
        elif name != 'face_vertex_latlon_deg':
            require(item['shape'] == [64800], 'face shape mismatch')
    a = {k: v['values'] for k, v in arrays.items()}
    expected = set(range(64800))
    ids = [checked_cell(r, c) for r, c in zip(a['face_row'], a['face_col'])]
    require(len(ids) == 64800 and set(ids) == expected, 'face partition is not exact')
    vertices = a['face_vertex_latlon_deg']
    require(all(math.isfinite(v) and v > 0 for v in a['boundary_length_m']), 'invalid boundary lengths')
    require(set(a['boundary_edge_axis']) <= {0, 1}, 'invalid edge axis')
    require(set(a['boundary_plate_a']) | set(a['boundary_plate_b']) <= set(range(12)), 'invalid boundary plate')
    seam_edges = 0
    seen_edges = set()
    for n, (r, c, axis) in enumerate(zip(a['boundary_edge_row'], a['boundary_edge_col'], a['boundary_edge_axis'])):
        left = checked_cell(r, c)
        right = checked_cell(r, (c + 1) % 360) if axis == 0 else checked_cell(r + 1, c)
        require((r, c, axis) not in seen_edges, 'duplicate boundary edge')
        seen_edges.add((r, c, axis))
        seam_edges += int(axis == 0 and c == 359)
        length = RADIUS_M * math.pi / 180 * (1 if axis == 0 else math.cos(math.radians(r - 89)))
        require(math.isclose(a['boundary_length_m'][n], length, rel_tol=1e-13), 'spherical boundary length mismatch')
        if geography is not None:
            plate = geography['plate_id']['values']
            pair = sorted([plate[left], plate[right]])
            require(pair[0] != pair[1] and pair == [a['boundary_plate_a'][n], a['boundary_plate_b'][n]], 'boundary parent plates mismatch')
            side_a, side_b = (left, right) if plate[left] == pair[0] else (right, left)
            for side, cell in [('a', side_a), ('b', side_b)]:
                require(a['boundary_crust_' + side][n] == geography['crust_class']['values'][cell] and
                        a['boundary_support_' + side][n] == geography['boundary_class']['values'][cell], 'boundary parent categories mismatch')
    require(arrays['face_vertex_latlon_deg']['shape'] == [64800, 5, 2], 'vertex shape mismatch')
    for n, cell in enumerate(ids):
        r, c = row_col(cell)
        south, west = r - 90, c - 180
        ring = vertices[n * 10:(n + 1) * 10]
        require(ring[:2] == ring[-2:], 'unclosed face ring')
        require(set(zip(ring[::2], ring[1::2])) ==
                {(south, west), (south, west + 1), (south + 1, west), (south + 1, west + 1)}, 'face bounds mismatch')
        if geography is not None:
            for face, grid in [('face_plate_id', 'plate_id'), ('face_crust_class', 'crust_class'), ('face_boundary_class', 'boundary_class')]:
                require(a[face][n] == geography[grid]['values'][cell], 'face/parent mismatch')
    return {'status': 'VERIFIED', 'unique_parent_faces': len(ids),
            'boundary_edges_checked': len(seen_edges), 'periodic_seam_boundary_edges': seam_edges,
            'parent_values_checked': geography is not None,
            'face_geometry': 'latitude small circles; longitude great-circle meridians'}


def json_structure(value):
    """Observed fields/types/shapes; never infer units or support from key names."""
    if isinstance(value, dict):
        return {k: json_structure(v) for k, v in value.items()}
    if isinstance(value, list):
        return {'length': len(value), 'element': json_structure(value[0]) if value else None}
    return type(value).__name__


def engineering_summary(document):
    require(document['canonical_publication'] is False and document['interpolation'] == 'NONE',
            'engineering authority/interpolation mismatch')
    observed = {}
    for support, samples in document['samples_by_support'].items():
        times = [s['elapsed_years'] for s in samples]
        require(times and all(b > a for a, b in zip(times, times[1:])), 'unordered engineering samples')
        for sample in samples:
            require(sample['support_id'] == support, 'engineering support identity mismatch')
            for field in document['units']:
                values = sample[field] if isinstance(sample[field], list) else [sample[field]]
                require(all(type(v) in (int, float) and math.isfinite(v) for v in values),
                        'invalid engineering numeric value')
            require(len(sample['temperature_k']) == len(sample['z_m']) ==
                    len(sample['material_coordinate']) == 73, 'engineering profile shape mismatch')
            require(math.isclose(sample['time_s'], sample['elapsed_years'] * 31557600, rel_tol=1e-12, abs_tol=1e-9),
                    'engineering time coordinate mismatch')
        observed[support] = {'sample_count': len(samples), 'profile_nodes': 73,
                             'elapsed_years': times, 'validity': 'ALL_RECORDED_NUMBERS_FINITE',
                             'unrecorded_support': 'UNSUPPORTED'}
    return {'units': document['units'], 'supports': observed,
            'authority': 'NONCANONICAL_ENGINEERING', 'interpolation': 'NONE'}


def audit(repo, lock, external_root=None):
    sources, loaded, payloads = [], {}, {}
    for entry in lock['sources']:
        path = (external_root / entry['external_relative_path'] if external_root is not None else
                Path(entry['recorded_path'])) if 'external_relative_path' in entry else repo / entry['path']
        result = inspect_file(path, entry, entry['authority']) | {'source_id': entry['path'],
                   'identity_basis': entry['identity_basis'],
                   'support_metadata': entry['support_metadata']}
        if result['status'] == 'VERIFIED':
            try:
                if path.suffix == '.json':
                    d = json.loads(path.read_text(encoding='utf-8'))
                    loaded[entry['path']] = d
                    result |= {'schema': d.get('schema', d.get('schema_version', 'UNDECLARED')),
                               'fields': json_structure(d)}
                    if path.name == 'DIAGNOSTIC_NUMERICAL_SAMPLES.json':
                        result['engineering_observations'] = engineering_summary(d)
                elif path.suffix == '.npz':
                    a = npz_arrays(path)
                    payloads[entry['path']] = a
                    result |= {'schema': 'NPZ_NUMERIC_NPY', 'fields': summaries(a)}
                else:
                    result |= {'schema': 'TEXT_EVIDENCE', 'numeric_support': 'NOT_APPLICABLE'}
            except (ValueError, KeyError, IndexError, SyntaxError, struct.error, zipfile.BadZipFile) as e:
                result |= {'status': 'UNSUPPORTED', 'reason': str(e)}
        sources.append(result)
    failures = [s for s in sources if s['status'] in {'SHA_MISMATCH', 'SIZE_MISMATCH', 'UNSUPPORTED'}]
    checks = {}
    if not failures:
        try:
            m = loaded['R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json']
            checks['grid'] = validate_grid(loaded['R6_INITIAL_WORLD_PHYSICAL_SPECIFICATION.json'], m,
                                          loaded['R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json'])
            geo = payloads.get('external://R6_INITIAL_PHYSICAL_GEOGRAPHY.npz')
            part = payloads.get('external://R6_T0_VECTOR_PLATE_PARTITION.npz')
            checks['geography'] = validate_geography(geo, m['payload']['fields']) if geo else {'status': 'INPUT_UNAVAILABLE'}
            checks['partition'] = validate_partition(part, geo) if part else {'status': 'INPUT_UNAVAILABLE'}
            k = loaded['R6_T0_CANONICAL_PLATE_KINEMATICS.json']
            require(k['authority_class'] == 'STOCHASTIC_CANONICAL_MODEL_REALIZATION' and
                    k['time_ma'] == 210 and len(k['plates']) == 12, 'kinematics authority/support mismatch')
            require({plate['plate_id'] for plate in k['plates']} == set(range(12)), 'kinematics plate identity mismatch')
            require(k['parent_canonical_t0_sha256'] == m['payload']['sha256'] and
                    k['parent_vector_partition_sha256'] == loaded['R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json']['payload']['sha256'],
                    'kinematics source chain mismatch')
            checks['kinematics'] = {'status': 'VERIFIED', 'plate_records': 12,
                                    'semantic_identity': k['payload_identity_sha256'], 'grid_motion': 'UNKNOWN'}
        except (KeyError, IndexError, ValueError) as e:
            checks['contract'] = {'status': 'UNSUPPORTED', 'reason': str(e)}
            failures.append(checks['contract'])
    missing = [s['source_id'] for s in sources if s['status'] == 'INPUT_UNAVAILABLE']
    # Hash again after inspection; do not silently attest a changing source.
    for source in sources:
        if source['status'] == 'VERIFIED' and sha256(source['path']) != source['sha256']:
            source['status'] = 'SOURCE_CHANGED_DURING_AUDIT'
            failures.append(source)
    return {'schema': 'ARCANA_VIEW_SOURCE_AUDIT_V1', 'source_baseline': lock['baseline'],
            'status': 'FAIL_CLOSED' if failures else 'INPUT_UNAVAILABLE' if missing else 'VERIFIED',
            'sources': sources, 'checks': checks, 'missing': missing,
            'unsupported_domains': ['bathymetry', 'tectonic_kinematics_grid', 'boundary_physical_classification',
                                    'deep', 'climate', 'hydrology', 'weak_zone_state', 'junction_physical_semantics'],
            'authority_promoted': False, 'inputs_mutated': False}, 1 if failures else 2 if missing else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--external-root', type=Path, help='Explicit relocation root; hashes still mandatory')
    args = parser.parse_args()
    lock = json.loads((Path(__file__).parent / 'source-lock.json').read_text(encoding='utf-8'))
    result, code = audit(args.repo.resolve(), lock, args.external_root)
    print(json.dumps(result, indent=2, allow_nan=False))
    return code


if __name__ == '__main__':
    sys.exit(main())
