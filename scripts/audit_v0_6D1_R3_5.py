from __future__ import annotations
from pathlib import Path
import json, sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import rebased_natural_control_runtime_v0_6D1_R3_5 as r35
import rebased_natural_control_runtime_v0_6D1_R3_4 as r34

checks=[]
def ck(name, ok, detail=''):
    checks.append({'check':name,'pass':bool(ok),'detail':str(detail)})

cfg=r35.R35Config(); p=r34.R34Config()
ck('stage_id',r35.R35_STAGE_ID=='v0.6D1-R3.5')
ck('deep_biological_off',r35.R35_DEEP_BIOLOGICAL_COUPLING_ENABLED is False)
ck('default_ceiling_0p08',abs(cfg.variance_ceiling_normalized-0.08)<1e-15)
ck('mu_unchanged',abs(cfg.mutation_variance_supply_normalized_per_myr-0.002)<1e-15)
ck('b_unchanged',abs(cfg.nonlinear_stabilizing_variance_depletion_per_myr_per_q-0.9876543209876544)<1e-15)
ck('biology_cadence_unchanged',cfg.biology_cadence_years==p.biology_cadence_years==125000.0)
ck('transport_cadence_unchanged',cfg.transport_cadence_years==p.transport_cadence_years==62500.0)
for k in r34.R34Config.__dataclass_fields__:
    if k=='variance_ceiling_normalized':
        continue
    ck(f'parent_parameter_unchanged::{k}',getattr(cfg,k)==getattr(p,k),f'{getattr(cfg,k)} vs {getattr(p,k)}')

src=(ROOT/'src/rebased_natural_control_runtime_v0_6D1_R3_5.py').read_text(encoding='utf-8')
ck('parent_runtime_called_not_reimplemented','r34.run(common, a1, metadata_rows, parent_cfg)' in src)
ck('d3_gene_flow_wrapped','av.gene_flow_moment_mix = gf_wrapper' in src)
ck('d3_homeostasis_wrapped','av.advance_nonflow_variance = nf_wrapper' in src)
ck('diagnostic_unclipped_not_fed_back','diagnostic_unclipped' in src and 'return actual, components' in src)
ck('instrumentation_restores_functions','av.gene_flow_moment_mix = original_gf' in src and 'av.advance_nonflow_variance = original_nf' in src)
ck('near_ceiling_lineage_telemetry','near_ceiling_reservoirs' in src and 'root_species' in src)
ck('same_step_event_context','event_counts_same_step' in src)

parity=json.loads((ROOT/'outputs/v0_6D1_R3_5/INSTRUMENTATION_BIT_EXACT_PARITY_210_209.json').read_text())
for f in ['population','trait','va','generation_time','ri','clock','contact','trait_distance','component_guild']:
    ck(f'instrumentation_bit_exact::{f}',parity[f]['array_equal'] and parity[f]['max_abs']==0.0)
ck('instrumentation_events_bit_exact',parity['events_equal'])
ck('instrumentation_component_ids_bit_exact',parity['component_ids_equal'])
ck('instrumentation_component_species_bit_exact',parity['component_species_equal'])
ck('instrumentation_records_present',parity['telemetry_records']==8)

s08=json.loads((ROOT/'outputs/v0_6D1_R3_5/DYNAMIC_SUMMARY_210_208_q0.08.json').read_text())
s10=json.loads((ROOT/'outputs/v0_6D1_R3_5/DYNAMIC_SUMMARY_210_208_q0.10.json').read_text())
cmp=json.loads((ROOT/'outputs/v0_6D1_R3_5/DYNAMIC_CEILING_SENSITIVITY_210_208.json').read_text())
ck('pre_contact_population_identical',cmp['final_total_population_abs_diff']==0.0)
ck('pre_contact_event_counts_identical',cmp['event_counts_equal'])
ck('pre_contact_peak_q_identical',cmp['peak_q_diff']==0.0)
ck('pre_contact_no_clipping_0p08',s08['headroom']['steps_with_homeostasis_clipping']==0)
ck('pre_contact_no_clipping_0p10',s10['headroom']['steps_with_homeostasis_clipping']==0)

s206=json.loads((ROOT/'outputs/v0_6D1_R3_5/DYNAMIC_SUMMARY_210_206_q0.08.json').read_text())
ck('eventful_window_contains_fission',s206['event_counts'].get('deme_fission',0)>0)
ck('eventful_window_contains_coalescence',s206['event_counts'].get('deme_coalescence',0)>0)
ck('eventful_window_no_clipping',s206['headroom']['steps_with_homeostasis_clipping']==0)
ck('eventful_window_headroom_below_cap',s206['headroom']['peak_after_homeostasis_q']<0.08)

ck('primary_dual_runner_exists',(ROOT/'run_v0_6D1_R3_5_sensitivity_windows.ps1').exists())
ck('single_runner_exists',(ROOT/'run_v0_6D1_R3_5_windows.ps1').exists())
ck('comparison_script_exists',(ROOT/'scripts/compare_v0_6D1_R3_5_dynamic_sensitivity.py').exists())
ck('r3_4_long_run_audit_reference_exists',(ROOT/'R3_4_210_150_LONG_RUN_AUDIT_REFERENCE.md').exists())
ck('full_210_150_dynamic_sensitivity_not_falsely_claimed',not (ROOT/'outputs/v0_6D1_R3_5/FULL_210_150_DYNAMIC_SENSITIVITY.json').exists())

passed=sum(x['pass'] for x in checks)
out={'stage':'v0.6D1-R3.5','status':'PASS' if passed==len(checks) else 'FAIL','passed':passed,'total':len(checks),'checks':checks,
     'verdict':'PASS_TIME_RESOLVED_VA_HEADROOM_INSTRUMENTATION_AND_DYNAMIC_SENSITIVITY_RUNPACK_CANDIDATE__FULL_210_TO_150_DUAL_REPLAY_PENDING'}
(ROOT/'outputs/v0_6D1_R3_5/FORMAL_AUDIT_v0_6D1_R3_5.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
raise SystemExit(0 if out['status']=='PASS' else 1)
