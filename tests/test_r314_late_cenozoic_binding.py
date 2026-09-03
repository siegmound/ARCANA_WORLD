from pathlib import Path
import json, zipfile
import numpy as np
import pytest

from arcana_worldsim.scientific_engines import r314_late_cenozoic_binding as r314

ROOT=Path(__file__).resolve().parents[1]

def test_r314_stage_is_binding_only():
    c=r314.R314Config()
    assert r314.STAGE=='v0.6D1-R3.14'
    assert c.boundary_age_ma==30.0
    assert c.biology_advanced_in_stage is False
    assert c.preview_boundary_authorized is False
    with pytest.raises(ValueError): r314.R314Config(biology_advanced_in_stage=True)
    with pytest.raises(ValueError): r314.R314Config(preview_boundary_authorized=True)

def test_parent_r313_sealed_authority_is_exact():
    p=r314.validate_parent_r313_authority(ROOT)
    assert p['age_ma']==30.0
    assert p['species']==111
    assert p['components']==219
    assert abs(p['population']-1304.4717354192449)<1e-9

def test_a1_has_exact_30_and_book_endpoints():
    a=r314.load_a1(ROOT)
    ages=np.asarray(a['age_ma'],float)
    assert np.any(np.isclose(ages,30.0)) and np.any(np.isclose(ages,0.0))
    assert np.asarray(a['land_mask']).shape[1:]==(90,180)

def test_expected_v061_hashes_remain_frozen():
    assert r314.EXPECTED_V061_SHA256['recent_history']=='be385c4e41345c9964ac49c695084cf2b37366058b1bc3d9fa22ff39195bb3c1'
    assert r314.EXPECTED_V061_SHA256['spatial_snapshots']=='a0ecdf8ee18ecb40883973e69b417bea3de7faead2a123a3bb09bd6c740176fd'
    assert r314.EXPECTED_V061_SHA256==r314.b1.EXPECTED

def test_zip_inspector_rejects_wrong_hashes(tmp_path):
    z=tmp_path/'fake.zip'
    prefix='FAKE_v061'
    with zipfile.ZipFile(z,'w') as f:
        for rel in r314.REQUIRED_V061_RELATIVE_PATHS.values(): f.writestr(prefix+'/'+rel,b'not sealed')
    assert r314.inspect_zip_for_exact_v061(z) is None

def test_missing_payload_returns_governed_blocker(tmp_path):
    # Discovery helper itself must fail closed and must not create a proxy.
    target=tmp_path/'bound'
    got=r314.discover_exact_v061([tmp_path],target)
    assert got is None
    assert not target.exists()

def test_30ma_unbound_late_endpoint_still_matches_r313():
    a=r314.load_a1(ROOT)
    h=r314.r313.validate_30ma_environment_handoff(a)
    assert h['environmental_endpoint_identity_exact'] is True
    assert all(v['max_abs_error']==0.0 for v in h['fields'].values())

def test_validate_30ma_binding_requires_actual_c1_parent(monkeypatch):
    monkeypatch.setattr(r314.r313, 'validate_30ma_environment_handoff', lambda a1: {
        'environmental_endpoint_identity_exact': True,
        'fields': {},
    })
    class WrongC2:
        parent = object()
    with pytest.raises(TypeError, match='required IntegratedLateCenozoicProviderC1 parent'):
        r314.validate_30ma_binding({}, WrongC2())


def test_validate_30ma_binding_accepts_actual_c1_parent(monkeypatch):
    monkeypatch.setattr(r314.r313, 'validate_30ma_environment_handoff', lambda a1: {
        'environmental_endpoint_identity_exact': True,
        'fields': {},
    })
    import arcana_worldsim.late_cenozoic.environment as env
    zeros=np.zeros((2,2), dtype=float)
    baseline={k: zeros.copy() for k in ('land_support','temperature_c','aridity_index','browse_forage','low_forage','wetland_forage','total_edible_forage')}
    monkeypatch.setattr(env, 'late_cenozoic_environment_state', lambda a1, age: baseline)
    class GoodC2:
        parent = object.__new__(r314.IntegratedLateCenozoicProviderC1)
        def state_at(self, age):
            return {k: v.copy() for k,v in baseline.items()}
    out=r314.validate_30ma_binding({}, GoodC2())
    assert out['r314_bound_c2_endpoint_identity_exact'] is True
