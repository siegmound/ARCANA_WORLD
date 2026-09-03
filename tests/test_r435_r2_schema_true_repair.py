import json
import numpy as np
import arcana_worldsim.scientific_engines.r435_geonomics_native_schema_initial_state_seed_closure as m

def test_seed_authority_is_four_replicates_per_job(tmp_path):
    p = tmp_path / "outputs/v0_6D1_R4_3"; p.mkdir(parents=True)
    jobs=[]; seed=1000
    for i in range(23):
        jid=f"R42_J{i+1:02d}_X"
        if i==13: jid=m.J14
        if i==17: jid=m.J18
        if i==20: jid=m.J21
        jobs.append({"engine":"X","job_id":jid,"replicates":[{"seed":seed+j} for j in range(4)]})
        seed += 10
    (p/"R4_3_SEED_LEDGER.json").write_text(json.dumps({"algorithm":"x","jobs":jobs,"stage":"v0.6D1-R4.3"}))
    r=m._seed_authority(tmp_path)
    assert r["exact_23_job_replicate_seed_vectors"] is True
    assert r["all_92_replicate_seeds_globally_unique"] is True
    assert r["geonomics_three_exact_replicate_seed_vectors"] is True
    assert all(x["replicate_count"]==4 for x in r["records"])
    assert all(x["scalar_seed_selection_performed"] is False for x in r["records"])

def test_j21_geometry_uses_declared_axis_positions(tmp_path):
    e=tmp_path/"e.npz"; p=tmp_path/"p.npz"
    np.savez(e,anchor_age_ka=np.arange(9),environment_variable_names=np.arange(7).astype(str),
             environment_fields=np.zeros((9,90,180,7)))
    np.savez(p,anchor_age_ka=np.arange(9),producer_taxon_ids=np.arange(36).astype(str),
             landscape_variable_names=np.arange(4).astype(str),
             producer_landscape=np.zeros((36,9,90,180,4)))
    pkg={"canonical_sources":[{"path":"e.npz","hash_match":True},{"path":"p.npz","hash_match":True}]}
    r=m._j21_grid_from_declared_axes(tmp_path,pkg)
    assert r["status"]=="CLOSED_CANONICAL_INDEX_GRID_GEOMETRY"
    assert (r["rows"],r["cols"])==(90,180)

def test_duplicate_time_axes_allowed_only_if_exactly_equivalent(tmp_path):
    a=tmp_path/"a.npz"; b=tmp_path/"b.npz"; vals=np.array([20.,15.,10.,0.])
    np.savez(a,anchor_age_ka=vals); np.savez(b,anchor_age_ka=vals.copy())
    pkg={"canonical_sources":[{"path":"a.npz","hash_match":True},{"path":"b.npz","hash_match":True}]}
    r=m._time_axis(tmp_path,m.J21,pkg)
    assert r["status"].startswith("CLOSED_")
    assert r["canonical_axis_copy_count"]==2
    assert r["all_canonical_axis_copies_exactly_equal"] is True

def test_j18_profile_selects_snapshot_not_cha2(tmp_path):
    out=tmp_path/"outputs/v0_6D1_R4_23/geonomics_profiles"/m.J18; out.mkdir(parents=True)
    (out/"LANDSCAPE_PROFILE.json").write_text(json.dumps({"translation":{
      "active_mask":"snapshot_active","coordinate_fields":["grid_row","grid_col"],
      "deme_state":"snapshot_deme_state","population_support_field":"population_proxy",
      "time_axis":"snapshot_age_ka"}}))
    npz=tmp_path/"x.npz"; names=np.array(["population_proxy","grid_row","grid_col","local_suitability"])
    st=np.zeros((1,1,2,2,4),dtype=np.float32); act=np.ones((1,1,2,2),dtype=np.uint8)
    np.savez(npz,state_variable_names=names,snapshot_age_ka=np.array([2.,0.]),
             snapshot_deme_state=st,snapshot_active=act,cha2_deme_state=st,cha2_active=act)
    pkg={"canonical_sources":[{"path":"x.npz","hash_match":True}]}
    r=m._state_field_authority(tmp_path,m.J18,pkg)
    assert r["status"]=="CLOSED_EXACT_DEME_STATE_FIELD_AUTHORITY"
    assert r["state_key"]=="snapshot_deme_state"
    assert r["coordinate_center_shift_performed"] is False
    assert "x=grid_col; y=grid_row" in r["carrier_coordinate_rule"]

def test_no_engine_execution_imports_or_calls():
    import inspect
    s=inspect.getsource(m)
    assert "import geonomics" not in s
    assert "gnx.make_model(" not in s
