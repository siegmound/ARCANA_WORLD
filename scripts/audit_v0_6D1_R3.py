from __future__ import annotations
from pathlib import Path
import hashlib, json, sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import rebased_deep_time_barrier_provider_v0_6D1_R3 as bp

OUT = ROOT / 'outputs/v0_6D1_R3'
REF = ROOT / 'references/v0_6D1_R3'
checks = {}
detail = {}

def check(name, cond, value=None):
    checks[name] = bool(cond)
    if value is not None:
        detail[name] = value

# Exact surviving provider authority.
src = ROOT/'src/d3_paleogeographic_history_v0_6_3D3_2C.py'
h = hashlib.sha256(src.read_bytes()).hexdigest()
check('d3_2c_source_hash_exact', h == '5831f41ba9cd7bc05be0cd25f8cd84e895c6c9fa453bde7634d7b27c82394730', h)

# Full A1 binding.
a1 = np.load(REF/'FULL_A1_REFERENCE_210_0Ma.npz', allow_pickle=False)
ages = a1['age_ma'].astype(float).tolist()
check('full_a1_age_sequence_exact', ages == [210.0,180.0,150.0,140.0,130.0,120.0,90.0,66.0,60.0,30.0,0.0], ages)
cat = bp.build_all_transition_schedules(a1)
check('ten_adjacent_barrier_brackets', cat['summary']['bracket_count'] == 10, cat['summary'])
check('event_cluster_inventory_801', cat['summary']['event_cluster_count'] == 801, cat['summary']['event_cluster_count'])
check('transition_inventory_12366', cat['summary']['transition_cells_counted_across_brackets'] == 12366, cat['summary']['transition_cells_counted_across_brackets'])
check('all_events_marked_derived_not_observed', all(e['semantic_status']=='DERIVED_ENDPOINT_CONSTRAINED_EVENT_CLUSTER_NOT_INDEPENDENT_GEOLOGICAL_OBSERVATION' for e in cat['events']))

endpoint_ok = True
for i, age in enumerate(a1['age_ma'].astype(float)):
    env = bp.environment_at(float(age), a1)
    endpoint_ok &= np.array_equal(env['land_support'], a1['land_mask'][i].astype(float))
check('all_land_support_endpoints_exact', endpoint_ok)

# Old D3.2C evidence preserved.
old_audit = json.loads((REF/'D3_2C_PALEOGEOGRAPHIC_HISTORY_AUDIT.json').read_text())
check('parent_d3_2c_physical_audit_pass', old_audit.get('status') == 'PASS_PALEOGEOGRAPHIC_BARRIER_HISTORY_PHYSICAL_AUDIT_CANDIDATE')
crit = json.loads((REF/'D3_2C_convergence_12_5__CRITICAL_WINDOW_CONVERGENCE_SUMMARY.json').read_text())
check('parent_d3_2c_25_vs_12p5_birth_identity_preserved', bool(crit['early_14_15_5']['same_species_ids'] and crit['late_17_19_5']['same_species_ids']))

# R3 rebase-specific event-driven activation evidence.
smoke = json.loads((OUT/'R3B_210_205_FISSION_ON_SMOKE.json').read_text())
check('r3_210_205_species_richness_preserved', smoke['species_count'] == 120, smoke['species_count'])
check('r3_210_205_no_speciation', smoke['counts']['speciation'] == 0, smoke['counts'])
check('r3_210_205_no_ordinary_extinction', smoke['counts']['ordinary_background_extinction'] == 0, smoke['counts'])
check('r3_210_205_fission_count_18', smoke['counts']['deme_fission'] == 18, smoke['counts']['deme_fission'])
check('r3_fission_is_deme_only', all(e.get('semantic_status')=='D3_2C_EVENT_HISTORY_BOUND_PERSISTENT_VICARIANCE_DEMOGRAPHIC_FRAGMENT_NOT_SPECIES' for e in smoke['events'] if e['event']=='deme_fission'))

sens = json.loads((OUT/'R3B_BARRIER_FISSION_SENSITIVITY_SUMMARY.json').read_text())
check('width0p5_preserves_materialized_parent_identity', sens['materialized_210_205']['parent_identity_exact'])
check('wide_envelope_and_width2_preserve_candidate_parents', sens['preactuation_210_206']['all_parent_candidate_sets_exact'])
check('sub_myr_fission_timing_not_sealed', 'TIMING_DIAGNOSTIC_NOT_SEALED' in sens['interpretation'])

# Governance / scope.
config = json.loads((ROOT/'configs/world1_rebased_h0_barrier_history_v0_6D1_R3.json').read_text())
check('deep_biological_coupling_off', config['deep_biological_coupling'] is False)
check('no_global_speciation_rate', config['global_speciation_rate'] is None)
check('no_global_extinction_rate', config['global_extinction_rate'] is None)
check('d3_2b_connectivity_threshold_reused', abs(float(config['connectivity_land_support_threshold'])-0.25)<1e-15 and abs(float(config['effective_connectivity_core_threshold'])-0.20)<1e-15)
check('d3_2c_event_envelope_reused', abs(float(config['barrier_phase_min'])-0.05)<1e-15 and abs(float(config['barrier_phase_max'])-0.95)<1e-15 and abs(float(config['barrier_transition_width_years'])-1_000_000.0)<1e-9)
check('initial_fragmentation_is_grandfathered', config['initial_fragmentation_policy']=='GRANDFATHERED_UNTIL_CONNECTED_THEN_NEW_SPLIT')

# Local runner smoke evidence.
ls = json.loads((OUT/'local_runner_smoke/210_to_209p0Ma_summary.json').read_text())
check('local_runner_smoke_210_209_richness_120', ls['species_count'] == 120)
check('local_runner_smoke_no_events', ls['event_counts'] == {}, ls['event_counts'])

status = 'PASS_REBASED_DEEP_TIME_BARRIER_HISTORY_BINDING_AND_FISSION_ACTIVATION_CANDIDATE' if all(checks.values()) else 'FAIL_R3_FORMAL_AUDIT'
obj = {'stage':'v0.6D1-R3','status':status,'checks':checks,'detail':detail,'pass_count':sum(checks.values()),'check_count':len(checks)}
(OUT/'FORMAL_AUDIT_v0_6D1_R3.json').write_text(json.dumps(obj, indent=2))
print(json.dumps(obj, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
