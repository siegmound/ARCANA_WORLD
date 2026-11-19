"""Source T0 PRE to nonlinear G2/G3 facet bridge: synthetic source fixtures."""
import pytest
import numpy as np
from types import SimpleNamespace
from experiments.plate58_deforming_explore_v1.g2_nodal_source_bridge import (
    parse_regional_pre,validate_column_for_potential,
    bind_source_triangles, vertex_quadrature_response)

FIELDS = ['node_id','crust_thickness_m','mantle_lithosphere_thickness_m',
          'crust_density_kg_m3','mantle_density_kg_m3',
          'layer1_z0_m','layer1_z1_m','layer2_z0_m','layer2_z1_m',
          'layer1_c0_k','layer2_c0_k','crust_material_code',
          'mantle_material_code','material_configuration_code','mixed_support']
FIELDS += [f'other_{i}' for i in range(51-len(FIELDS))]


def record(i,code=1):
    values=dict.fromkeys(FIELDS,0.)
    values.update(node_id=float(i),crust_thickness_m=10.,
        mantle_lithosphere_thickness_m=20.,crust_density_kg_m3=2.5,
        mantle_density_kg_m3=3.,layer1_z0_m=0.,layer1_z1_m=10.,
        layer2_z0_m=10.,layer2_z1_m=30.,layer1_c0_k=300.,
        layer2_c0_k=700.,crust_material_code=1.,mantle_material_code=2.,
        material_configuration_code=float(code),mixed_support=0.)
    return values


def path(tmp_path,rows):
    p=tmp_path/'PRE.dat'
    p.write_text(f'ARCANA_R6_G3_A_PASSIVE_PRE_V1 arcana_worldsim.r6.shellset_owner_bound_runtime.v1 {len(rows)}\n'+
    ''.join(' '.join(str(record(i)[k]) for k in FIELDS)+'\n' for i in rows))
    return p


def test_roundtrip_rows_in_original_parent_ids(tmp_path):
    cols=parse_regional_pre(path(tmp_path,[11,12,13,14]),FIELDS,[11,12,13,14])
    assert set(cols)=={11,12,13,14}
    assert all(validate_column_for_potential(row) for row in cols.values())
    assert cols[14]['node_id']==14


def test_absent_duplicate_source_fails(tmp_path):
    p=path(tmp_path,[11,12,12,14])
    with pytest.raises(ValueError,match='DUPLICATE'):
        parse_regional_pre(p,FIELDS,[11,12,13,14])


def test_schema_field_count_fails(tmp_path):
    with pytest.raises(ValueError,match='FIELD_SCHEMA'):
        parse_regional_pre(path(tmp_path,[11,12,13]),FIELDS[:25],[11,12,13])


def test_exterior_element_mapping_keeps_all_three_owners():
    cols={i:record(i,1 if i<4 else 2) for i in [1,2,3,4]}
    elements=[SimpleNamespace(node_ids=(1,2,3)),SimpleNamespace(node_ids=(1,3,4))]
    tri,mixed=bind_source_triangles([1,2,3,4],elements,[701,702],[702],cols)
    assert list(tri)==[702]
    assert tri[702]['parent_node_ids']==[1,3,4]
    assert mixed==1
    assert tri[702]['material_law_by_node'] is None


def test_quadrature_nodal_scenario_and_derivative():
    triangle={'parent_node_ids':[11,12,13], 'vertex_quadrature_weights':[1/3]*3}
    cols={i:record(i) for i in (11,12,13)}
    specs={i:{'authority':'ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED',
              'coeff':float(i)} for i in cols}
    def mock(pre,spec,strain):
        x=np.asarray(strain);a=spec['coeff']
        return {'potential_N_per_m_s':.5*a*float(x@x),
                'stress_resultant_N_per_m':a*x,
                'tangent_N_s_per_m':a*np.eye(3)}
    v=np.array([2.,3.,4.])
    r=vertex_quadrature_response(triangle,cols,specs,v,mock)
    assert r['potential_N_per_m_s']==pytest.approx(.5*12.0*(v@v))
    assert np.allclose(r['stress_resultant_N_per_m'],12*v)
    assert np.allclose(r['tangent_N_s_per_m'],12*np.eye(3))
    assert r['real_G2_material_authorized'] is False


def test_no_material_candidate_refused():
    triangle={'parent_node_ids':[11,12,13],'vertex_quadrature_weights':[1/3]*3}
    cols={i:record(i) for i in (11,12,13)}
    with pytest.raises(ValueError,match='MATERIAL_CANDIDATE_COVERAGE'):
        vertex_quadrature_response(triangle,cols,{},[1,2,3])


def test_unratified_materials_only():
    triangle={'parent_node_ids':[11,12,13],'vertex_quadrature_weights':[1/3]*3}
    cols={i:record(i) for i in (11,12,13)}
    specs={i:{'authority':'AUTHOR_RATIFIED'} for i in cols}
    with pytest.raises(ValueError,match='AUTHORITY_INVALID'):
        vertex_quadrature_response(triangle,cols,specs,[1,2,3],lambda *args:None)
