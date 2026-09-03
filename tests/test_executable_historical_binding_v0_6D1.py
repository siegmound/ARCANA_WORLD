from __future__ import annotations
import hashlib, json, sys, zipfile
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import executable_historical_binding_v0_6D1 as b


def _make_zip(tmp_path: Path, bad=False):
    root=tmp_path/'payload'; raw=root/'outputs/hybrid1/cha1_highres_v0_6_3D2_2'; raw.mkdir(parents=True)
    for n in b.REQUIRED_RAW_BASENAMES:
        (raw/n).write_bytes(b'x')
    z=tmp_path/'x.zip'
    with zipfile.ZipFile(z,'w') as f:
        for p in root.rglob('*'):
            if p.is_file(): f.write(p,p.relative_to(root).as_posix())
        if bad: f.writestr('../escape.txt','bad')
    return z


def test_hash_verifier_accepts_explicit_test_hash(tmp_path):
    z=_make_zip(tmp_path); h=b.sha256_file(z)
    r=b.verify_canonical_d22_archive(z,require_canonical_hash=True,expected_hash=h,expected_bytes=z.stat().st_size)
    assert r['status']=='PASS_CANONICAL_D22_ARCHIVE_BINDING'


def test_hash_verifier_fails_wrong_hash(tmp_path):
    z=_make_zip(tmp_path)
    with pytest.raises(b.BindingError): b.verify_canonical_d22_archive(z,expected_hash='0'*64,expected_bytes=z.stat().st_size)


def test_zip_slip_fails_closed(tmp_path):
    z=_make_zip(tmp_path,bad=True); h=b.sha256_file(z)
    with pytest.raises(b.BindingError): b.verify_canonical_d22_archive(z,expected_hash=h,expected_bytes=z.stat().st_size)


def test_extract_and_find_raw(tmp_path):
    z=_make_zip(tmp_path); out=b.safe_extract_archive(z,tmp_path/'out'); raw=b.find_raw_dir(out)
    assert raw.name=='cha1_highres_v0_6_3D2_2'


def test_hx_gate_requires_all_historical_inputs(tmp_path):
    with pytest.raises(b.BindingError):
        b.require_historical_hx_inputs(d22_archive=None,d1_archive=None,d2_precha1_archive=None,d1_population_state=None,d1_variance_state=None)


def test_governance_no_summary_reconstruction_and_no_named_protection():
    assert b.GOVERNANCE['reconstruct_D2_from_summaries'] is False
    assert b.GOVERNANCE['direct_Deep_survivor_selector'] is False
    assert b.GOVERNANCE['named_survivor_protection'] is False
    assert b.GOVERNANCE['HSG025_proxy_allowed_in_historical_HX'] is False
