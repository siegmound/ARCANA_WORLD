from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import json, subprocess, sys, tempfile
import numpy as np

ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
from arcana_worldsim.scientific_engines.nemo_qtl_ensemble import NemoQTLArchitectureSpec, build_qtl_realization
from arcana_worldsim.scientific_engines.nemo242_r36d import (
    NEMO_REQUIRED_EXECUTABLE, NEMO_REQUIRED_VERSION, Nemo242ExecutableReferenceSpec,
    canonical_r36d_scenarios, matched_no_flow_scenario, parse_qfreq, preflight_nemo242,
    render_nemo242_axis_ini, simulate_arcana_admixture_only_probe,
)

PARENT_HASHES={
 'src/rebased_natural_control_runtime_v0_6D1_R3_4.py':'087d05f532d84f53f8c99d08ae0099657792526eb3aa97bab7cb9e64cb342e45',
 'src/rebased_natural_control_runtime_v0_6D1_R3_5.py':'634237eb15383000e88180b890ead9b6facc281c0a77eb5ce00efe32f3d0bc95',
 'src/d3_additive_variance_v0_6_3D3_3A.py':'3b235b186e234f66a77443bec3a46c80ef699ecd715737be7d36103db01b4c21',
 'src/d3_paleogeographic_history_v0_6_3D3_2C.py':'5831f41ba9cd7bc05be0cd25f8cd84e895c6c9fa453bde7634d7b27c82394730',
 'src/arcana_worldsim/scientific_engines/contracts.py':'4983b25cd3311448bd1bb8dd41b957e6e2d8a2200fcd660343d3e2eda9d47a5b',
 'src/arcana_worldsim/scientific_engines/nemo242.py':'6e4cea2620cfcd475328682c5458a4a54771c36bda8488da828cb9d7004202f5',
 'src/arcana_worldsim/scientific_engines/nemo242_r36b.py':'136f4bbc2f74101576890ddefeedafa4c403ceebd81e09ff4e6fae941e01f3fc',
 'src/arcana_worldsim/scientific_engines/nemo_qtl_ensemble.py':'9f430b6c0b1d15d0ee523de89b16f8d0e80b6238f3e21945b287440ce0e0683f',
 'src/arcana_worldsim/scientific_engines/cadence_validation.py':'a7a26e868c417bbc35349d2884dc15828a64dfbde8ceb04203f21e1533232f9a',
 'scripts/audit_v0_6D1_R3_6C.py':'7dadd837099acab723f2b16f30e0986214f09302352919cb244e788c9ed14735',
}
def dig(p): return sha256((ROOT/p).read_bytes()).hexdigest()

def main():
    checks=[]
    def ck(name, ok, detail=''): checks.append({'check':name,'pass':bool(ok),'detail':str(detail)})
    cfg=json.loads((ROOT/'configs/world1_nemo_executable_reference_v0_6D1_R3_6D.json').read_text())
    ck('stage',cfg['stage']=='v0.6D1-R3.6D'); ck('parent',cfg['parent_stage']=='v0.6D1-R3.6C')
    ck('nemo_version_pin',cfg['nemo_version_required']==NEMO_REQUIRED_VERSION=='2.4.2')
    ck('nemo_executable_pin',cfg['nemo_executable_required']==NEMO_REQUIRED_EXECUTABLE=='nemo2.4.2')
    ck('protocol',cfg['protocol']=='ADMIXTURE_RECOMBINATION_DRIFT_ONLY')
    ck('interval_lock',cfg['arcana_interval_years']==125000.0); ck('generation_mapping',cfg['nemo_generation_transitions_per_arcana_interval']==25000)
    ck('mutation_zero',cfg['mutation_rate_per_locus']==0.0); ck('selection_off',cfg['selection_enabled'] is False); ck('free_recombination',cfg['recombination_rate']==0.5)
    ck('wf_mating',cfg['wright_fisher'] is True and cfg['mating_system']==6)
    ck('breed_disperse_lifecycle',cfg['nemo_lifecycle']==['quanti_init','breed_disperse','save_stats','save_files'])
    ck('backward_semantics',cfg['nemo_migration_semantics']=='BACKWARD_GAMETIC_PARENT_SOURCE')
    ck('symmetric_gate',cfg['migration_matrix_requirement']=='SYMMETRIC_DOUBLY_STOCHASTIC')
    ck('paired_common_rng',cfg['paired_control_design']=='COMMON_QTL_REALIZATION_AND_COMMON_ENGINE_RANDOM_SEED')
    ck('mu_lock',cfg['mu_q_per_myr_locked']==0.002)
    ck('b_lock',abs(cfg['nonlinear_homeostasis_b_per_myr_per_q_locked']-0.9876543209876544)<1e-15)
    ck('qstar_lock',cfg['q_star_locked']==0.045)
    ck('no_canonical_write',cfg['canonical_write_allowed'] is False)
    ck('no_auto_calibration',cfg['automatic_calibration_allowed'] is False)
    ck('no_auto_speciation',cfg['automatic_speciation_authority_allowed'] is False)
    for p,h in PARENT_HASHES.items(): ck('parent_hash::'+p,dig(p)==h,dig(p))

    spec=Nemo242ExecutableReferenceSpec(); ck('spec_exact_exec',spec.executable=='nemo2.4.2'); ck('spec_zero_mut',spec.mutation_rate_per_locus==0.0); ck('spec_free_rec',spec.recombination_rate==0.5)
    suite=canonical_r36d_scenarios(n_individuals=200)
    ck('scenario_names',[s.name for s in suite]==['B0_EQUILIBRIUM_NO_FLOW','B1_TWO_DEME_ADMIXTURE','C3_EMBEDDABLE_HIGH_ADMIXTURE_STRESS'])
    b1=suite[1]; ctrl=matched_no_flow_scenario(b1)
    ck('control_start_mean',np.array_equal(ctrl.normalized_trait_means,b1.normalized_trait_means)); ck('control_start_va',np.array_equal(ctrl.normalized_additive_variance,b1.normalized_additive_variance)); ck('control_zero_flow',np.count_nonzero(ctrl.phases[0].exchange_matrix)==0)

    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        r=build_qtl_realization(b1.normalized_trait_means,b1.normalized_additive_variance,trait_axes=(0,1),seed=42,spec=NemoQTLArchitectureSpec(loci_per_trait=16,individual_sample_size=200),individuals_per_patch=b1.population_individuals)
        m=render_nemo242_axis_ini(b1,r,trait_local_index=0,seed=99,output_dir=td)
        text=(td/'Nemo2_ARCANA_R36D.ini').read_text()
        d=np.loadtxt(td/'nemo_per_generation_dispersal.tsv',delimiter='\t')
        half=np.loadtxt(td/'nemo_allele_half_effects.tsv',delimiter='\t',ndmin=2)[0]
        ck('renderer_patch_nbfem','patch_nbfem' in text and 'patch_nbmal             0' in text)
        ck('renderer_no_patch_capacity','patch_capacity' not in text)
        ck('renderer_breed_disperse','breed_disperse          2' in text and 'breed_disperse_matrix' in text)
        ck('renderer_no_separate_disperse','\ndisperse                ' not in text)
        ck('renderer_wf','mating_isWrightFisher' in text and 'mating_system           6' in text)
        ck('renderer_qtl_init','quanti_init_freq' in text and 'quanti_allele_model     diallelic' in text)
        ck('renderer_half_effect',np.allclose(half,0.5*r.effect_sizes[0],atol=0,rtol=1e-15))
        ck('renderer_matrix_symmetric',np.allclose(d,d.T,atol=1e-12,rtol=0)); ck('renderer_rows_one',np.allclose(d.sum(1),1,atol=1e-12)); ck('renderer_cols_one',np.allclose(d.sum(0),1,atol=1e-12))
        ck('renderer_small_migration',0<d[0,1]<1e-5,d[0,1]); ck('renderer_25000_transitions',m['nemo_transitions']==25000 and m['nemo_generations_parameter']==25001)
        ck('renderer_qfreq_hits_final_generation',m['quanti_freq_logtime']==m['nemo_generations_parameter'] and 'quanti_freq_logtime     25001' in text)
        ck('renderer_qfreq_persistence_semantics',m['qfreq_persistence_semantics']=='FINAL_GENERATION_CALLBACK_REQUIRED_BY_NEMO_2_4_2_TTQFREQEXTRACTOR')
        try:
            render_nemo242_axis_ini(b1,r,trait_local_index=0,seed=99,output_dir=td/'bad_qfreq',spec=Nemo242ExecutableReferenceSpec(quanti_freq_logtime=25000))
            bad_qfreq_rejected=False
        except ValueError as exc:
            bad_qfreq_rejected='must divide the NEMO generations parameter' in str(exc)
        ck('renderer_qfreq_missed_final_rejected',bad_qfreq_rejected)
        ck('renderer_governance',m['canonical_write_allowed'] is False and m['automatic_calibration_allowed'] is False)
        q=td/'fake.qfreq'; q.write_text('pop trait locus allele g1 g2\n1 1 1 0.5 0.5 0.75\n1 1 2 0.5 0.5 0.25\n2 1 1 0.5 0.25 0.5\n2 1 2 0.5 0.75 0.5\n')
        parsed=parse_qfreq(q,arcana_effect_a=[1,1]); ck('qfreq_shape',parsed['allele_frequencies'].shape==(2,2,2)); ck('qfreq_finite',np.isfinite(parsed['additive_variance']).all())

    flow=simulate_arcana_admixture_only_probe(b1,macro_intervals=1,substeps_per_interval=1); no=simulate_arcana_admixture_only_probe(ctrl,macro_intervals=1,substeps_per_interval=1)
    ck('arcana_probe_no_homeostasis',flow['homeostasis_applied'] is False and flow['mutation_applied'] is False)
    ck('arcana_flow_injects_va',flow['final_mean_va']>no['final_mean_va'])
    ck('arcana_control_qstar',abs(no['final_mean_va']-0.045)<1e-12,no['final_mean_va'])

    pre=preflight_nemo242(); ck('preflight_exact_name_gate',pre.exact_version_name is True); bad=preflight_nemo242('nemo'); ck('preflight_wrong_name_fails',not bad.pass_exact_242 and bad.reason=='WRONG_EXECUTABLE_BASENAME')

    # Mini preparation proves paired FLOW/control share both genetic and engine seeds.
    with tempfile.TemporaryDirectory() as td:
        cmd=[sys.executable,str(ROOT/'scripts/prepare_nemo_242_executable_suite_v0_6D1_R3_6D.py'),td,'--replicates','1','--population-sizes','100','--loci-per-trait','16','--macro-intervals','1']
        pr=subprocess.run(cmd,cwd=ROOT,env={**__import__('os').environ,'PYTHONPATH':str(SRC)},text=True,capture_output=True)
        ck('mini_suite_prepare_exit',pr.returncode==0,pr.stderr[-500:])
        root=Path(td)
        f=json.loads((root/'N_100/B1_TWO_DEME_ADMIXTURE/rep_000/FLOW/axis_0/R3_6D_JOB.json').read_text())
        c=json.loads((root/'N_100/B1_TWO_DEME_ADMIXTURE/rep_000/MATCHED_NO_FLOW/axis_0/R3_6D_JOB.json').read_text())
        ck('paired_engine_seed',f['engine_seed']==c['engine_seed'],(f['engine_seed'],c['engine_seed']))
        ck('paired_genetic_seed',f['genetic_seed']==c['genetic_seed'])
        ck('paired_qtl_hash',f['qtl_realization_sha256']==c['qtl_realization_sha256'])
        col=subprocess.run([sys.executable,str(ROOT/'scripts/collect_nemo_242_evidence_v0_6D1_R3_6D.py'),td],cwd=ROOT,env={**__import__('os').environ,'PYTHONPATH':str(SRC)},text=True,capture_output=True)
        sm=json.loads((root/'R3_6D_NEMO_EVIDENCE_SUMMARY.json').read_text())
        ck('collector_pending_exit',col.returncode==0); ck('collector_pending_truthful',sm['status']=='NEMO_RUNS_PENDING' and sm['executed_count']==0)
        ck('collector_no_auto_calibration',sm['automatic_calibration_allowed'] is False and sm['full_r3_5_calibration_authorized'] is False)

    required=[
      'NEMO_2_4_2_EXECUTABLE_BINDING_CONTRACT_v0_6D1_R3_6D.md','NEMO_ADMIXTURE_ONLY_REFERENCE_PROTOCOL_v0_6D1_R3_6D.md','NEMO_QFREQ_EVIDENCE_CONTRACT_v0_6D1_R3_6D.md','NEMO_QFREQ_FINALIZATION_REPAIR_v0_6D1_R3_6D_R2.md','NEMO_WSL_EXECUTION_GUIDE_v0_6D1_R3_6D.md','README_R3_6D.md','V0_6D1_R3_6D_STATUS.md','NEXT_STAGE_HANDOFF_v0_6D1_R3_6D.md','configs/world1_nemo_executable_reference_v0_6D1_R3_6D.json','src/arcana_worldsim/scientific_engines/nemo242_r36d.py','tests/test_nemo_executable_reference_v0_6D1_R3_6D.py','scripts/prepare_nemo_242_executable_suite_v0_6D1_R3_6D.py','scripts/collect_nemo_242_evidence_v0_6D1_R3_6D.py','scripts/preflight_nemo_242_v0_6D1_R3_6D.py','scripts/run_nemo_242_suite_wsl.sh','setup_nemo_242_wsl.ps1','run_v0_6D1_R3_6D_nemo_wsl.ps1','run_v0_6D1_R3_6D_checks.ps1']
    for r in required: ck('required::'+r,(ROOT/r).exists())

    passed=sum(x['pass'] for x in checks); total=len(checks)
    engine_state='AVAILABLE' if pre.pass_exact_242 else 'PENDING_EXTERNAL_WSL'
    verdict=('PASS_EXECUTABLE_REFERENCE_BINDING__NEMO_ENGINE_'+engine_state) if passed==total else 'FAIL'
    out={'stage':'v0.6D1-R3.6D','status':'PASS' if passed==total else 'FAIL','passed':passed,'total':total,'engine_preflight':pre.__dict__,'checks':checks,'verdict':verdict}
    outdir=ROOT/'outputs/v0_6D1_R3_6D'; outdir.mkdir(parents=True,exist_ok=True); (outdir/'FORMAL_AUDIT_v0_6D1_R3_6D.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2)); return 0 if passed==total else 1
if __name__=='__main__': raise SystemExit(main())
