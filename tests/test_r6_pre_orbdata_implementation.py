from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from arcana_worldsim.r6.pre_orbdata_heat_flow import HWR2, cell_provenance_record, produce_heat_flow
from arcana_worldsim.r6.pre_orbdata_thermal_column import (
    LayerMaterial, continental_column, ocean_column,
)
from arcana_worldsim.r6.pre_orbdata_projection import project_heat_flow_to_feg

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz'
LINEAGE={"age":"aed3d311296947aad0f4cc041cfbb1b2784763704b23b1a3e746d2079a607dc2",
         "physical_domain":"814acfdde0285bf6bd549ae8c06e853da5855acb9e78187359a5230fe47cdfd1",
         "continental_heat_flow":"234d2c34f4bc98f72cbaa0e1b322ba781bc95fab9e7b69795fb2b3e7a03b7e2f"}


def _global_product():
    with np.load(PACKAGE,allow_pickle=False) as z:
        domain=z['physical_crust_domain_id'].copy()
        age=z['oceanic_lithosphere_age_ma'].copy()
        cont=z['continental_reference_surface_heat_flow_w_m2'].copy()
    ridge=np.zeros(domain.shape,dtype=bool)
    report=json.loads((ROOT/'R6_PRE_ORBDATA_HEAT_FLOW_RIDGE_AND_RUNTIME_CLOSURE.json').read_text())
    for cell in report['t0_ocean_age_support_audit']['age_zero_cell_locations']:
        ridge[cell['row_south_to_north_zero_based'],cell['column_west_to_east_zero_based']]=True
    assert np.array_equal(ridge,(domain==1)&(age==0))
    return domain,age,cont,ridge


def test_config_values_are_hash_bound_and_gates_stay_closed():
    material=json.loads((ROOT/'R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json').read_text())
    config=json.loads((ROOT/'R6_PRE_ORBDATA_HEAT_FLOW_CONFIG_V1.json').read_text())
    assert material['identity']=='R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1'
    for name,identity in config['source_authorities'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==identity['sha256']
    assert config['architecture_identity']=='HYBRID_DOMAIN_AWARE_HEAT_FLOW'
    assert config['global_heat_flow_envelope_w_m2']=={'nominal':[.045,.47415],'sensitivity':[.03222,.58154],'authority':'R6_PRE_ORBDATA_HEAT_FLOW_MISSING_AUTHORITY_CLOSURE.json'}
    assert config['hwr2']['series_N']==256 and config['hwr2']['relative_tolerance']==1e-12
    assert config['preserved_gates']['PRE_ORBDATA_ready'] is False
    assert config['preserved_gates']['OrbData_authorized'] is False


def test_hwr2_reference_points_and_invalid_age():
    h=HWR2()
    assert h.flux(1.1491667412337465)==pytest.approx(.4741482528,abs=1e-9)
    assert h.flux(70)==pytest.approx(.0612828,abs=1e-7)
    assert h.flux(160)==pytest.approx(.047652545,abs=1e-9)
    with pytest.raises(ValueError,match='STRICTLY_POSITIVE'):
        h.flux(0)


def test_hwr2_parameter_endpoint_sensitivity_envelope_matches_adjudication():
    ranges=((3.0,4.1),(3200.0,3400.0),(1100.0,1250.0),
            (1523.0,1737.0),(250.0,300.0),(80000.0,140000.0))
    values=[]
    for params in itertools.product(*ranges):
        model=HWR2(*params)
        values.extend((model.flux(1.1491667412337465),model.flux(160.0)))
    assert min(values)==pytest.approx(.03221905979948161,abs=1e-12)
    assert max(values)==pytest.approx(.5815390971398668,abs=1e-12)


def test_full_t0_heat_flow_keeps_1072_reauthorized_positive_age_cells_on_hwr_branch():
    domain,age,cont,ridge=_global_product()
    q,branch,valid=produce_heat_flow(physical_domain=domain,age_ma=age,
        continental_q_w_m2=cont,ridge_support=ridge,parent_lineage=LINEAGE)
    assert int(np.count_nonzero(ridge))==108
    assert int(np.count_nonzero((domain==1)&(age>0)))==50434
    closure=json.loads((ROOT/'R6_PRE_ORBDATA_HEAT_FLOW_MISSING_AUTHORITY_CLOSURE.json').read_text())
    assert closure['remaining_unknown_support']['positive_age_ocean_cells']==0
    assert 50434-49362==1072
    assert np.all(branch[(domain==1)&(age>0)]==3)
    assert np.all(valid)
    continental=np.isin(domain,(2,3,4,5,6))
    assert np.array_equal(q[continental],cont[continental])
    assert np.all(q[(domain==1)&(age==0)]==.3)
    assert np.nanmin(q)==pytest.approx(.045)
    assert np.nanmax(q)==pytest.approx(.4741482528,abs=1e-9)
    rec=cell_provenance_record(float(q[np.argwhere((domain==1)&(age>0))[0][0],np.argwhere((domain==1)&(age>0))[0][1]]),3,LINEAGE)
    assert rec.model_identity=='HWR2_FINITE_PLATE_CONSTANT_PROPERTY_SURFACE_FLUX'
    assert rec.parent_lineage==LINEAGE


def test_heat_flow_invalid_authority_fails_closed_and_zero_age_never_enters_hwr(monkeypatch):
    domain,age,cont,ridge=_global_product()
    bad=domain.copy(); bad[0,0]=0
    with pytest.raises(ValueError,match='UNKNOWN_PHYSICAL_DOMAIN'):
        produce_heat_flow(physical_domain=bad,age_ma=age,continental_q_w_m2=cont,ridge_support=ridge,parent_lineage=LINEAGE)
    # Instrument the vector HWR entry point: every evaluated age must be >0.
    original=HWR2.flux_many
    seen=[]
    def guarded(self,ages):
        assert np.all(np.asarray(ages)>0)
        seen.extend(np.asarray(ages).tolist())
        return original(self,ages)
    monkeypatch.setattr(HWR2,'flux_many',guarded)
    q,branch,_=produce_heat_flow(physical_domain=domain,age_ma=age,continental_q_w_m2=cont,
        ridge_support=ridge,parent_lineage=LINEAGE)
    assert np.all(branch[ridge]==2) and np.all(q[ridge]==.3) and len(seen)==50434


@pytest.mark.parametrize('age',[1.1491667412337465,70.0,160.0])
def test_ocean_transient_column_conserves_moho_and_meets_lab(age):
    c=ocean_column(age_ma=age,crust_m=6500)
    assert c.q_surface_w_m2==pytest.approx(HWR2().flux(age),abs=1e-12)
    assert c.crust_m>0 and c.mantle_m>0
    assert c.moho_temperature_k>280 and c.moho_flux_w_m2>0
    assert c.lab_temperature_k>c.moho_temperature_k
    assert c.lab_m<=100000
    tp=1680*math.exp(-3e-5*9.82*100000/1200)
    assert c.lab_temperature_k==pytest.approx(tp*math.exp(3e-5*9.82*c.lab_m/1200),abs=1e-7)
    assert max(c.moho_temperature_k,c.lab_temperature_k)<1900
    assert len(c.profile_coefficients)==2
    x0,x1,a,b,cc,d=c.profile_coefficients[0]
    assert a+b+cc+d==pytest.approx(c.moho_temperature_k,abs=1e-7)
    assert 2.2*(3*a+2*b+cc)/(x1-x0)==pytest.approx(c.moho_flux_w_m2,abs=1e-8)
    x0,x1,a,b,cc,d=c.profile_coefficients[1]
    assert d==pytest.approx(c.moho_temperature_k,abs=1e-7)
    assert 3.3*cc/(x1-x0)==pytest.approx(c.moho_flux_w_m2,abs=1e-8)


@pytest.mark.parametrize('q,hc,total',[ (.045,50000,200000),(.060,35000,135000),(.085,25000,80000) ])
def test_continental_transient_column_preserves_authored_geometry_and_lab(q,hc,total):
    c=continental_column(q_surface=q,crust_m=hc,total_lithosphere_m=total)
    assert c.crust_m==hc and c.crust_m+c.mantle_m==total
    assert c.moho_flux_w_m2>0 and c.lab_flux_w_m2>0
    tp=1680*math.exp(-3e-5*9.82*100000/1200)
    assert c.lab_temperature_k==pytest.approx(tp*math.exp(3e-5*9.82*total/1200),abs=1e-7)
    assert c.lab_temperature_k==pytest.approx(continental_column(q_surface=q,crust_m=hc,total_lithosphere_m=total).lab_temperature_k)
    crust_poly,mantle_poly=c.profile_coefficients
    assert crust_poly[2]*hc*hc+crust_poly[3]*hc+crust_poly[4]==pytest.approx(c.moho_temperature_k,abs=1e-7)
    assert 2.5*(2*crust_poly[2]*hc+crust_poly[3])==pytest.approx(c.moho_flux_w_m2,abs=1e-8)
    assert mantle_poly[4]==pytest.approx(c.moho_temperature_k,abs=1e-7)
    assert 3.3*mantle_poly[3]==pytest.approx(c.moho_flux_w_m2,abs=1e-8)


def test_ridge_keeps_authored_age_zero_but_uses_positive_derived_index():
    c=ocean_column(age_ma=0,crust_m=6500,ridge=True)
    assert c.age_ma==0 and c.q_surface_w_m2==.3
    assert c.effective_age_ma==pytest.approx(2.87057,abs=1e-4)
    assert c.lab_m>c.crust_m


def test_ocean_age_zero_and_nonpositive_geometry_fail_closed():
    with pytest.raises(ValueError,match='MUST_BE_POSITIVE'):
        ocean_column(age_ma=0,crust_m=6500)
    with pytest.raises(ValueError,match='NONPOSITIVE'):
        ocean_column(age_ma=70,crust_m=100000)


def test_continental_sensitivity_case_with_nonpositive_moho_flux_fails_closed():
    # This uses the governed low-q, high-production material endpoints; it is
    # deliberately rejected by the physical monotonic-flux feasibility check.
    crust=LayerMaterial(2.0,2800,800,1.2e-6)
    mantle=LayerMaterial(3.0,3200,1100,4e-8)
    with pytest.raises(ValueError,match='NONMONOTONE_OR_NEGATIVE_FLUX'):
        continental_column(q_surface=.045,crust_m=50000,total_lithosphere_m=200000,
                          crust=crust,mantle=mantle)


def test_projection_preserves_unknown_mixed_support_and_parent_lineage():
    mesh=SimpleNamespace(vertices_lat_lon=np.zeros((4,2)),
        triangles=np.asarray(((1,2,3),(2,3,4))),
        triangle_parent_face=np.asarray((0,1)))
    p=project_heat_flow_to_feg(mesh,np.asarray((0,0)),np.asarray((0,1)),
        np.asarray(((.06,.3),)),np.asarray(((4,1),)),
        source_lineage={'age':'age-sha','domain':'domain-sha'},expected_nodes=4)
    assert p.node_heat_flow_w_m2[0]==.06
    assert p.node_heat_flow_w_m2[1] is None and p.node_heat_flow_w_m2[2] is None
    assert p.node_domain_id[1] is None
    assert p.lineage[1]['incident_domain_ids']==[1,4]
    assert p.lineage[0]['parent_lineage']=={'age':'age-sha','domain':'domain-sha'}
    assert p.source_classification=='NUMERICAL_DERIVED_SUPPORT'
    assert p.serialized_authority=='NUMERICAL_RUNTIME_INPUT_ONLY'


def test_numerical_fixture_projection_accepts_64442_nodes_and_replays_deterministically():
    # Synthetic topology fixture checks the count contract only; it is not
    # presented as the missing canonical R6 FEG parent payload.
    count=64442
    triangles=[(3*i+1,3*i+2,3*i+3) for i in range(21480)]
    triangles.append((64440,64441,64442))
    mesh=SimpleNamespace(vertices_lat_lon=np.zeros((count,2)),
        triangles=np.asarray(triangles),
        triangle_parent_face=np.zeros(len(triangles),dtype=np.int64))
    args=(mesh,np.asarray((0,)),np.asarray((0,)),np.asarray(((.06,),)),
          np.asarray(((4,),)))
    first=project_heat_flow_to_feg(*args,source_lineage={'parent':'sha'})
    second=project_heat_flow_to_feg(*args,source_lineage={'parent':'sha'})
    assert first.node_count==64442
    assert first.replay_sha256==second.replay_sha256
    assert first.serialized_payload()['physical_resolution_promotion'] is False
    assert all(v==.06 for v in first.node_heat_flow_w_m2)


def test_shellset_successor_contract_does_not_claim_historical_fair_for_successor():
    contract=json.loads((ROOT/'R6_PRE_ORBDATA_SHELLSET_SUCCESSOR_PATCH_PROVENANCE.json').read_text())
    assert contract['qualified_parent_shellset_commit']=='62fd474f229b2676fd9d39c5def45137d22d2481'
    assert contract['successor_patch_identity'] is None
    assert contract['historical_patch']['role']=='HISTORICAL_BASELINE_AND_ORACLE_ONLY'
    assert contract['historical_patch']['successor_fair_qualification'] is False
    semantics=' '.join(x['semantic_change'] for x in contract['required_successor_changes']).lower()
    assert 'preserves governed heatfl' in semantics and 'gdh1 replacement' in semantics
    assert 'qlim1 clipping are stock-only' in semantics
    assert 'legacy' in semantics and 'fail closed' in semantics
    assert contract['ubuntu_fair_qualification_required'] is True
