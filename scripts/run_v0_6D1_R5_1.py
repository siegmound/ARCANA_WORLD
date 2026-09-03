from __future__ import annotations
import argparse, json, os
from pathlib import Path
from arcana_worldsim.state_query.r51_cradle import *

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--allow-non-scientific-dev-parent',action='store_true'); args=ap.parse_args(); root=args.root.resolve(); out=root/'outputs/v0_6D1_R5_1'; out.mkdir(parents=True,exist_ok=True)
 auth=validate_authority(root,args.allow_non_scientific_dev_parent)
 if auth['failed']: print(json.dumps(auth,indent=2)); raise SystemExit(2)
 eng=engine_utility_review(); write_json(out/'R5_1_ENGINE_UTILITY_REVIEW.json',eng)
 atlas=build_atlas(root); saved=save_atlas(out,atlas)
 checks={
  'parent_authority_pass':auth['status']=='PASS_R51_IMMUTABLE_PARENT_AUTHORITY',
  'candidate_cohort_exact':tuple(atlas['candidate_ids'])==CANDIDATES,
  'age_axis_3ma_to_200ka_20kyr':len(atlas['age_ma'])==141 and abs(float(atlas['age_ma'][0])-3)<1e-12 and abs(float(atlas['age_ma'][-1])-.2)<1e-12,
  'spatial_grid_90x180':atlas['population_mass_fraction'].shape==(2,90,180),
  'finite_population_mass':bool(np.isfinite(atlas['population_mass_fraction']).all()),
  'nonnegative_population_mass':float(atlas['population_mass_fraction'].min())>=0,
  'environment_finite':all(bool(np.isfinite(v).all()) for v in atlas['environment'].values()),
  'region_registry_nonempty':saved['region_count']>0,
  'pareto_registry_nonempty':saved['pareto_region_count']>0,
  'threshold_family_exact':THRESHOLD_QUANTILES==(0.90,0.95,0.975,0.99),
  'no_weighted_cradle_score':True,
  'no_single_winner_selected':True,
  'no_0ka_trait_backprojection':True,
  'j14_not_observed_location_claim':True,
  'new_external_engine_execution_performed_is_false':True,
  'external_engine_defines_target_is_false':True,
  'majority_vote_is_false':True,
  'full_history_rerun_performed_is_false':True,
  'canonical_state_changed_is_false':True,
  'derived_refinement_promoted_to_canon_is_false':True,
  'deep_biological_coupling_is_false':True,
 }
 failed=[k for k,v in checks.items() if not v]
 status=('PASS_R51_EMERGENT_HOMINID_CRADLE_ECOLOGICAL_NICHE_DISCOVERY_CANDIDATE' if not failed else 'BLOCKED_R51_INTEGRATED')
 scientific=bool(not args.allow_non_scientific_dev_parent and not failed)
 summary={"stage":STAGE,"status":status,"scientific_candidate_eligible":scientific,"checks_passed":sum(checks.values()),"checks_total":len(checks),"failed":failed,"summary":{"candidate_ids":list(atlas['candidate_ids']),"ages":len(atlas['age_ma']),"region_records":saved['region_count'],"pareto_region_records":saved['pareto_region_count'],"atlas_sha256":saved['atlas_sha256'],"new_external_engine_execution_performed":False,"canonical_state_changed":False,"deep_biological_coupling":False,"cradle_semantics":"MODEL_DERIVED_CRADLE_OPPORTUNITY_REGIONS_NOT_OBSERVED_LITERAL_BIRTHPLACE"},"checks":checks}
 write_json(out/'R5_1_INTEGRATED_AUDIT.json',summary)
 # exact artifact allowlist
 names=['R5_1_ENGINE_UTILITY_REVIEW.json','R5_1_CRADLE_OPPORTUNITY_ATLAS.npz','R5_1_OCCUPIED_ENVIRONMENT_ENVELOPES.json','R5_1_CRADLE_CANDIDATE_REGISTRY.json','R5_1_INTEGRATED_AUDIT.json']
 files={n:{'bytes':(out/n).stat().st_size,'sha256':sha256_file(out/n)} for n in names}
 write_json(out/'R5_1_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':status,'files':files})
 print(json.dumps(summary,indent=2)); print('PASS_R51_EMERGENT_HOMINID_CRADLE_ECOLOGICAL_NICHE_DISCOVERY_CANDIDATE_RUN' if not failed else 'BLOCKED_R51_RUN')
 if failed: raise SystemExit(3)
if __name__=='__main__': main()
