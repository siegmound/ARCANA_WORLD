from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import json, sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
from arcana_worldsim.scientific_engines import (  # noqa:E402
    CadenceNormalizationSpec, canonical_r36b_scenarios,
    interval_exchange_to_nemo_generation, edge_hazard_substep_exchange,
    build_three_way_reference_plan, simulate_arcana_cadence_probe,
    embeddable_reference_exchange_from_edge_targets,
)

PARENT_HASHES={
 'src/rebased_natural_control_runtime_v0_6D1_R3_4.py':'087d05f532d84f53f8c99d08ae0099657792526eb3aa97bab7cb9e64cb342e45',
 'src/rebased_natural_control_runtime_v0_6D1_R3_5.py':'634237eb15383000e88180b890ead9b6facc281c0a77eb5ce00efe32f3d0bc95',
 'src/d3_additive_variance_v0_6_3D3_3A.py':'3b235b186e234f66a77443bec3a46c80ef699ecd715737be7d36103db01b4c21',
 'src/d3_paleogeographic_history_v0_6_3D3_2C.py':'5831f41ba9cd7bc05be0cd25f8cd84e895c6c9fa453bde7634d7b27c82394730',
 'src/arcana_worldsim/scientific_engines/contracts.py':'4983b25cd3311448bd1bb8dd41b957e6e2d8a2200fcd660343d3e2eda9d47a5b',
 'src/arcana_worldsim/scientific_engines/nemo242.py':'6e4cea2620cfcd475328682c5458a4a54771c36bda8488da828cb9d7004202f5',
 'src/arcana_worldsim/scientific_engines/registry.py':'6706bfbb36490460e3ba16d1c9d4ad3b0550b6f30d1db246eb341870ee771a27',
}
def dig(p): return sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 checks=[]
 def ck(n,o,d=''): checks.append({'check':n,'pass':bool(o),'detail':str(d)})
 cfg=json.loads((ROOT/'configs/world1_cross_engine_cadence_v0_6D1_R3_6C.json').read_text())
 ck('stage',cfg['stage']=='v0.6D1-R3.6C'); ck('parent',cfg['parent_stage']=='v0.6D1-R3.6B')
 ck('nemo242',cfg['nemo_version_required']=='2.4.2'); ck('cadence125',cfg['arcana_biology_interval_years']==125000.0)
 ck('cadence25',cfg['arcana_quantgen_substep_years']==25000.0); ck('five_substeps',cfg['arcana_quantgen_substeps']==5)
 ck('mu_lock',cfg['mu_q_per_myr']==0.002); ck('b_lock',abs(cfg['nonlinear_homeostasis_b_per_myr_per_q']-0.9876543209876544)<1e-15)
 ck('qstar_lock',cfg['q_star']==0.045); ck('no_canonical_write',cfg['canonical_write_allowed'] is False); ck('no_auto_calibration',cfg['automatic_calibration_allowed'] is False)
 for p,h in PARENT_HASHES.items(): ck('parent_hash::'+p,dig(p)==h,dig(p))
 s=CadenceNormalizationSpec(); ck('sqrt_mu_b',abs(np.sqrt(s.mutation_q_per_myr/s.nonlinear_b_per_myr_per_q)-s.q_star)<1e-15)
 suite=canonical_r36b_scenarios(n_individuals=2000); b0,b1,b3=suite[0],suite[1],suite[3]
 pg=interval_exchange_to_nemo_generation(b1.phases[0].exchange_matrix,125000.0,5.0)
 ck('b1_pergen_rows',np.allclose(pg.sum(1),1)); ck('b1_pergen_small',0<pg[0,1]<1e-5,pg[0,1]); ck('b1_not_raw_005',not np.isclose(pg[0,1],0.05))
 sub=edge_hazard_substep_exchange(b1.phases[0].exchange_matrix,5); ck('pairwise_sub_symmetric',np.allclose(sub,sub.T)); ck('pairwise_retention',abs((1-sub[0,1])**5-(1-0.05))<1e-12)
 p=build_three_way_reference_plan(b1); ck('plan_rows',p['checks']['nemo_rows_sum_one']); ck('plan_no_write',p['authority']['canonical_write_allowed'] is False)
 a=simulate_arcana_cadence_probe(b0,macrosteps=10,substeps_per_macrostep=1); b=simulate_arcana_cadence_probe(b0,macrosteps=10,substeps_per_macrostep=5)
 ck('b0_cadence_invariant',abs(a['final_max_q']-b['final_max_q'])<1e-12,abs(a['final_max_q']-b['final_max_q']))
 a=simulate_arcana_cadence_probe(b1,macrosteps=10,substeps_per_macrostep=1); b=simulate_arcana_cadence_probe(b1,macrosteps=10,substeps_per_macrostep=5)
 ck('b1_cadence_finite',np.isfinite(a['final_max_q']) and np.isfinite(b['final_max_q'])); ck('b1_locks_equal',a['locks']==b['locks'])
 rejected=False
 try: interval_exchange_to_nemo_generation(b3.phases[0].exchange_matrix,125000.0,5.0)
 except ValueError: rejected=True
 ck('b3_nonembeddable_rejected',rejected)
 c3=embeddable_reference_exchange_from_edge_targets(b3.phases[0].exchange_matrix,125000.0); pg3=interval_exchange_to_nemo_generation(c3,125000.0,5.0)
 ck('c3_embeddable',np.allclose(pg3.sum(1),1,atol=1e-12)); ck('c3_nonnegative',np.min(pg3)>=-1e-12)
 required=['QUANTITATIVE_GENETICS_THREE_WAY_CADENCE_VALIDATION_CONTRACT_v0_6D1_R3_6C.md','NEMO_PER_GENERATION_CADENCE_MAPPING_AUDIT_v0_6D1_R3_6C.md','CROSS_ENGINE_POPULATION_SCALE_CONTRACT_v0_6D1_R3_6C.md','README_R3_6C.md','V0_6D1_R3_6C_STATUS.md','NEXT_STAGE_HANDOFF_v0_6D1_R3_6C.md','src/arcana_worldsim/scientific_engines/cadence_validation.py','tests/test_cross_engine_cadence_v0_6D1_R3_6C.py','scripts/run_cross_engine_cadence_v0_6D1_R3_6C.py','run_v0_6D1_R3_6C_checks.ps1']
 for r in required: ck('required::'+r,(ROOT/r).exists())
 passed=sum(x['pass'] for x in checks); out={'stage':'v0.6D1-R3.6C','status':'PASS' if passed==len(checks) else 'FAIL','passed':passed,'total':len(checks),'checks':checks,'verdict':'PASS_THREE_WAY_CADENCE_NORMALIZATION_FOUNDATION__NEMO_ENGINE_RUNS_PENDING' if passed==len(checks) else 'FAIL'}
 outdir=ROOT/'outputs/v0_6D1_R3_6C'; outdir.mkdir(parents=True,exist_ok=True); (outdir/'FORMAL_AUDIT_v0_6D1_R3_6C.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(out,indent=2)); return 0 if passed==len(checks) else 1
if __name__=='__main__': raise SystemExit(main())
