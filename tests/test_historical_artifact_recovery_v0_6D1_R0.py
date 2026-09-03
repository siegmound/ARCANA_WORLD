from pathlib import Path
import hashlib, importlib.util, zipfile

HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("r0", HERE/"scripts"/"scan_arcana_historical_artifacts.py")
r0=importlib.util.module_from_spec(spec); spec.loader.exec_module(r0)

def test_expected_package_hash_surface_is_locked():
    assert r0.EXPECTED_PACKAGES["v0.6.3D2.2"] == "42f6c506dcb81ed06549713bdf6f2313aa51bd2cb55fe17571fce493923394a8"
    assert len(r0.EXPECTED_PACKAGES)==5

def test_raw_targets_include_rawfirst_and_highres_state():
    assert "arcana_rawfirst.sqlite" in r0.RAW_TARGETS
    assert "physical_reference_cube.nc" in r0.RAW_TARGETS
    assert "cha1_highres_state.npz" in r0.RAW_TARGETS

def test_name_only_raw_does_not_authorize_history(tmp_path):
    (tmp_path/"species_population_timeseries.csv").write_text("x\n")
    rep=r0.scan([tmp_path])
    assert rep["summary"]["raw_targets_found"]==1
    assert rep["summary"]["production_historical_hx_authorized"] is False

def test_zip_member_discovery_without_extract(tmp_path):
    z=tmp_path/"later.zip"
    with zipfile.ZipFile(z,"w") as h:
        h.writestr("inputs/D1_METADATA/species_metadata.json","[]")
        h.writestr("outputs/foo/solver_diagnostics.json","{}")
    rep=r0.scan([tmp_path])
    d={x["target"]:x for x in rep["raw_targets"]}
    s={x["target"]:x for x in rep["support_targets"]}
    assert d["solver_diagnostics.json"]["status"]=="FOUND_IN_ZIP"
    assert s["species_metadata.json"]["status"]=="FOUND_IN_ZIP"

def test_hash_exact_package_promotes_only_matching_stage(tmp_path):
    p=tmp_path/"candidate.zip"; p.write_bytes(b"abc")
    digest=hashlib.sha256(b"abc").hexdigest()
    old=dict(r0.EXPECTED_PACKAGES)
    try:
        r0.EXPECTED_PACKAGES.clear(); r0.EXPECTED_PACKAGES.update({"fake":digest})
        rep=r0.scan([tmp_path])
        assert rep["packages"][0]["status"]=="FOUND_HASH_EXACT"
        assert rep["summary"]["production_historical_hx_authorized"] is False
    finally:
        r0.EXPECTED_PACKAGES.clear(); r0.EXPECTED_PACKAGES.update(old)
