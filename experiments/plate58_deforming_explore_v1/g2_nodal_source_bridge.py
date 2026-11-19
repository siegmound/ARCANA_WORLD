"""R6 G2: bind original T0 PRE nodal columns to G3 A exterior triangles.

Full 51-field source records are held by original node IDs. Per-triangle vertex
quadrature is explicit engineering sampling; no material parameters are inferred.
No mechanical solve, basal forcing, constitutive promotion, or physical T1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from collections.abc import Mapping

import numpy as np

STATUS = "PASS_G2_SOURCE_NODAL_ELEMENT_BINDING__CONSTITUTIVE_AND_G3_FORCING_OPEN"
EXPECTED_MULTI = "PASS_G3_A_MULTISCALE_SOURCE_CONTINUATION__BC_AND_G2_UNRESOLVED"
EXPECTED_INTERFACE = "PASS_G3_A_MULTISCALE_INTERFACE_AND_CONTACT_GRAPH__PHYSICS_UNRESOLVED"
EXPECTED_SPHERE = "PASS_G3_A_SOURCE_SPHERICAL_FACET_AUDIT__G2_G3_PHYSICS_UNRESOLVED"
WEIGHTS = (1.0/3.0, 1.0/3.0, 1.0/3.0)
REQUIRED = ("node_id", "crust_thickness_m", "mantle_lithosphere_thickness_m",
            "crust_density_kg_m3", "mantle_density_kg_m3",
            "layer1_z0_m", "layer1_z1_m", "layer2_z0_m", "layer2_z1_m",
            "layer1_c0_k", "layer2_c0_k", "crust_material_code",
            "mantle_material_code", "material_configuration_code", "mixed_support")


def require(test, message):
    if not test:
        raise ValueError(message)


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def parse_regional_pre(path: Path, field_order: list[str], expected_ids):
    """Parse exact source T0 record order; do not infer missing fields from 0."""
    expected = set(map(int, expected_ids))
    require(len(expected) == len(expected_ids) and len(expected) > 0,
            "G2_PRE_EXPECTED_SOURCE_NODE_IDS_INVALID")
    require(len(field_order) == 51 and len(set(field_order)) == 51 and
            field_order[0] == 'node_id' and set(REQUIRED).issubset(field_order),
            "G2_PRE_FIELD_SCHEMA_DRIFT")
    rows = {}
    with Path(path).open() as fh:
        header = fh.readline().split()
        require(len(header) == 3 and
                header[0] == 'ARCANA_R6_G3_A_PASSIVE_PRE_V1' and
                int(header[2]) == len(expected) and
                header[1] == 'arcana_worldsim.r6.shellset_owner_bound_runtime.v1',
                "G2_PRE_REGIONAL_HEADER_INVALID")
        for line in fh:
            tokens = line.split()
            require(len(tokens) == len(field_order),
                    "G2_PRE_RECORD_FIELD_COUNT_CHANGED")
            numbers = [float(v) for v in tokens]
            require(all(math.isfinite(v) for v in numbers),
                    "G2_PRE_NONFINITE_SOURCE_RECORD")
            pid = int(numbers[0])
            require(numbers[0] == pid and pid in expected and pid not in rows,
                    "G2_PRE_DUPLICATE_OR_UNEXPECTED_PARENT_ID")
            rows[pid] = dict(zip(field_order, numbers, strict=True))
    require(set(rows) == expected, "G2_PRE_MISSING_PARENT_COLUMNS")
    return rows


def validate_column_for_potential(pre):
    """Validate the *geometric thermal inputs*, not the physical material law."""
    p = pre
    for k in ("crust_thickness_m", "mantle_lithosphere_thickness_m",
              "crust_density_kg_m3", "mantle_density_kg_m3",
              "layer1_c0_k", "layer2_c0_k"):
        require(math.isfinite(float(p[k])) and float(p[k]) > 0,
                "G2_PRE_THERMAL_INPUT_NOT_POSITIVE:"+k)
    crust = float(p["crust_thickness_m"])
    total = crust+float(p["mantle_lithosphere_thickness_m"])
    require(abs(p["layer1_z0_m"]) < 1e-6 and
            abs(p["layer1_z1_m"]-crust) < 1e-5 and
            abs(p["layer2_z0_m"]-crust) < 1e-5 and
            abs(p["layer2_z1_m"]-total) < 1e-5,
            "G2_PRE_LAYER_GEOMETRY_NOT_CONTIGUOUS")
    # Material codes and absent-field flags are retained, never inferred.
    return True


def bind_source_triangles(parent_node_ids, feg_elements, parent_triangle_ids,
                          exterior_triangle_ids, source_columns):
    ids = list(map(int, parent_node_ids))
    tris = list(map(int, parent_triangle_ids))
    ext = set(map(int, exterior_triangle_ids))
    require(len(ids) == len(set(ids)) == len(source_columns) and
            set(ids) == set(source_columns) and
            len(feg_elements) == len(tris) == len(set(tris)) and
            ext.issubset(tris), "G2_SOURCE_TRIANGLE_INVENTORY_CHANGED")
    triples = {}
    mixed_codes = 0
    for tid, element in zip(tris, feg_elements, strict=True):
        if tid not in ext:
            continue
        local = tuple(map(int, element.node_ids))
        require(len(local) == 3 and len(set(local)) == 3 and
                all(1 <= n <= len(ids) for n in local),
                "G2_FEG_TRIANGLE_LOCAL_NODE_INVALID")
        parents = [ids[n-1] for n in local]
        configs = [source_columns[p]["material_configuration_code"]
                   for p in parents]
        mixed = len(set(configs)) > 1
        mixed_codes += int(mixed)
        triples[tid] = {
            "parent_triangle_id": tid,
            "parent_node_ids": parents,
            "vertex_quadrature_weights": list(WEIGHTS),
            "material_configuration_codes": configs,
            "mixed_material_configuration": mixed,
            "material_law_by_node": None,
            "PRE_source_only_not_constitutive_projection": True,
        }
    require(len(triples) == len(ext), "G2_EXTERIOR_TRIANGLE_BINDING_INCOMPLETE")
    return triples, mixed_codes


def vertex_quadrature_response(triangle, source_columns, specs_by_parent_node,
                               strain, evaluator=None):
    """Optional experiment: average nodal constitutive responses over a P1 facet.

    Strict 1/3 vertex quadrature, NOT a physically validated spatial/higher-order
    quadrature of a heterogeneous nonlinear material. Requires a separately
    supplied candidate material per original parent node, with no defaults.
    """
    parents = list(map(int, triangle['parent_node_ids']))
    weights = triangle['vertex_quadrature_weights']
    require(len(parents) == 3 and len(set(parents)) == 3 and
            np.allclose(weights, WEIGHTS, rtol=0, atol=0) and
            set(parents).issubset(source_columns) and
            set(parents).issubset(specs_by_parent_node),
            "G2_NODAL_MATERIAL_CANDIDATE_COVERAGE_MISSING")
    if evaluator is None:
        from experiments.plate58_deforming_explore_v1.nonlinear_layered_g3 import (
            column_potential_gradient_tangent as evaluator)
    potential = 0.0
    stress = np.zeros(3)
    tangent = np.zeros((3,3))
    for p, weight in zip(parents, weights, strict=True):
        spec = specs_by_parent_node[p]
        require(isinstance(spec, Mapping) and
                spec.get('authority') == 'ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED',
                "G2_CONSTITUTIVE_SOURCE_AUTHORITY_INVALID")
        state = evaluator(source_columns[p], spec, strain)
        potential += weight*float(state['potential_N_per_m_s'])
        stress += weight*np.asarray(state['stress_resultant_N_per_m'],dtype=float)
        tangent += weight*np.asarray(state['tangent_N_s_per_m'],dtype=float)
    require(np.all(np.isfinite(stress)) and np.all(np.isfinite(tangent)) and
            math.isfinite(potential) and potential >= 0,
            "G2_NODAL_QUADRATURE_RESPONSE_INVALID")
    return {"potential_N_per_m_s": potential,
            "stress_resultant_N_per_m": stress,
            "tangent_N_s_per_m": 0.5*(tangent+tangent.T),
            "vertex_sampled_not_converged": True,
            "real_G2_material_authorized": False,
            "real_G3_forcing": None,
            "mechanical_solve_authorized": False,
            "physical_T1": None}


def build(multiscale_dir: Path, interface_dir: Path, spherical_dir: Path,
          output_dir: Path):
    """Read and SHA-bind only. No material scenarios accepted or solved."""
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    from experiments.plate58_deforming_explore_v1.prepare import _json
    require(not output_dir.exists(), "G2_BINDING_OUTPUT_ALREADY_EXISTS")
    dirs = (multiscale_dir, interface_dir, spherical_dir)
    names = ('CONTINUATION_A.json', 'MULTISCALE_INTERFACE.json',
             'SPHERICAL_AUDIT.json')
    statuses = (EXPECTED_MULTI, EXPECTED_INTERFACE, EXPECTED_SPHERE)
    manifests, records = [], []
    for folder, recordname, status in zip(dirs, names, statuses, strict=True):
        manifest = json.loads((folder/'MANIFEST.json').read_text())
        record = json.loads((folder/recordname).read_text())
        require(manifest['status'] == record['status'] == status and
                manifest['no_solver_run'] and manifest['no_T1'] and
                manifest['no_canonical_promotion'] and
                recordname in manifest['files'] and
                all(sha(folder/f) == d for f, d in manifest['files'].items()),
                "G2_BINDING_UPSTREAM_HASH_OR_AUTHORITY_INVALID")
        manifests.append(manifest)
        records.append(record)
    multiscale, interface, sphere = records
    require(interface['source_multiscale_manifest_sha256'] ==
            sha(multiscale_dir/'MANIFEST.json') and
            sphere['source_multiscale_manifest_sha256'] ==
            sha(multiscale_dir/'MANIFEST.json') and
            sphere['source_interface_manifest_sha256'] ==
            sha(interface_dir/'MANIFEST.json'),
            "G2_BINDING_UPSTREAM_CHAIN_CHANGED")
    regions = {int(x['cell_extent_per_side']): x
               for x in multiscale['topological_comparative_extents']}
    scales = {int(x['extent_cells_per_side']): x for x in interface['scales']}
    require(set(regions) == set(scales) == {8, 16},
            "G2_BINDING_SCALE_INVENTORY_CHANGED")
    output = []
    overlap = {}
    for width in (8,16):
        region, scale = regions[width], scales[width]
        feg_file = multiscale_dir/f'OUTER_A_{width:02d}x{width:02d}.feg'
        pre_file = multiscale_dir/f'OUTER_A_{width:02d}x{width:02d}_PRE_T0_PASSIVE.dat'
        require(sha(feg_file) == region['output_FEG_sha256'] and
                sha(pre_file) == region['output_PRE_sha256'],
                "G2_BINDING_SOURCE_REGION_HASH_CHANGED")
        feg = parse_feg(feg_file.read_text(), mode='SHELLS_READY')
        cols = parse_regional_pre(pre_file, region['PRE_source_field_order'],
                                  region['parent_node_ids'])
        for record in cols.values():
            validate_column_for_potential(record)
        ext, mixed = bind_source_triangles(
            region['parent_node_ids'], feg.elements,
            region['parent_triangle_ids'], scale['source_exterior_triangles'], cols)
        require(len(ext) == 2*width*width-8 and
                set(scale['mechanical_node_order_interface_first']) ==
                  {n for tri in ext.values() for n in tri['parent_node_ids']},
                "G2_BINDING_EXTERIOR_DOF_COVERAGE_CHANGED")
        for node, rec in cols.items():
            if node in overlap:
                require(rec == overlap[node], "G2_BINDING_NESTED_PRE_SOURCE_DRIFT")
            else:
                overlap[node] = rec
        output.append({
            'extent_cells': width,
            'source_FEG_sha256': sha(feg_file),
            'source_regional_PRE_sha256': sha(pre_file),
            'source_node_count': len(cols),
            'source_exterior_triangle_count': len(ext),
            'mixed_material_configuration_triangle_count': mixed,
            'source_PRE_by_parent_node': {str(i): cols[i] for i in sorted(cols)},
            'exterior_triangles': {str(i):ext[i] for i in sorted(ext)},
            'G2_candidate_scenarios': None,
            'G3_external_forces': None,
            'material_projection_to_triangle_validated': False,
            'no_material_inferred_from_codes': True,
        })
    require(34587 in overlap, "G2_BINDING_AUTHENTIC_TRIPLE_NODE_NOT_FOUND")
    result = {
        'schema': 'ARCANA_R6_G2_SOURCE_NODAL_TRIANGLE_QUADRATURE_BINDING_V1',
        'status': STATUS,
        'source_multiscale_manifest_sha256': sha(multiscale_dir/'MANIFEST.json'),
        'source_interface_manifest_sha256': sha(interface_dir/'MANIFEST.json'),
        'source_spherical_manifest_sha256': sha(spherical_dir/'MANIFEST.json'),
        'source_node_34587_PRE_record': overlap[34587],
        'scales': output,
        'physical_material_G2': None,
        'external_G3_forcing': None,
        'basal_GPE_balance': None,
        'mechanical_solve_authorized': False,
        'solver_runs': 0,
        'physical_T1': None,
    }
    output_dir.mkdir(parents=True,exist_ok=False)
    target = output_dir/'SOURCE_NODAL_ELEMENT_G2.json'
    target.write_bytes(_json(result))
    (output_dir/'MANIFEST.json').write_bytes(_json({
        'schema': 'ARCANA_R6_G2_SOURCE_NODAL_ELEMENT_BINDING_MANIFEST_V1',
        'status': STATUS,
        'files': {target.name: sha(target)},
        'no_solver_run': True, 'no_T1': True,
        'no_canonical_promotion': True,
    }))
    return {'status': STATUS,
            'scales': [{'extent': a['extent_cells'],
                        'source_nodes': a['source_node_count'],
                        'exterior_triangles': a['source_exterior_triangle_count'],
                        'mixed_material_configuration_triangles':
                            a['mixed_material_configuration_triangle_count']}
                       for a in output],
            'triple_source_node':34587,
            'mechanical_solve_authorized':False,
            'solver_runs':0,'physical_T1':None}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('multiscale',type=Path)
    p.add_argument('mechanical_interface',type=Path)
    p.add_argument('spherical',type=Path)
    p.add_argument('output',type=Path)
    a=p.parse_args()
    print(json.dumps(build(a.multiscale,a.mechanical_interface,a.spherical,a.output),
                     indent=2))
