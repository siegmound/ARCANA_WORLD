from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import rebased_natural_control_runtime_v0_6D1_R3_4 as r34

def check(name, cond, detail=''):
    return {'name':name,'pass':bool(cond),'detail':detail}

def main():
    h=json.loads((ROOT/'outputs/v0_6D1_R3_4/HEADROOM_AUDIT_v0_6D1_R3_4.json').read_text())
    smoke=json.loads((ROOT/'outputs/v0_6D1_R3_4/smoke_210_209/210_to_209p0Ma_summary.json').read_text())
    src=(ROOT/'src/rebased_natural_control_runtime_v0_6D1_R3_4.py').read_text()
    c=r34.R34Config()
    by={x['ceiling']:x for x in h['experiments']}
    rows=[]
    rows += [
      check('stage_id', r34.R3_STAGE_ID=='v0.6D1-R3.4'),
      check('deep_bio_off', r34.R3_DEEP_BIOLOGICAL_COUPLING_ENABLED is False),
      check('ceiling_0p08', c.variance_ceiling_normalized==0.08),
      check('mu_unchanged', c.mutation_variance_supply_normalized_per_myr==0.002),
      check('b_unchanged', abs(c.nonlinear_stabilizing_variance_depletion_per_myr_per_q-0.9876543209876544)<1e-15),
      check('headroom_verdict', h['verdict'].startswith('PASS_')),
      check('0p075_still_touches', by[0.075]['fraction_ge_99pct_ceiling']>0),
      check('0p08_nonbinding', by[0.08]['fraction_ge_99pct_ceiling']==0),
      check('0p10_nonbinding', by[0.1]['fraction_ge_99pct_ceiling']==0),
      check('0p08_equals_0p10_natural_max', abs(by[0.08]['max_q']-by[0.1]['max_q'])<1e-12),
      check('natural_max_below_0p08', by[0.08]['max_q']<0.08),
      check('identity_mismatch_detected_in_parent', h['semantic_identity_audit']['cross_current_species_contact_edges_within_same_root']==131),
      check('runtime_uses_current_species_pair_metrics', 'current_species, metadata, lat, lon, env, cfg' in src),
      check('runtime_gene_flow_current_idx', 'gene_flow_moment_mix(\n                selected, va, totals, G_pre, ri_before, current_idx' in src),
      check('runtime_pair_state_current_species', 'component_ids, current_species, gen, contact, td' in src),
      check('root_provenance_retained', 'root_idx, root_ids = _root_index(root_species)' in src),
      check('smoke_species_120', smoke['species_count']==120),
      check('smoke_components_133', smoke['component_count']==133),
      check('smoke_no_events', smoke['event_counts']=={}),
      check('smoke_population_positive', smoke['final_total_population']>0),
      check('long_rerun_pending', 'LONG_210_TO_150_RERUN_PENDING' in (ROOT/'V0_6D1_R3_4_STATUS.md').read_text()),
    ]
    out={'stage':'v0.6D1-R3.4','checks':rows,'pass_count':sum(x['pass'] for x in rows),'total':len(rows)}
    out['status']='PASS' if out['pass_count']==out['total'] else 'FAIL'
    p=ROOT/'outputs/v0_6D1_R3_4/FORMAL_AUDIT_v0_6D1_R3_4.json'; p.write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
    raise SystemExit(0 if out['status']=='PASS' else 1)
if __name__=='__main__':main()
