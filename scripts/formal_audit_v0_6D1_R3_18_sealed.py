from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np

ROOT0 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT0 / 'src'))

from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
from arcana_worldsim.scientific_engines import r318_recent_exposure_transport_readiness as r318

STAGE = 'v0.6D1-R3.18'
CANONICAL_VERDICT = (
    'PASS_R318_120KA_TO_0_RECENT_H0_EXPOSURE_COMPLETED__'
    '125KA_BIOLOGY_PRESERVED_TRANSPORT_PHASE_OPERATOR_AUDIT_READY'
)
SEALED_VERDICT = (
    'PASS_R318_120KA_TO_0_RECENT_H0_EXPOSURE_COMPLETED__'
    '125KA_BIOLOGY_PRESERVED_TRANSPORT_PHASE_READINESS_SEALED'
)
EXPECTED_ENVELOPE_SHA256 = '45f42200faa315ad7fe69f4fa8bcb1019c8f0c8dcb90fc2a18488bd40a9df58a'
EXPECTED_BUNDLE_SHA256 = '54172b22540b854115e82c041d4fb8dc2f0bdfbbc6784c669c145ba1db0c1a70'
EXPECTED_SUMMARY_SHA256 = '189007565f3f70c89b73e71bb4c23e9339bb392c550408a08b0d43c60f71317a'
EXPECTED_POP = 1217.8946033288662
EXPECTED_PHASE_DIVERGENCE = 1.5816467428221057
EXPECTED_CLOSURE_MAX = 6.984919309616089e-09
EXPECTED_INACCESSIBLE_0 = 3.5009958898334106e-11


def hfile(path: Path) -> str:
    h = sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def f_eq(a: Any, b: float, atol: float = 1e-12) -> bool:
    try:
        return abs(float(a) - float(b)) <= atol
    except Exception:
        return False


def core_equal(a: dict[str, Any], b: dict[str, Any], key: str) -> bool:
    return a.get(key) == b.get(key)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--run-dir', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--seal-out', type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve(); run = args.run_dir.resolve(); out = args.out.resolve(); seal_out = args.seal_out.resolve()

    envp = run / 'R3_18_RECENT_EXPOSURE_TRANSPORT_PHASE_READINESS_ENVELOPE.json'
    bunp = run / 'R3_18_125KA_TO_0_EXPOSURE_AND_TRANSPORT_PHASES.npz'
    sump = run / 'R3_18_RECENT_EXPOSURE_COMPLETION_SUMMARY.json'

    checks: list[dict[str, Any]] = []
    def ck(name: str, passed: bool, actual: Any = None, expected: Any = None) -> None:
        checks.append({'name': name, 'pass': bool(passed), 'actual': actual, 'expected': expected})

    for label, path in [('envelope', envp), ('bundle', bunp), ('summary', sump)]:
        ck(f'{label}_exists', path.is_file(), str(path), 'file')
    if not all(p.is_file() for p in (envp, bunp, sump)):
        failed = [x for x in checks if not x['pass']]
        audit={'schema':'ARCANA_R318_FORMAL_SEALED_AUDIT_V1','stage':STAGE,'verdict':'FAIL_R318_SEALED_AUDIT','checks':f"{len(checks)-len(failed)}/{len(checks)}",'failed':failed,'check_rows':checks}
        out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(audit, indent=2), encoding='utf-8')
        print(json.dumps({'verdict':audit['verdict'],'checks':audit['checks'],'audit':str(out)}, indent=2)); return 1

    env = json.loads(envp.read_text(encoding='utf-8'))
    summary = json.loads(sump.read_text(encoding='utf-8'))
    bundle = r318.load_integral_bundle(bunp)
    env_sha, bun_sha, sum_sha = hfile(envp), hfile(bunp), hfile(sump)

    ck('envelope_sha_exact', env_sha == EXPECTED_ENVELOPE_SHA256, env_sha, EXPECTED_ENVELOPE_SHA256)
    ck('bundle_sha_exact', bun_sha == EXPECTED_BUNDLE_SHA256, bun_sha, EXPECTED_BUNDLE_SHA256)
    ck('summary_sha_exact', sum_sha == EXPECTED_SUMMARY_SHA256, sum_sha, EXPECTED_SUMMARY_SHA256)
    ck('summary_stage', summary.get('stage') == STAGE, summary.get('stage'), STAGE)
    ck('summary_verdict', summary.get('verdict') == CANONICAL_VERDICT, summary.get('verdict'), CANONICAL_VERDICT)
    ck('summary_physical_end_0', f_eq(summary.get('physical_end_age_ma'), 0.0), summary.get('physical_end_age_ma'), 0.0)
    ck('summary_biology_age_125ka', f_eq(summary.get('biology_state_age_ma'), .125), summary.get('biology_state_age_ma'), .125)
    ck('summary_biology_identity', summary.get('biology_state_identity_exact') is True, summary.get('biology_state_identity_exact'), True)
    ck('summary_species_134', summary.get('species') == 134, summary.get('species'), 134)
    ck('summary_components_295', summary.get('components') == 295, summary.get('components'), 295)
    ck('summary_population', f_eq(summary.get('population'), EXPECTED_POP, 1e-9), summary.get('population'), EXPECTED_POP)
    ck('summary_recent_120k', f_eq(summary.get('recent_environmental_years_integrated'), 120000.0, 1e-6), summary.get('recent_environmental_years_integrated'), 120000.0)
    ck('summary_full_125k', f_eq(summary.get('full_macrostep_environmental_years'), 125000.0, 1e-6), summary.get('full_macrostep_environmental_years'), 125000.0)
    ck('summary_transport_boundary', f_eq(summary.get('transport_boundary_age_ma'), .0625), summary.get('transport_boundary_age_ma'), .0625)
    ck('summary_phase_aware_required', summary.get('phase_aware_transport_operator_required') is True, summary.get('phase_aware_transport_operator_required'), True)
    ck('summary_biology_not_advanced', summary.get('biology_advanced') is False, summary.get('biology_advanced'), False)
    ck('summary_transport_not_advanced', summary.get('transport_advanced') is False, summary.get('transport_advanced'), False)

    ck('envelope_schema', env.get('schema') == r318.ENVELOPE_SCHEMA, env.get('schema'), r318.ENVELOPE_SCHEMA)
    ck('envelope_biology_not_mutated', env.get('biology_state_mutated') is False, env.get('biology_state_mutated'), False)
    ck('envelope_not_relabelled', env.get('biology_state_relabelled_to_0ka') is False, env.get('biology_state_relabelled_to_0ka'), False)
    phase = env.get('transport_phases', {})
    ck('phase1_62500', f_eq(phase.get('phase1',{}).get('duration_years'),62500.0,1e-6), phase.get('phase1',{}).get('duration_years'),62500.0)
    ck('phase2_62500', f_eq(phase.get('phase2',{}).get('duration_years'),62500.0,1e-6), phase.get('phase2',{}).get('duration_years'),62500.0)
    div = phase.get('effective_environment_divergence', {})
    ck('phase_divergence_not_roundoff', div.get('roundoff_equivalent_all_fields') is False, div.get('roundoff_equivalent_all_fields'), False)
    ck('phase_divergence_exact', f_eq(div.get('global_max_abs_difference'), EXPECTED_PHASE_DIVERGENCE, 1e-12), div.get('global_max_abs_difference'), EXPECTED_PHASE_DIVERGENCE)
    ck('phase_operator_required', phase.get('phase_aware_transport_operator_required') is True, phase.get('phase_aware_transport_operator_required'), True)
    closure = env.get('full_125ka_macrostep',{}).get('integral_phase_closure_max_abs')
    ck('closure_under_1e6', float(closure) <= 1e-6, closure, '<=1e-6')
    ck('closure_matches_canonical', f_eq(closure, EXPECTED_CLOSURE_MAX, 1e-12), closure, EXPECTED_CLOSURE_MAX)
    support = env.get('support_diagnostics', {})
    ck('support_120_62_no_loss', support.get('120_to_62p5',{}).get('lost_accessible_cell_count') == 0, support.get('120_to_62p5',{}).get('lost_accessible_cell_count'),0)
    ck('support_120_62_gain_81', support.get('120_to_62p5',{}).get('gained_accessible_cell_count') == 81, support.get('120_to_62p5',{}).get('gained_accessible_cell_count'),81)
    ck('support_62_0_loss_1758', support.get('62p5_to_0',{}).get('lost_accessible_cell_count') == 1758, support.get('62p5_to_0',{}).get('lost_accessible_cell_count'),1758)
    ck('support_62_0_no_remap', support.get('62p5_to_0',{}).get('remap_applied') is False, support.get('62p5_to_0',{}).get('remap_applied'),False)
    mass = env.get('parent_population_endpoint_inaccessible_mass', {})
    ck('mass_inaccessible_62_zero', f_eq(mass.get('at_62p5ka'),0.0,1e-12), mass.get('at_62p5ka'),0.0)
    ck('mass_inaccessible_0_tiny', abs(float(mass.get('at_0ka',99))) <= 1e-9, mass.get('at_0ka'),'<=1e-9')
    ck('mass_inaccessible_0_matches', f_eq(mass.get('at_0ka'),EXPECTED_INACCESSIBLE_0,1e-15), mass.get('at_0ka'),EXPECTED_INACCESSIBLE_0)
    gov = env.get('governance', {})
    for key in ('biology_advanced','transport_advanced','gene_flow_advanced','lifecycle_gates_advanced','biology_cadence_changed','transport_cadence_changed','adaptive_clock_used_as_biology_timestep','support_remap_applied','scientific_parameter_changes','deep_biological_coupling','richness_target_used','human_lineage_target_used','production_biology_closure_authorized_in_r318'):
        ck(f'governance_false::{key}', gov.get(key) is False, gov.get(key), False)

    ck('bundle_biology_age', f_eq(bundle.get('biology_state_age_ma'),.125), bundle.get('biology_state_age_ma'),.125)
    ck('bundle_end_age', f_eq(bundle.get('physical_end_age_ma'),0.0), bundle.get('physical_end_age_ma'),0.0)
    ck('bundle_transport_boundary', f_eq(bundle.get('transport_boundary_age_ma'),.0625), bundle.get('transport_boundary_age_ma'),.0625)
    expected_groups={'recent_120_to_0','full_125_to_0','transport_phase1_125_to_62p5','transport_phase2_62p5_to_0'}
    ck('bundle_groups', set(bundle.get('groups',{})) == expected_groups, sorted(bundle.get('groups',{})), sorted(expected_groups))
    for g in sorted(expected_groups):
        fields=bundle.get('groups',{}).get(g,{})
        ck(f'bundle_fields::{g}', set(fields)==set(r318.AVERAGED_FIELDS), sorted(fields), sorted(r318.AVERAGED_FIELDS))
        for k in r318.AVERAGED_FIELDS:
            arr=np.asarray(fields.get(k),dtype=float)
            ck(f'bundle_finite::{g}::{k}', bool(np.isfinite(arr).all()))

    # Exact algebraic closure of the stored integral groups within the established numerical tolerance.
    for k in r318.AVERAGED_FIELDS:
        full=np.asarray(bundle['groups']['full_125_to_0'][k],float)
        p1=np.asarray(bundle['groups']['transport_phase1_125_to_62p5'][k],float)
        p2=np.asarray(bundle['groups']['transport_phase2_62p5_to_0'][k],float)
        err=float(np.max(np.abs(full-(p1+p2))))
        ck(f'bundle_phase_closure::{k}', err <= 1e-6, err, '<=1e-6')

    # Rehydrate all SEALED parent authorities and independently reproduce R3.18.
    parent = r318.validate_parent_r317_authority(root)
    st=parent['state']; a1=parent['a1']; c2=parent['c2']; clock=parent['clock']; pending=parent['pending']
    ck('parent_biology_125ka', f_eq(st.age_ma,.125), st.age_ma,.125)
    ck('parent_species_134', len(set(st.current_species))==134, len(set(st.current_species)),134)
    ck('parent_components_295', len(st.component_ids)==295, len(st.component_ids),295)
    ck('parent_population', f_eq(float(st.pop.sum()),EXPECTED_POP,1e-9), float(st.pop.sum()),EXPECTED_POP)
    before=deepcopy(st)
    live_env, live_groups = r318.build_recent_exposure_readiness(st,a1,c2,clock,pending,r318.R318Config())
    cmp=r38.compare_runtime_states(before,st,atol=0.0)
    ck('independent_parent_state_unchanged', cmp.get('equivalent') is True, cmp.get('equivalent'),True)
    for key in ('schema','stage','physical_start_age_ma','physical_end_age_ma','biology_state_age_ma','biology_state_mutated','biology_state_relabelled_to_0ka','recent_exposure','full_125ka_macrostep','transport_phases','support_diagnostics','parent_population_endpoint_inaccessible_mass','governance','next_stage_requirement'):
        ck(f'independent_envelope_core::{key}', core_equal(env,live_env,key), env.get(key),live_env.get(key))
    ck('independent_group_set', set(live_groups)==set(bundle['groups']), sorted(live_groups),sorted(bundle['groups']))
    for g in sorted(expected_groups):
        for k in r318.AVERAGED_FIELDS:
            a=np.asarray(live_groups[g][k],float); b=np.asarray(bundle['groups'][g][k],float)
            ck(f'independent_shape::{g}::{k}', a.shape==b.shape, a.shape,b.shape)
            ck(f'independent_exact::{g}::{k}', np.array_equal(a,b), float(np.max(np.abs(a-b))) if a.shape==b.shape and a.size else None,0.0)

    art=summary.get('artifacts',{})
    ck('summary_envelope_pointer', art.get('readiness_envelope_sha256')==EXPECTED_ENVELOPE_SHA256, art.get('readiness_envelope_sha256'),EXPECTED_ENVELOPE_SHA256)
    ck('summary_bundle_pointer', art.get('integral_bundle_sha256')==EXPECTED_BUNDLE_SHA256, art.get('integral_bundle_sha256'),EXPECTED_BUNDLE_SHA256)
    ck('summary_bundle_roundtrip', art.get('bundle_roundtrip_exact') is True, art.get('bundle_roundtrip_exact'),True)

    failed=[x for x in checks if not x['pass']]
    verdict=SEALED_VERDICT if not failed else 'FAIL_R318_SEALED_AUDIT'
    audit={
        'schema':'ARCANA_R318_FORMAL_SEALED_AUDIT_V1','stage':STAGE,'verdict':verdict,
        'checks':f"{len(checks)-len(failed)}/{len(checks)}",'failed':failed,
        'decision':'RECENT_120KA_TO_0_EXPOSURE_AND_TWO_62P5KYR_TRANSPORT_PHASE_INTEGRALS_SEALED__BIOLOGY_REMAINS_125KA',
        'boundary':{
            'physical_environment_age_ma':0.0,'biology_state_age_ma':.125,'species':134,'components':295,'population':EXPECTED_POP,
            'transport_boundary_age_ma':.0625,'transport_phase_years':[62500.0,62500.0],
            'phase_aware_transport_operator_required':True,'phase_environment_global_max_abs_difference':EXPECTED_PHASE_DIVERGENCE,
            'population_mass_inaccessible_at_62p5ka':0.0,'population_mass_inaccessible_at_0ka':EXPECTED_INACCESSIBLE_0,
        },
        'canonical_artifacts':{
            'readiness_envelope':str(envp),'readiness_envelope_sha256':env_sha,
            'integral_bundle':str(bunp),'integral_bundle_sha256':bun_sha,
            'summary':str(sump),'summary_sha256':sum_sha,
        },
        'independent_replay':{
            'enabled':True,'biology_state_identity_exact':bool(cmp.get('equivalent')),
            'integral_bundle_array_identity_exact':not any(x['name'].startswith('independent_exact::') and not x['pass'] for x in checks),
            'envelope_core_identity_exact':not any(x['name'].startswith('independent_envelope_core::') and not x['pass'] for x in checks),
        },
        'production_biology_closure_authorized':False,
        'scientific_parameter_changes':False,'biology_cadence_changes':False,'transport_cadence_changes':False,'deep_biological_coupling':False,
        'check_rows':checks,
    }
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(audit,indent=2),encoding='utf-8')
    if not failed:
        seal={
            'schema':'ARCANA_R318_SEAL_SUMMARY_V1','stage':STAGE,'verdict':SEALED_VERDICT,
            'formal_audit':str(out),'formal_audit_sha256':hfile(out),'formal_audit_checks':audit['checks'],
            'boundary':audit['boundary'],'canonical_artifacts':audit['canonical_artifacts'],
            'parent_authority':{
                'stage':'v0.6D1-R3.17','r317_seal_sha256':parent['r317_seal_sha256'],'r317_audit_sha256':parent['r317_audit_sha256'],
                'r317_summary_sha256':parent['r317_summary_sha256'],'r317_envelope_sha256':parent['r317_envelope_sha256'],'r317_accumulator_sha256':parent['r317_accumulator_sha256'],
            },
            'independent_replay':audit['independent_replay'],
            'governance':{
                'recent_environmental_exposure_to_0ka_sealed':True,'biology_state_remains_at_125ka':True,
                'two_62p5k_transport_phase_integrals_sealed':True,'phase_aware_transport_operator_required':True,
                'biology_advanced':False,'transport_advanced':False,'support_remap_applied':False,
                'biology_cadence_changed':False,'transport_cadence_changed':False,'gene_flow_cadence_changed':False,
                'deep_biological_coupling':False,'scientific_parameter_changes':False,
            },
            'next':'v0.6D1-R3.19 — Phase-Aware Two-Transport-Substep Operator Validation & H0 Biology Closure Candidate',
        }
        seal_out.write_text(json.dumps(seal,indent=2),encoding='utf-8')
    print(json.dumps({'verdict':verdict,'checks':audit['checks'],'audit':str(out),'seal':str(seal_out) if not failed else None},indent=2))
    try:
        if hasattr(a1,'close'): a1.close()
    except Exception:
        pass
    return 0 if not failed else 1

if __name__=='__main__':
    raise SystemExit(main())
