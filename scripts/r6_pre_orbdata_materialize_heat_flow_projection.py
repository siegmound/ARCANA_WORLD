#!/usr/bin/env python3
"""Materialize replayable heat-flow state and numerical FEG support; never run OrbData."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from arcana_worldsim.r6.repository_context import resolve_external_payload_path
from arcana_worldsim.r6.shellset_mesh.adapter import load_canonical_mesh
from arcana_worldsim.r6.pre_orbdata_heat_flow import produce_heat_flow
from arcana_worldsim.r6.pre_orbdata_projection import project_heat_flow_to_feg

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz'
OUTPUT=ROOT/'R6_PRE_ORBDATA_HEAT_FLOW_FEG_PROJECTION_V1.json'


def main() -> int:
    lineage={
        'field_package_sha256':hashlib.sha256(PACKAGE.read_bytes()).hexdigest(),
        'physical_geography_sha256':'a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c',
        'vector_partition_sha256':'a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab',
        'kinematics_sha256':'50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4',
        'heat_flow_config_sha256':hashlib.sha256((ROOT/'R6_PRE_ORBDATA_HEAT_FLOW_CONFIG_V1.json').read_bytes()).hexdigest(),
        'material_config_sha256':hashlib.sha256((ROOT/'R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json').read_bytes()).hexdigest(),
    }
    with np.load(PACKAGE,allow_pickle=False) as z:
        domain=z['physical_crust_domain_id'].copy()
        age=z['oceanic_lithosphere_age_ma'].copy()
        continental=z['continental_reference_surface_heat_flow_w_m2'].copy()
    ridge_report=json.loads((ROOT/'R6_PRE_ORBDATA_HEAT_FLOW_RIDGE_AND_RUNTIME_CLOSURE.json').read_text())
    ridge=np.zeros(domain.shape,dtype=bool)
    for cell in ridge_report['t0_ocean_age_support_audit']['age_zero_cell_locations']:
        ridge[cell['row_south_to_north_zero_based'],cell['column_west_to_east_zero_based']]=True
    if np.count_nonzero(ridge)!=108 or not np.array_equal(ridge,(domain==1)&(age==0)):
        raise ValueError('GOVERNED_RIDGE_MASK_DOES_NOT_MATCH_T0_SUPPORT')
    lineage['ridge_support_mask_sha256']=hashlib.sha256(ridge.astype('uint8').tobytes(order='C')).hexdigest()
    lineage['ridge_source_authority_sha256']=hashlib.sha256((ROOT/'R6_PRE_ORBDATA_HEAT_FLOW_RIDGE_AND_RUNTIME_CLOSURE.json').read_bytes()).hexdigest()
    lineage['feg_mesh_sha256']='6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad'
    for rel in ('src/arcana_worldsim/r6/pre_orbdata_heat_flow.py',
                'src/arcana_worldsim/r6/pre_orbdata_thermal_column.py',
                'src/arcana_worldsim/r6/pre_orbdata_projection.py',
                'scripts/r6_pre_orbdata_materialize_heat_flow_projection.py'):
        lineage[rel.replace('/','_')+'_sha256']=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
    q,branch,valid=produce_heat_flow(physical_domain=domain,age_ma=age,
        continental_q_w_m2=continental,ridge_support=ridge,parent_lineage=lineage)
    result={
        'schema':'R6_PRE_ORBDATA_HEAT_FLOW_DERIVED_CELL_STATE_V1',
        'decision':'DERIVED_REPLAYABLE_T0_STATE__FEG_PROJECTION_PENDING',
        'cell_shape':list(q.shape),'cell_count':int(q.size),
        'cell_heat_flow_w_m2':q.tolist(),'cell_source_branch_code':branch.tolist(),
        'cell_applicability_mask':valid.tolist(),
        'cell_branch_metadata':{
            '1':{'branch':'CONTINENTAL_AUTHORED_REFERENCE','model_identity':None,'lineage':lineage},
            '2':{'branch':'GOVERNED_RIDGE_BOUNDARY','model_identity':None,'lineage':lineage},
            '3':{'branch':'AUTHORIZED_POSITIVE_AGE_OCEAN','model_identity':'HWR2_FINITE_PLATE_CONSTANT_PROPERTY_SURFACE_FLUX','lineage':lineage}},
        'lineage':lineage,
        'cell_heat_flow_sha256':hashlib.sha256(np.asarray(q,dtype='<f8').tobytes()).hexdigest(),
        'cell_branch_counts':{'CONTINENT':int(np.count_nonzero(branch==1)),
                              'RIDGE':int(np.count_nonzero(branch==2)),
                              'POSITIVE_AGE_OCEAN':int(np.count_nonzero(branch==3))},
        'cell_unknown_count':int(np.count_nonzero(~valid)),
        'authority':'DERIVED_REPLAYABLE_T0_STATE',
        'projection_authority':'NUMERICAL_DERIVED_SUPPORT',
        'serialized_orbdata_authority':'NUMERICAL_RUNTIME_INPUT_ONLY',
        'physical_resolution_promotion':False,'smoothing':'NONE',
    }
    OUTPUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    parent=json.loads((ROOT/'R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json').read_text())
    try:
        payload=resolve_external_payload_path(ROOT,parent['payload']['path'])
        with np.load(payload,allow_pickle=False) as z:
            rows=z['face_row'].copy(); cols=z['face_col'].copy()
        mesh=load_canonical_mesh(ROOT)
    except (FileNotFoundError,KeyError,ValueError) as exc:
        result['projection_status']='BLOCKED_MISSING_OR_INVALID_PINNED_FEG_PARENT_PAYLOAD'
        result['projection_diagnostic']=str(exc)
        result['node_count_target']=64442
        result['replay_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        OUTPUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        print(f"cell_state_materialized; FEG projection blocked: {exc}")
        return 2
    projection=project_heat_flow_to_feg(mesh,rows,cols,q,domain,source_lineage=lineage)
    result=projection.serialized_payload()
    result.update({
        'decision':'DERIVED_REPLAYABLE_T0_STATE__NUMERICAL_RUNTIME_INPUT_ONLY',
        'field_shape':list(q.shape),'cell_count':int(q.size),
        'cell_heat_flow_w_m2':q.tolist(),
        'cell_source_branch_code':branch.tolist(),
        'cell_validity_mask':valid.tolist(),
        'cell_branch_counts':{'CONTINENT':int(np.count_nonzero(branch==1)),
                              'RIDGE':int(np.count_nonzero(branch==2)),
                              'POSITIVE_AGE_OCEAN':int(np.count_nonzero(branch==3))},
        'cell_unknown_count':int(np.count_nonzero(~valid)),
        'cell_heat_flow_sha256':hashlib.sha256(np.asarray(q,dtype='<f8').tobytes()).hexdigest(),
        'node_unknown_count':sum(v is None for v in projection.node_heat_flow_w_m2),
        'node_known_count':sum(v is not None for v in projection.node_heat_flow_w_m2),
        'mesh_sha256':mesh.normalized_sha256,
        'lineage':lineage,
        'cell_heat_flow_w_m2':q.tolist(),
        'cell_source_branch_code':branch.tolist(),
        'cell_applicability_mask':valid.tolist(),
        'cell_branch_metadata':{
            '1':{'branch':'CONTINENTAL_AUTHORED_REFERENCE','model_identity':None},
            '2':{'branch':'GOVERNED_RIDGE_BOUNDARY','model_identity':None},
            '3':{'branch':'AUTHORIZED_POSITIVE_AGE_OCEAN','model_identity':'HWR2_FINITE_PLATE_CONSTANT_PROPERTY_SURFACE_FLUX'}},
        'authority':'DERIVED_REPLAYABLE_T0_STATE',
    })
    result.pop('replay_sha256',None)
    result['replay_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    OUTPUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(f"projection_nodes={result['node_count']} unknown={result['node_unknown_count']} replay_sha256={result['replay_sha256']}")
    return 0


if __name__=='__main__':
    raise SystemExit(main())
