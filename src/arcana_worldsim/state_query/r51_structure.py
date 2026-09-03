from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json
import numpy as np

from . import r51_cradle as c

STAGE = c.STAGE
OUT_REL = Path('outputs/v0_6D1_R5_1')
ATLAS_NAME = 'R5_1_CRADLE_OPPORTUNITY_ATLAS.npz'
REGISTRY_NAME = 'R5_1_CRADLE_CANDIDATE_REGISTRY.json'
AUDIT_NAME = 'R5_1_INTEGRATED_AUDIT.json'
MANIFEST_NAME = 'R5_1_OUTPUT_MANIFEST.json'
THRESHOLDS = c.THRESHOLD_QUANTILES

class R51StructureError(RuntimeError):
    pass


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _load_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding='utf-8'))


def _write_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')


def validate_candidate_outputs(root: Path, allow_non_scientific_dev: bool = False) -> dict[str, Any]:
    root = Path(root)
    out = root / OUT_REL
    paths = {
        'atlas': out / ATLAS_NAME,
        'registry': out / REGISTRY_NAME,
        'audit': out / AUDIT_NAME,
        'manifest': out / MANIFEST_NAME,
    }
    checks = {f'present::{k}': p.is_file() for k, p in paths.items()}
    if all(checks.values()):
        audit = _load_json(paths['audit'])
        manifest = _load_json(paths['manifest'])
        checks['audit_scientific_candidate_eligible'] = (audit.get('scientific_candidate_eligible') is True) or bool(allow_non_scientific_dev)
        checks['audit_status_exact'] = audit.get('status') == 'PASS_R51_EMERGENT_HOMINID_CRADLE_ECOLOGICAL_NICHE_DISCOVERY_CANDIDATE'
        checks['audit_canonical_unchanged'] = (audit.get('summary') or {}).get('canonical_state_changed') is False
        checks['audit_deep_coupling_off'] = (audit.get('summary') or {}).get('deep_biological_coupling') is False
        files = manifest.get('files') or {}
        required = {
            'R5_1_ENGINE_UTILITY_REVIEW.json', ATLAS_NAME,
            'R5_1_OCCUPIED_ENVIRONMENT_ENVELOPES.json', REGISTRY_NAME, AUDIT_NAME,
        }
        checks['manifest_exact_candidate_allowlist'] = set(files) == required
        checks['manifest_file_hashes_match'] = all(
            (out / name).is_file() and rec.get('sha256') == _sha256(out / name) and rec.get('bytes') == (out / name).stat().st_size
            for name, rec in files.items()
        )
        checks['audit_atlas_hash_matches'] = (audit.get('summary') or {}).get('atlas_sha256') == _sha256(paths['atlas'])
        reg = _load_json(paths['registry'])
        checks['registry_threshold_family_exact'] = tuple(reg.get('threshold_quantiles') or []) == THRESHOLDS
        checks['registry_no_single_winner_semantics'] = 'NO_SINGLE_WINNER' in str(reg.get('selection_semantics', ''))
    else:
        for k in (
            'audit_scientific_candidate_eligible','audit_status_exact','audit_canonical_unchanged','audit_deep_coupling_off',
            'manifest_exact_candidate_allowlist','manifest_file_hashes_match','audit_atlas_hash_matches',
            'registry_threshold_family_exact','registry_no_single_winner_semantics'):
            checks[k] = False
    failed = [k for k, v in checks.items() if not bool(v)]
    return {
        'stage': STAGE,
        'status': 'PASS_R51_CANDIDATE_OUTPUT_INTEGRITY' if not failed else 'BLOCKED_R51_CANDIDATE_OUTPUT_INTEGRITY',
        'checks_passed': sum(bool(v) for v in checks.values()),
        'checks_total': len(checks),
        'failed': failed,
        'checks': {k: bool(v) for k, v in checks.items()},
    }


def _reconstruct_components(mass: np.ndarray, land: np.ndarray) -> dict[float, list[set[int]]]:
    nr, nc = mass.shape
    positive = mass[mass > 0]
    out: dict[float, list[set[int]]] = {}
    for q in THRESHOLDS:
        threshold = float(np.quantile(positive, q)) if positive.size else float('inf')
        mask = (mass >= threshold) & (mass > 0) & (land > 0)
        comps = c._components(mask)
        out[q] = [set(r * nc + col for r, col in cells) for cells in comps]
    return out


def _registry_integrity(regions: list[dict[str, Any]], atlas: dict[str, np.ndarray]) -> tuple[bool, dict[str, Any]]:
    ids = tuple(map(str, atlas['candidate_ids'].tolist()))
    lat = np.asarray(atlas['lat'], float)
    lon = np.asarray(atlas['lon'], float)
    mass_all = np.asarray(atlas['population_mass_fraction'], float)
    land = np.asarray(atlas['land_persistence_fraction'], float)
    details: dict[str, Any] = {}
    ok = True
    for j, sid in enumerate(ids):
        comps = _reconstruct_components(mass_all[j], land)
        sub = [r for r in regions if r['candidate_id'] == sid]
        expected_count = sum(len(v) for v in comps.values())
        if len(sub) != expected_count:
            ok = False
        per_q = {}
        for q in THRESHOLDS:
            rows = sorted([r for r in sub if abs(float(r['threshold_quantile']) - q) < 1e-12], key=lambda r: int(r['component_index']))
            qs = comps[q]
            qok = len(rows) == len(qs)
            if qok:
                for idx, cells in enumerate(qs):
                    rr = np.array([x // len(lon) for x in sorted(cells)], int)
                    cc = np.array([x % len(lon) for x in sorted(cells)], int)
                    rec = rows[idx]
                    if int(rec['cell_count']) != len(cells): qok = False
                    if list(map(int, rec['row_minmax'])) != [int(rr.min()), int(rr.max())]: qok = False
                    if list(map(int, rec['col_minmax'])) != [int(cc.min()), int(cc.max())]: qok = False
            per_q[str(q)] = {'component_count': len(qs), 'registry_count': len(rows), 'exact_structure_match': bool(qok)}
            ok = ok and qok
        details[sid] = {'expected_region_count': expected_count, 'registry_region_count': len(sub), 'thresholds': per_q}
    return bool(ok), details


def _build_families_for_candidate(sid: str, mass: np.ndarray, land: np.ndarray) -> tuple[list[dict[str, Any]], dict[float, list[set[int]]]]:
    comps = _reconstruct_components(mass, land)
    qs = list(THRESHOLDS)
    family_of: dict[tuple[float, int], str] = {}
    families: dict[str, dict[str, Any]] = {}
    for i, cells in enumerate(comps[qs[0]]):
        fid = f'{sid}__F{i:04d}'
        family_of[(qs[0], i)] = fid
        families[fid] = {'family_id': fid, 'candidate_id': sid, 'members': {qs[0]: [i]}}
    for qi in range(1, len(qs)):
        q_prev, q_cur = qs[qi-1], qs[qi]
        prev = comps[q_prev]
        cur = comps[q_cur]
        for ci, cells in enumerate(cur):
            parents = [pi for pi, pcells in enumerate(prev) if cells & pcells]
            if len(parents) != 1:
                raise R51StructureError(f'{sid} q={q_cur} component={ci}: expected exactly one nested parent at q={q_prev}, got {parents}')
            parent_fid = family_of[(q_prev, parents[0])]
            family_of[(q_cur, ci)] = parent_fid
            families[parent_fid]['members'].setdefault(q_cur, []).append(ci)
    records = []
    for fid, fam in sorted(families.items()):
        covered = [q for q in qs if q in fam['members']]
        highest = max(covered)
        highest_cells: set[int] = set()
        for ci in fam['members'][highest]: highest_cells |= comps[highest][ci]
        base_cells: set[int] = set()
        for ci in fam['members'][qs[0]]: base_cells |= comps[qs[0]][ci]
        records.append({
            'family_id': fid,
            'candidate_id': sid,
            'thresholds_present': covered,
            'threshold_coverage_count': len(covered),
            'survives_all_thresholds': len(covered) == len(qs),
            'highest_threshold_quantile': highest,
            'branch_count_at_highest_threshold': len(fam['members'][highest]),
            'base_cell_count': len(base_cells),
            'core_cell_count': len(highest_cells),
            '_base_cells': base_cells,
            '_core_cells': highest_cells,
            'component_indices_by_threshold': {str(q): list(fam['members'][q]) for q in covered},
            '_members': fam['members'],
        })
    return records, comps


def _precompute_j14_cell_support(root: Path, nr: int, nc: int) -> tuple[np.ndarray, tuple[str, ...], list[dict[int, np.ndarray]]]:
    with np.load(Path(root) / c.J14_REL, allow_pickle=False) as z:
        ages = np.asarray(z['age_ma'], float)
        ids = tuple(map(str, z['candidate_ids'].tolist()))
        spatial = np.asarray(z['spatial_state'], float)
    E, ncan, T = spatial.shape[:3]
    by_candidate: list[dict[int, np.ndarray]] = []
    for j in range(ncan):
        mapping: dict[int, np.ndarray] = {}
        for e in range(E):
            for t in range(T):
                ds = spatial[e, j, t]
                for row in ds[ds[:, 3] > 0.5]:
                    r = int(np.clip(np.rint(row[1]), 0, nr - 1))
                    col = int(np.clip(np.rint(row[2]), 0, nc - 1))
                    key = r * nc + col
                    arr = mapping.get(key)
                    if arr is None:
                        arr = np.zeros((T, E), dtype=bool)
                        mapping[key] = arr
                    arr[t, e] = True
        by_candidate.append(mapping)
    return ages, ids, by_candidate


def _longest_true_run(x: np.ndarray) -> int:
    best = cur = 0
    for v in map(bool, x.tolist()):
        if v:
            cur += 1; best = max(best, cur)
        else:
            cur = 0
    return best




def adjudicate_engine_use(per_candidate: dict[str, dict[str, Any]], ids: tuple[str, ...]) -> dict[str, Any]:
    lineage_complete = all(per_candidate[sid]['all_threshold_family_count'] > 0 for sid in ids)
    if lineage_complete:
        closure_readiness = 'READY_FOR_R51_SEAL_NO_NEW_EXTERNAL_ENGINE_REQUIRED'
        next_action = 'SEAL_R51_THEN_USE_RANGESHIFTER_IN_R52_FOR_TARGETED_EXPANSION_CORRIDOR_VALIDATION'
        range_action = 'DEFER_NEW_EXECUTION_TO_R5_2_TARGETED_CORRIDOR_VALIDATION'
        reason = 'Both R3.27 human-cohort lineages retain at least one spatial family across every pre-frozen threshold; external engines are not needed to repair or define R5.1 cradle-opportunity geography.'
    else:
        closure_readiness = 'R51_INTERNAL_SPATIAL_METHOD_REFINEMENT_REQUIRED_BEFORE_SEAL'
        next_action = 'REFINE_ARCANA_INTERNAL_REGION_CONSOLIDATION_BEFORE_ANY_NEW_EXTERNAL_ENGINE_EXECUTION'
        range_action = 'DO_NOT_RUN_FOR_R51_METHOD_REPAIR'
        reason = 'At least one lineage lacks an all-threshold spatial family. An external engine cannot repair an ARCANA internal robustness gap without improperly becoming target authority.'
    return {
        'closure_readiness': closure_readiness,
        'recommended_next_action': next_action,
        'engine_adjudication': {
            'new_external_engine_execution_required_for_r51_closure': False,
            'new_external_engine_execution_authorized_in_r51': False,
            'RangeShifter': {'action': range_action, 'reason': reason},
            'Geonomics': {'action': 'NO_NEW_EXECUTION_REUSE_SEALED_J14_AND_R4_EVIDENCE'},
            'Madingley': {'action': 'DEFER_TARGETED_TROPHIC_CORROBORATION_UNLESS_A_LATER_QUESTION_REQUIRES_IT'},
            'CDMetaPOP': {'action': 'DEFER_TO_PERSISTENCE_BOTTLENECK_CONTACT_STAGE'},
            'NEMO': {'action': 'DEFER_TO_GENETIC_PERSISTENCE_GENE_FLOW_STAGE'},
            'SLiM': {'action': 'DEFER_TO_ANCESTRY_ADMIXTURE_STAGE'},
            'external_engine_defines_arcana_target': False,
            'majority_vote': False,
        },
    }

def analyze_structure(root: Path, allow_non_scientific_dev: bool = False) -> dict[str, Any]:
    root = Path(root)
    integrity = validate_candidate_outputs(root, allow_non_scientific_dev=allow_non_scientific_dev)
    if integrity['failed']:
        raise R51StructureError('R5.1 candidate outputs failed integrity validation')
    out = root / OUT_REL
    registry = _load_json(out / REGISTRY_NAME)
    regions = list(registry.get('regions') or [])
    with np.load(out / ATLAS_NAME, allow_pickle=False) as z:
        atlas = {k: np.asarray(z[k]) for k in z.files}
    ids = tuple(map(str, atlas['candidate_ids'].tolist()))
    mass_all = np.asarray(atlas['population_mass_fraction'], float)
    land = np.asarray(atlas['land_persistence_fraction'], float)
    nr, nc = land.shape

    registry_ok, registry_details = _registry_integrity(regions, atlas)
    if not registry_ok:
        raise R51StructureError('R5.1 region registry cannot be exactly reconstructed from the atlas')

    ages, jids, cell_support = _precompute_j14_cell_support(root, nr, nc)
    if ids != jids:
        raise R51StructureError('Atlas/J14 candidate IDs differ')

    all_families: list[dict[str, Any]] = []
    family_occ_rows: list[np.ndarray] = []
    family_core_masks: dict[str, set[int]] = {}
    per_candidate = {}
    for j, sid in enumerate(ids):
        fams, comps = _build_families_for_candidate(sid, mass_all[j], land)
        for fam in fams:
            core = fam.pop('_core_cells')
            base = fam.pop('_base_cells')
            fam.pop('_members')
            core_idx = np.asarray(sorted(core), dtype=int)
            cr = core_idx // nc; cc = core_idx % nc
            base_idx = np.asarray(sorted(base), dtype=int)
            br = base_idx // nc; bc = base_idx % nc
            cm = mass_all[j, cr, cc]
            cw = cm / max(float(cm.sum()), 1e-30)
            lon_rad = np.deg2rad(np.asarray(atlas['lon'], float)[cc])
            sx = float(np.sum(np.cos(lon_rad) * cw)); sy = float(np.sum(np.sin(lon_rad) * cw))
            circular_lon = float(np.rad2deg(np.arctan2(sy, sx)))
            fam.update({
                'base_row_minmax': [int(br.min()), int(br.max())],
                'base_col_minmax': [int(bc.min()), int(bc.max())],
                'core_row_minmax': [int(cr.min()), int(cr.max())],
                'core_col_minmax': [int(cc.min()), int(cc.max())],
                'core_lat_centroid': float(np.sum(np.asarray(atlas['lat'], float)[cr] * cw)),
                'core_lon_centroid_circular': circular_lon,
                'core_population_mass_fraction_sum': float(np.sum(cm)),
                'core_age_presence_fraction_mean': float(np.mean(np.asarray(atlas['age_presence_fraction'], float)[j, cr, cc])),
                'core_member_coverage_fraction_mean': float(np.mean(np.asarray(atlas['member_coverage_fraction'], float)[j, cr, cc])),
                'core_land_persistence_mean': float(np.mean(land[cr, cc])),
                'core_forage_q10_mean': float(np.mean(np.asarray(atlas['forage_q10'], float)[cr, cc])),
                'core_temperature_std_c_mean': float(np.mean(np.asarray(atlas['temperature_std_c'], float)[cr, cc])),
                'core_aridity_std_mean': float(np.mean(np.asarray(atlas['aridity_std'], float)[cr, cc])),
            })
            ensemble_count = next(iter(cell_support[j].values())).shape[1] if cell_support[j] else 96
            occ = np.zeros((len(ages), ensemble_count), dtype=bool)
            for cell in core:
                arr = cell_support[j].get(cell)
                if arr is not None:
                    occ |= arr
            frac = np.mean(occ, axis=1)
            supported = frac > 0
            fam['oldest_supported_age_ma'] = float(np.max(ages[supported])) if np.any(supported) else None
            fam['youngest_supported_age_ma'] = float(np.min(ages[supported])) if np.any(supported) else None
            fam['supported_age_state_fraction'] = float(np.mean(supported))
            fam['full_ensemble_supported_age_state_fraction'] = float(np.mean(frac >= 1.0 - 1e-12))
            fam['ensemble_occupancy_fraction_by_age_q05'] = float(np.quantile(frac, .05))
            fam['ensemble_occupancy_fraction_by_age_q50'] = float(np.quantile(frac, .50))
            fam['ensemble_occupancy_fraction_by_age_q95'] = float(np.quantile(frac, .95))
            fam['ensemble_occupancy_fraction_by_age_max'] = float(np.max(frac))
            fam['longest_contiguous_supported_state_count'] = int(_longest_true_run(supported))
            fam['longest_contiguous_supported_sample_span_kyr'] = float(max(0, _longest_true_run(supported)-1) * 20.0)
            family_occ_rows.append(frac.astype(np.float32))
            family_core_masks[fam['family_id']] = set(core)
            all_families.append(fam)
        per_candidate[sid] = {
            'family_count': len(fams),
            'all_threshold_family_count': sum(bool(f['survives_all_thresholds']) for f in fams),
            'three_plus_threshold_family_count': sum(int(f['threshold_coverage_count']) >= 3 for f in fams),
            'q99_survivor_count': sum(float(f['highest_threshold_quantile']) >= .99 - 1e-12 for f in fams),
        }

    robust = [f for f in all_families if f['survives_all_thresholds']]
    overlap_pairs = []
    a = [f for f in robust if f['candidate_id'] == ids[0]]
    b = [f for f in robust if f['candidate_id'] == ids[1]]
    for fa in a:
        ma = family_core_masks[fa['family_id']]
        for fb in b:
            mb = family_core_masks[fb['family_id']]
            inter = len(ma & mb); union = len(ma | mb)
            if inter:
                overlap_pairs.append({
                    'family_a': fa['family_id'], 'family_b': fb['family_id'],
                    'intersection_cell_count': inter,
                    'union_cell_count': union,
                    'jaccard': float(inter / union) if union else 0.0,
                })
    overlap_pairs.sort(key=lambda x: (-x['jaccard'], x['family_a'], x['family_b']))

    decision = adjudicate_engine_use(per_candidate, ids)

    pareto_count = sum(bool(r.get('pareto_nondominated')) for r in regions)
    structure = {
        'stage': STAGE,
        'status': 'PASS_R51_CRADLE_STRUCTURE_AND_ENGINE_ADJUDICATION',
        'semantics': 'THRESHOLD_NESTED_REGION_FAMILIES_AND_TEMPORAL_SUPPORT_NO_WEIGHTED_SCORE_NO_SINGLE_WINNER',
        'candidate_output_integrity': integrity,
        'registry_reconstruction_exact': True,
        'registry_reconstruction_details': registry_details,
        'region_record_count': len(regions),
        'pareto_region_record_count': pareto_count,
        'pareto_front_is_final_selection': False,
        'candidate_ids': list(ids),
        'family_count': len(all_families),
        'all_threshold_family_count': len(robust),
        'per_candidate': per_candidate,
        'cross_lineage_all_threshold_core_overlap': {
            'nonzero_overlap_pair_count': len(overlap_pairs),
            'max_jaccard': float(overlap_pairs[0]['jaccard']) if overlap_pairs else 0.0,
            'pairs': overlap_pairs,
        },
        'closure_readiness': decision['closure_readiness'],
        'engine_adjudication': decision['engine_adjudication'],
        'recommended_next_action': decision['recommended_next_action'],
        'canonical_state_changed': False,
        'derived_refinement_promoted_to_canon': False,
        'deep_biological_coupling': False,
    }
    occ = np.stack(family_occ_rows, axis=0) if family_occ_rows else np.zeros((0, len(ages)), np.float32)
    family_ids = np.asarray([f['family_id'] for f in all_families])
    return {'structure': structure, 'families': all_families, 'age_ma': ages, 'family_ids': family_ids, 'occupancy': occ}


def save_structure_outputs(root: Path, result: dict[str, Any]) -> dict[str, Any]:
    out = Path(root) / OUT_REL
    structure_path = out / 'R5_1_CRADLE_STRUCTURE_AND_ENGINE_ADJUDICATION.json'
    families_path = out / 'R5_1_ROBUST_REGION_FAMILIES.json'
    temporal_path = out / 'R5_1_REGION_FAMILY_TEMPORAL_SUPPORT.npz'
    _write_json(structure_path, result['structure'])
    _write_json(families_path, {
        'stage': STAGE,
        'status': 'R51_THRESHOLD_NESTED_REGION_FAMILY_REGISTRY',
        'semantics': 'FAMILIES_TRACK_CONNECTED_COMPONENT_DESCENDANTS_ACROSS_FIXED_90_95_97P5_99_PERCENTILE_THRESHOLDS',
        'families': result['families'],
    })
    np.savez_compressed(temporal_path, age_ma=result['age_ma'], family_ids=result['family_ids'], ensemble_occupancy_fraction_by_age=result['occupancy'])
    files = {}
    for p in (structure_path, families_path, temporal_path):
        files[p.name] = {'bytes': p.stat().st_size, 'sha256': _sha256(p)}
    manifest_path = out / 'R5_1_STRUCTURE_ADJUDICATION_MANIFEST.json'
    _write_json(manifest_path, {'stage': STAGE, 'status': result['structure']['status'], 'files': files})
    files[manifest_path.name] = {'bytes': manifest_path.stat().st_size, 'sha256': _sha256(manifest_path)}
    return {'files': files, 'manifest_sha256': _sha256(manifest_path)}
