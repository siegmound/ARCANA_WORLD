from __future__ import annotations

import argparse, hashlib, json, sys
from pathlib import Path
from typing import Any
import numpy as np


def hfile(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args(); root=args.root.resolve(); out=args.out.resolve(); sys.path.insert(0,str(root/'src'))
    from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
    from arcana_worldsim.scientific_engines import r315_late_cenozoic_secular_biology as r315
    from arcana_worldsim.scientific_engines import r319_phase_aware_transport_closure as r319

    checks=[]
    def ck(name,cond,actual=None,expected=None): checks.append({'name':name,'pass':bool(cond),'actual':actual,'expected':expected})

    c=r319.R319Config()
    constants={
        'start_age_ma':(.125,r319.START_AGE_MA),'end_age_ma':(0.0,c.end_age_ma),
        'biology_cadence_years':(125000.0,c.biology_cadence_years),'transport_cadence_years':(62500.0,c.transport_cadence_years),
        'phase1_transport_years':(62500.0,c.phase1_transport_years),'phase2_transport_years':(62500.0,c.phase2_transport_years),
    }
    for k,(want,got) in constants.items(): ck('config::'+k,abs(float(got)-float(want))<=1e-12,got,want)
    ck('config::phase_aware',c.phase_aware_transport_enabled is True,c.phase_aware_transport_enabled,True)
    ck('config::deep_off',c.deep_biological_coupling is False,c.deep_biological_coupling,False)
    ck('config::endpoint_topology_reconciliation',c.support_remap_semantics=='R319_EXACT_ENDPOINT_TOPOLOGY_WITH_POST_TRANSPORT_RECONCILIATION',c.support_remap_semantics)
    ck('config::q_ceiling_authority_name',hasattr(c,'variance_ceiling_normalized') and not hasattr(c,'resource_variance_ceiling'),[x for x in dir(c) if 'ceiling' in x])
    ck('config::q_ceiling_value',abs(float(c.variance_ceiling_normalized)-0.08)<=1e-15,float(c.variance_ceiling_normalized),0.08)
    runner_text=(root/'scripts/run_v0_6D1_R3_19_phase_aware_transport_closure.py').read_text(encoding='utf-8')
    ck('runner::q_ceiling_uses_inherited_authority','q_ceiling=float(cfg.variance_ceiling_normalized)' in runner_text and 'cfg.resource_variance_ceiling' not in runner_text)
    ck('runner::binds_exact_endpoint_support',"endpoint_access=np.asarray(endpoint0['accessible'],bool)" in runner_text and 'endpoint_accessible=endpoint_access' in runner_text)

    # Pure bundle conversion and exact phase durations.
    shape=(3,4)
    base={
        'land_support':np.full(shape,.8),'temperature_c':np.full(shape,12.0),'aridity_index':np.full(shape,.4),
        'browse_forage':np.full(shape,3.0),'low_forage':np.full(shape,2.0),'wetland_forage':np.full(shape,1.0),
        'reference_population':np.full((6,)+shape,5.0),
    }
    groups={
        'full_125_to_0':{k:v*125000.0 for k,v in base.items()},
        'transport_phase1_125_to_62p5':{k:v*62500.0 for k,v in base.items()},
        'transport_phase2_62p5_to_0':{k:v*62500.0 for k,v in base.items()},
    }
    macro,(p1,p2)=r319.environments_from_r318_bundle({'groups':groups})
    for label,e in [('macro',macro),('phase1',p1),('phase2',p2)]:
        for k in r319.AVERAGED_FIELDS:
            arr=np.asarray(e[k],float); want=np.asarray(base[k],float)
            ck(f'env_shape::{label}::{k}',arr.shape==want.shape,arr.shape,want.shape)
            ck(f'env_finite::{label}::{k}',bool(np.isfinite(arr).all()))
            ck(f'env_exact::{label}::{k}',bool(np.array_equal(arr,want)),float(np.max(np.abs(arr-want))) if arr.size else 0.0,0.0)
        ck(f'env_accessible::{label}',bool(np.asarray(e['accessible']).all()))
        ck(f'env_forage_closure::{label}',bool(np.array_equal(np.asarray(e['total_edible_forage']),np.asarray(e['browse_forage'])+np.asarray(e['low_forage'])+np.asarray(e['wetland_forage']))))
    ck('macro_bounds',macro['older_ma']==.125 and macro['younger_ma']==0.0,(macro['older_ma'],macro['younger_ma']))
    ck('phase1_bounds',p1['older_ma']==.125 and p1['younger_ma']==.0625,(p1['older_ma'],p1['younger_ma']))
    ck('phase2_bounds',p2['older_ma']==.0625 and p2['younger_ma']==0.0,(p2['older_ma'],p2['younger_ma']))

    # Two-phase operator sequencing with a controlled base migration.
    calls=[]
    def fake_base(pop, root_species, guild, trait, metadata, lat, lon, env, dt, cfg):
        calls.append((env['tag'],float(dt)))
        return np.asarray(pop,float)+float(env['inc']), {'tag':env['tag']}
    trace=[]
    outpop,hab=r319.migration_two_phase(np.zeros((1,1,1)),[],np.array([]),np.zeros((0,3)),{},np.array([]),np.array([]),{},125000.0,c,({'tag':'A','inc':1.0},{'tag':'B','inc':2.0}),base_migration=fake_base,trace=trace)
    ck('migration_call_count',len(calls)==2,calls)
    ck('migration_call_1',calls[0]==('A',62500.0),calls[0])
    ck('migration_call_2',calls[1]==('B',62500.0),calls[1])
    ck('migration_order_effect',float(outpop[0,0,0])==3.0,float(outpop[0,0,0]),3.0)
    ck('migration_final_hab',hab=={'tag':'B'},hab)
    ck('migration_trace_count',len(trace)==2,trace)
    for i,row in enumerate(trace,1):
        ck(f'migration_trace_phase::{i}',int(row['phase_index'])==i,row)
        ck(f'migration_trace_dt::{i}',float(row['dt_years'])==62500.0,row)

    # Endpoint support is a discrete boundary state, not a time-averaged field.
    ecalls=[]
    def endpoint_fake(pop, root_species, guild, trait, metadata, lat, lon, env, dt, cfg):
        ecalls.append(env['tag']); q=np.asarray(pop,float).copy()
        if env['tag']=='P2': q[0,0,0]=0.0; q[0,0,1]=1.0
        return q, {'tag':env['tag']}
    rec={}
    epop,_=r319.migration_two_phase(
        np.array([[[1.0,0.0]]]),[],np.array([]),np.zeros((0,3)),{},np.array([0.0]),np.array([0.0,10.0]),{},125000.0,c,
        ({'tag':'P1','accessible':np.array([[True,True]])},{'tag':'P2','accessible':np.array([[True,True]])}),
        base_migration=endpoint_fake,endpoint_accessible=np.array([[True,False]]),endpoint_reconciliation=rec)
    ck('endpoint_reconcile_calls',ecalls==['P1','P2'],ecalls)
    ck('endpoint_reconcile_mass_conserved',float(epop.sum())==1.0,float(epop.sum()),1.0)
    ck('endpoint_reconcile_closed_cell_zero',float(epop[0,0,1])==0.0,float(epop[0,0,1]),0.0)
    ck('endpoint_reconcile_moved_mass',float(rec.get('remapped_population_mass',-1))==1.0,rec)
    ck('endpoint_reconcile_after_zero',float(rec.get('endpoint_inaccessible_population_after',-1))==0.0,rec)

    # Mandatory real-world constant-forcing promotion test on an actual restartable state.
    mdj=json.loads((root/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text(encoding='utf-8'))
    md=mdj['species'] if isinstance(mdj,dict) and 'species' in mdj else mdj
    p315=root/'local_runs/v0_6D1_R3_15/WORLD1_H0_250ka_LATE_CENOZOIC_SECULAR_BIOLOGY_PRE_C2_BRIDGE_CHECKPOINT_v0_6D1_R3_15.json'
    a1p=root/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz'
    ck('real_fixture_r315_exists',p315.is_file(),str(p315)); ck('real_fixture_a1_exists',a1p.is_file(),str(a1p))
    if p315.is_file() and a1p.is_file():
        st=r315.load_checkpoint(p315); a1=np.load(a1p,allow_pickle=False)
        try:
            rcfg=r38.R38Config(end_age_ma=.125)
            env=r38.bp.environment_at(.125,a1,r38.r34.barrier_cfg(rcfg))
            eq=r319.constant_forcing_equivalence(st,a1,md,env,rcfg,.125)
        finally:
            a1.close()
        ck('constant_equivalence_passed',eq['passed'] is True,eq['passed'],True)
        ck('constant_state_bit_exact',eq['state_bit_exact'] is True,eq['state_bit_exact'],True)
        ck('constant_records_exact',eq['records_exact'] is True,eq['records_exact'],True)
        ck('constant_events_exact',eq['events_exact'] is True,eq['events_exact'],True)
        ck('constant_snapshots_exact',eq['snapshots_exact'] is True,eq['snapshots_exact'],True)
        ck('constant_trace_two',len(eq['transport_trace'])==2,eq['transport_trace'])
        ck('constant_endpoint_reconcile_noop',float(eq.get('endpoint_support_reconciliation',{}).get('remapped_population_mass',-1))==0.0,eq.get('endpoint_support_reconciliation'))
        comp=eq['state_comparison']
        for k,row in comp.get('arrays',{}).items():
            ck('constant_array_exact::'+k,row['same'] is True,row)
            ck('constant_array_zeroerr::'+k,float(row['max_abs_error'])==0.0,row)
        for k,row in comp.get('reduced_state',{}).items():
            ck('constant_reduced_exact::'+k,row['same'] is True,row)
            ck('constant_reduced_zeroerr::'+k,float(row['max_abs_error'])==0.0,row)
        for k,v in comp.get('exact_fields',{}).items(): ck('constant_field_exact::'+k,v is True,v)
        for k,v in comp.get('scalar_abs_errors',{}).items(): ck('constant_scalar_zero::'+k,float(v)==0.0,v)

    # Source-surface governance: only environment and migration are rebound.
    src=root/'src/arcana_worldsim/scientific_engines/r319_phase_aware_transport_closure.py'; text=src.read_text(encoding='utf-8')
    required=(
        'r38.bp.environment_at = environment_at','r38.r34._migration_subcycled_r3 = migration',
        'base_migration=original_migration','R319_EXACT_ENDPOINT_TOPOLOGY_WITH_POST_TRANSPORT_RECONCILIATION',
        'endpoint_accessible=endpoint', 'r38.r2.remap_to_land',
        'constant_forcing_equivalence','EXPECTED_TRANSPORT_SUBSTEPS = 2','TRANSPORT_CADENCE_YEARS = 62_500.0',
    )
    forbidden=(
        'r38.r21._apply_demography =','r38.r2.select_traits =','gene_flow_moment_mix =','advance_nonflow_variance =',
        'advance_pair_states =','maybe_speciate_founder =','ordinary_extinction_update =','apply_mature_fissions_r3 =','apply_mature_coalescences_r33 =',
    )
    for tok in required: ck('source_required::'+tok[:48],tok in text,tok if tok not in text else None)
    for tok in forbidden: ck('source_forbidden_absent::'+tok,tok not in text,tok if tok in text else None)

    # Hard-pinned R3.8 authority.
    r38p=root/'src/arcana_worldsim/scientific_engines/r38_restartable_checkpoint.py'
    ck('r38_sha_sealed',hfile(r38p)=='67211772a20bd942569d7bb8cc3e8c19c6a4071e0bca8ca0cfb1fe15b5d79698',hfile(r38p))

    mp=root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_19.json'
    ck('manifest_exists',mp.is_file(),str(mp))
    manifest=json.loads(mp.read_text(encoding='utf-8')) if mp.is_file() else {}
    ck('manifest_stage',manifest.get('stage')==r319.STAGE,manifest.get('stage'),r319.STAGE)
    ck('manifest_science_unchanged',manifest.get('scientific_parameter_changes') is False,manifest.get('scientific_parameter_changes'))
    ck('manifest_bio_cadence_unchanged',manifest.get('biology_cadence_changes') is False,manifest.get('biology_cadence_changes'))
    ck('manifest_transport_cadence_unchanged',manifest.get('transport_cadence_changes') is False,manifest.get('transport_cadence_changes'))
    ck('manifest_deep_off',manifest.get('deep_biological_coupling') is False,manifest.get('deep_biological_coupling'))
    for rel,want in manifest.get('inherited_authorities_unchanged',{}).items():
        q=root/rel; ck('authority_exists::'+rel,q.is_file(),str(q))
        if q.is_file(): ck('authority_sha::'+rel,hfile(q)==want,hfile(q),want)
    for rel,want in manifest.get('r319_files',{}).items():
        q=root/rel; ck('r319_exists::'+rel,q.is_file(),str(q))
        if q.is_file(): ck('r319_sha::'+rel,hfile(q)==want,hfile(q),want)

    failed=[x for x in checks if not x['pass']]
    verdict='PASS_R319_CANDIDATE_FORMAL_AUDIT__PHASE_AWARE_TRANSPORT_PROMOTED_READY_FOR_LOCAL_125KA_TO_0_H0_BIOLOGY_RUN' if not failed else 'FAIL_R319_CANDIDATE_FORMAL_AUDIT'
    audit={
        'schema':'ARCANA_R319_FORMAL_CANDIDATE_AUDIT_V1','stage':r319.STAGE,'verdict':verdict,
        'checks':f"{len(checks)-len(failed)}/{len(checks)}",'failed':failed,
        'decision':'PROMOTE_PHASE_AWARE_TRANSPORT_WITH_EXACT_ENDPOINT_TOPOLOGY_RECONCILIATION_ONLY_AFTER_BIT_EXACT_CONSTANT_FORCING_EQUIVALENCE',
        'biology_start_age_ma':.125,'biology_end_age_ma':0.0,'biology_cadence_years':125000.0,'transport_cadence_years':62500.0,
        'transport_substeps':2,'r38_modified':False,'scientific_parameter_changes':False,'deep_biological_coupling':False,
        'production_run_fail_closed_on_exact_0ka_support_inconsistency':True,
        'source_manifest_sha256':hfile(mp) if mp.is_file() else None,
    }
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print(json.dumps({'verdict':verdict,'checks':audit['checks'],'out':str(out)},indent=2))
    return 0 if not failed else 1

if __name__=='__main__': raise SystemExit(main())
