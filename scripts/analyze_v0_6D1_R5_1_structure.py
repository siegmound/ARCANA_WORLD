from __future__ import annotations
import argparse, json
from pathlib import Path
from arcana_worldsim.state_query.r51_structure import analyze_structure, save_structure_outputs, R51StructureError


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    args = ap.parse_args()
    try:
        result = analyze_structure(args.root.resolve())
        saved = save_structure_outputs(args.root.resolve(), result)
    except R51StructureError as e:
        print(json.dumps({'stage':'v0.6D1-R5.1','status':'BLOCKED_R51_CRADLE_STRUCTURE_AND_ENGINE_ADJUDICATION','error':str(e)}, indent=2))
        raise SystemExit(2)
    s = result['structure']
    summary = {
        'stage': s['stage'], 'status': s['status'],
        'region_record_count': s['region_record_count'],
        'pareto_region_record_count': s['pareto_region_record_count'],
        'family_count': s['family_count'],
        'all_threshold_family_count': s['all_threshold_family_count'],
        'per_candidate': s['per_candidate'],
        'cross_lineage_overlap_pair_count': s['cross_lineage_all_threshold_core_overlap']['nonzero_overlap_pair_count'],
        'cross_lineage_max_jaccard': s['cross_lineage_all_threshold_core_overlap']['max_jaccard'],
        'closure_readiness': s['closure_readiness'],
        'new_external_engine_execution_required_for_r51_closure': s['engine_adjudication']['new_external_engine_execution_required_for_r51_closure'],
        'new_external_engine_execution_authorized_in_r51': s['engine_adjudication']['new_external_engine_execution_authorized_in_r51'],
        'RangeShifter_action': s['engine_adjudication']['RangeShifter']['action'],
        'recommended_next_action': s['recommended_next_action'],
        'structure_manifest_sha256': saved['manifest_sha256'],
    }
    print(json.dumps(summary, indent=2))
    print('PASS_R51_CRADLE_STRUCTURE_AND_ENGINE_ADJUDICATION_RUN')

if __name__ == '__main__':
    main()
