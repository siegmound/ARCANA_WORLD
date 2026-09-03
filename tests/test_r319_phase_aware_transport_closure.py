from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
from arcana_worldsim.scientific_engines import r315_late_cenozoic_secular_biology as r315
from arcana_worldsim.scientific_engines import r319_phase_aware_transport_closure as r319

ROOT = Path(__file__).resolve().parents[1]


def _metadata_rows():
    x=json.loads((ROOT/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text(encoding='utf-8'))
    return x['species'] if isinstance(x,dict) and 'species' in x else x


def _r315_state():
    return r315.load_checkpoint(ROOT/'local_runs/v0_6D1_R3_15/WORLD1_H0_250ka_LATE_CENOZOIC_SECULAR_BIOLOGY_PRE_C2_BRIDGE_CHECKPOINT_v0_6D1_R3_15.json')


def _a1():
    return np.load(ROOT/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz',allow_pickle=False)


def _bundle_from_env(env):
    fields={k:np.asarray(env[k],float) for k in r319.AVERAGED_FIELDS}
    return {'biology_state_age_ma':.125,'physical_end_age_ma':0.0,'transport_boundary_age_ma':.0625,'groups':{
        'full_125_to_0':{k:v*125000.0 for k,v in fields.items()},
        'transport_phase1_125_to_62p5':{k:v*62500.0 for k,v in fields.items()},
        'transport_phase2_62p5_to_0':{k:v*62500.0 for k,v in fields.items()},
    }}


def test_config_preserves_sealed_cadences_and_h0():
    c=r319.R319Config()
    assert c.end_age_ma==0.0
    assert c.biology_cadence_years==125000.0
    assert c.transport_cadence_years==62500.0
    assert c.phase1_transport_years==62500.0
    assert c.phase2_transport_years==62500.0
    assert c.phase_aware_transport_enabled is True
    assert c.deep_biological_coupling is False


def test_bundle_to_environments_has_one_macro_and_two_phases():
    z=np.ones((2,3),float)
    full={k:z.copy()*125000.0 for k in r319.AVERAGED_FIELDS}
    p1={k:z.copy()*62500.0 for k in r319.AVERAGED_FIELDS}
    p2={k:z.copy()*62500.0 for k in r319.AVERAGED_FIELDS}
    # reference_population may have any governed shape; all groups must agree per field.
    bundle={'groups':{'full_125_to_0':full,'transport_phase1_125_to_62p5':p1,'transport_phase2_62p5_to_0':p2}}
    macro,(e1,e2)=r319.environments_from_r318_bundle(bundle)
    for e in (macro,e1,e2):
        assert np.array_equal(e['land_support'],z)
        assert np.array_equal(e['accessible'],np.ones_like(z,dtype=bool))
    assert macro['older_ma']==.125 and macro['younger_ma']==0.0
    assert e1['older_ma']==.125 and e1['younger_ma']==.0625
    assert e2['older_ma']==.0625 and e2['younger_ma']==0.0


def test_two_phase_migration_calls_base_exactly_twice_with_62500():
    calls=[]
    def fake(pop,*args,**kwargs):
        # positional env and dt are positions 6 and 7 after pop in base signature here.
        env=args[6]; dt=args[7]
        calls.append((env['tag'],dt))
        return np.asarray(pop,float)+float(env['inc']), {'tag':env['tag']}
    pop=np.zeros((1,1,1),float)
    env1={'tag':'p1','inc':1.0}; env2={'tag':'p2','inc':2.0}
    cfg=r319.R319Config()
    out,hab=r319.migration_two_phase(pop,[],np.array([]),np.zeros((0,3)),{},np.array([]),np.array([]),{},125000.0,cfg,(env1,env2),base_migration=fake)
    assert calls==[('p1',62500.0),('p2',62500.0)]
    assert float(out[0,0,0])==3.0
    assert hab=={'tag':'p2'}


def test_two_phase_migration_rejects_wrong_macro_dt_or_phase_count():
    cfg=r319.R319Config()
    with pytest.raises(ValueError):
        r319.migration_two_phase(np.zeros((1,1,1)),[],np.array([]),np.zeros((0,3)),{},np.array([]),np.array([]),{},62500.0,cfg,({},{}),base_migration=lambda *a,**k:(a[0],None))
    with pytest.raises(ValueError):
        r319.migration_two_phase(np.zeros((1,1,1)),[],np.array([]),np.zeros((0,3)),{},np.array([]),np.array([]),{},125000.0,cfg,({},),base_migration=lambda *a,**k:(a[0],None))


def test_constant_forcing_real_r38_step_is_bit_exact():
    st=_r315_state(); md=_metadata_rows(); a1=_a1()
    try:
        cfg=r38.R38Config(end_age_ma=.125)
        env=r38.bp.environment_at(.125,a1,r38.r34.barrier_cfg(cfg))
        rep=r319.constant_forcing_equivalence(st,a1,md,env,cfg,.125)
    finally:
        a1.close()
    assert rep['passed'] is True
    assert rep['state_bit_exact'] is True
    assert rep['records_exact'] is True
    assert rep['events_exact'] is True
    assert rep['snapshots_exact'] is True
    assert len(rep['transport_trace'])==2
    assert all(x['dt_years']==62500.0 for x in rep['transport_trace'])


def test_phase_aware_binding_restores_r38_functions_after_exit():
    old_env=r38.bp.environment_at; old_mig=r38.r34._migration_subcycled_r3
    e={'x':1}
    with r319.patched_r38_phase_aware_transport(e,(e,e),expected_end_age_ma=.0):
        assert r38.bp.environment_at is not old_env
        assert r38.r34._migration_subcycled_r3 is not old_mig
    assert r38.bp.environment_at is old_env
    assert r38.r34._migration_subcycled_r3 is old_mig


def test_parent_validation_fails_closed_without_r318_seal(tmp_path):
    with pytest.raises(RuntimeError):
        r319.validate_parent_r318_authority(tmp_path)


def test_checkpoint_roundtrip_preserves_runtime_state(tmp_path):
    # Reuse a real restartable state while changing only the authorized endpoint for serialization test.
    st=_r315_state(); st.age_ma=0.0; st.elapsed_year=(210.0-0.0)*1e6
    cfg=r319.R319Config()
    meta=r319.save_checkpoint(st,tmp_path,{'test':True},cfg,{'test':True})
    loaded=r319.load_checkpoint(Path(meta['json']))
    cmp=r38.compare_runtime_states(st,loaded,atol=0.0)
    assert cmp['equivalent'] is True


def test_source_does_not_modify_sealed_r38_file_and_only_patches_environment_and_migration():
    text=(ROOT/'src/arcana_worldsim/scientific_engines/r319_phase_aware_transport_closure.py').read_text(encoding='utf-8')
    assert 'r38.r34._migration_subcycled_r3 = migration' in text
    assert 'r38.bp.environment_at = environment_at' in text
    assert '_apply_demography =' not in text
    assert 'gene_flow_moment_mix =' not in text
    assert 'advance_pair_states =' not in text
    assert 'maybe_speciate_founder =' not in text



def test_canonical_runner_uses_inherited_r38_variance_ceiling_name():
    cfg=r319.R319Config()
    assert cfg.variance_ceiling_normalized==0.08
    assert not hasattr(cfg, "resource_variance_ceiling")
    text=(ROOT/'scripts/run_v0_6D1_R3_19_phase_aware_transport_closure.py').read_text(encoding='utf-8')
    assert 'q_ceiling=float(cfg.variance_ceiling_normalized)' in text
    assert 'cfg.resource_variance_ceiling' not in text

def test_scientific_authority_r38_hash_is_unchanged():
    import hashlib
    p=ROOT/'src/arcana_worldsim/scientific_engines/r38_restartable_checkpoint.py'
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    assert h=='67211772a20bd942569d7bb8cc3e8c19c6a4071e0bca8ca0cfb1fe15b5d79698'


def test_endpoint_support_reconciliation_moves_mass_conservatively_after_phase2():
    calls=[]
    def fake(pop, root_species, guild, trait, metadata, lat, lon, env, dt, cfg):
        calls.append(env['tag'])
        out=np.asarray(pop,float).copy()
        if env['tag']=='p2':
            out[0,0,1]=1.0
            out[0,0,0]=0.0
        return out, {'tag':env['tag']}
    pop=np.array([[[1.0,0.0]]],float)
    phase1={'tag':'p1','accessible':np.array([[True,True]])}
    phase2={'tag':'p2','accessible':np.array([[True,True]])}
    endpoint=np.array([[True,False]])
    rec={}
    out,_=r319.migration_two_phase(
        pop,[],np.array([]),np.zeros((0,3)),{},np.array([0.0]),np.array([0.0,10.0]),{},125000.0,
        r319.R319Config(),(phase1,phase2),base_migration=fake,endpoint_accessible=endpoint,endpoint_reconciliation=rec
    )
    assert calls==['p1','p2']
    assert float(out.sum())==1.0
    assert float(out[0,0,1])==0.0
    assert float(out[0,0,0])==1.0
    assert rec['applied'] is True
    assert rec['remapped_population_mass']==1.0
    assert rec['endpoint_inaccessible_population_after']==0.0


def test_canonical_runner_binds_exact_0ka_endpoint_support_into_phase_aware_macrostep():
    text=(ROOT/'scripts/run_v0_6D1_R3_19_phase_aware_transport_closure.py').read_text(encoding='utf-8')
    assert "endpoint_access=np.asarray(endpoint0['accessible'],bool)" in text
    assert 'endpoint_accessible=endpoint_access' in text
    assert "'endpoint_support_reconciliation':coupling['endpoint_support_reconciliation']" in text
