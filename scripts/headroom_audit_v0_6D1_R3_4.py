from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import d3_additive_variance_v0_6_3D3_3A as av
import rebased_natural_control_runtime_v0_6D1_R3_4 as r34

REF = ROOT / 'references/v0_6D1_R3_4/R3_3_150Ma_HEADROOM_REFERENCE.npz'
META = ROOT / 'references/D1_species_metadata.json'
OUT = ROOT / 'outputs/v0_6D1_R3_4/HEADROOM_AUDIT_v0_6D1_R3_4.json'


def _metadata():
    rows = json.loads(META.read_text())
    if isinstance(rows, dict) and 'species' in rows:
        rows = rows['species']
    return {r['species_id']: r for r in rows}


def _run_frozen(ref, md, ceiling: float, years: float):
    trait = ref['trait'].astype(float).copy()
    va = ref['va'].astype(float).copy()
    pop = ref['population_total'].astype(float)
    gen = ref['generation_time'].astype(float)
    ri = ref['ri'].astype(float)
    contact = ref['contact'].astype(float)
    root = ref['component_root_species'].astype(str).tolist()
    current = ref['component_species'].astype(str).tolist()
    root_idx, root_ids = r34._root_index(root)
    same_current = np.equal.outer(np.asarray(current), np.asarray(current))
    G = float(r34.R34Config().gene_flow_ceiling_per_step) * contact * same_current
    cfg = r34._variance_cfg_d3_3a(r34.R34Config(variance_ceiling_normalized=float(ceiling)))
    dt = float(r34.R34Config().biology_cadence_years)
    n = int(round(float(years) / dt))
    last_diag = None
    for _ in range(n):
        before = trait.copy()
        trait, va, last_diag = av.gene_flow_moment_mix(trait, va, pop, G, ri, root_idx, cfg)
        # Frozen-environment headroom audit: zero new directional selection.
        va, _ = av.advance_nonflow_variance(
            va, before, before, pop, gen, root_idx, root_ids, md,
            float(r34.R34Config().body_mass_scale), dt, cfg,
        )
    q = av.normalized_variance_matrix(
        va, root_idx, root_ids, md, float(r34.R34Config().body_mass_scale)
    )
    return {
        'ceiling': float(ceiling),
        'years': float(years),
        'max_q': float(np.max(q)),
        'median_q': float(np.median(q)),
        'p95_q': float(np.quantile(q, .95)),
        'p99_q': float(np.quantile(q, .99)),
        'fraction_ge_99pct_ceiling': float(np.mean(q >= 0.99 * ceiling)),
        'fraction_ge_0p0495': float(np.mean(q >= 0.0495)),
        'edge_count_last_step': int(last_diag['edge_count']) if last_diag else 0,
        'exchange_mass_last_step': float(last_diag['total_pair_exchange_mass']) if last_diag else 0.0,
    }


def main():
    ref = np.load(REF, allow_pickle=False)
    md = _metadata()
    root = ref['component_root_species'].astype(str)
    cur = ref['component_species'].astype(str)
    contact = ref['contact'].astype(float)
    same_root = np.equal.outer(root, root)
    same_cur = np.equal.outer(cur, cur)
    illegal = np.triu(same_root & (~same_cur) & (contact > 0), 1)

    experiments = [
        _run_frozen(ref, md, .05, 1_000_000),
        _run_frozen(ref, md, .06, 5_000_000),
        _run_frozen(ref, md, .075, 20_000_000),
        _run_frozen(ref, md, .08, 20_000_000),
        _run_frozen(ref, md, .10, 20_000_000),
    ]
    by = {str(x['ceiling']): x for x in experiments}
    verdict = (
        'PASS_HEADROOM_SUPPORTS_0P08_NONBINDING_SAFETY_CEILING_CANDIDATE'
        if by['0.08']['fraction_ge_99pct_ceiling'] == 0.0
        and abs(by['0.08']['max_q'] - by['0.1']['max_q']) < 1e-12
        and by['0.075']['fraction_ge_99pct_ceiling'] > 0.0
        else 'FAIL_HEADROOM_CALIBRATION'
    )
    out = {
        'stage': 'v0.6D1-R3.4',
        'scope': 'LONG_HORIZON_ADMIXTURE_VARIANCE_HEADROOM_AND_SPECIES_BOUND_GENE_FLOW',
        'verdict': verdict,
        'semantic_identity_audit': {
            'cross_current_species_contact_edges_within_same_root': int(np.count_nonzero(illegal)),
            'max_cross_current_species_contact': float(np.max(contact[illegal])) if np.any(illegal) else 0.0,
            'sum_cross_current_species_contact': float(np.sum(contact[illegal])) if np.any(illegal) else 0.0,
            'required_semantics': 'GENE_FLOW_AND_PAIR_STATE_ARE_CURRENT_SPECIES_BOUND; ROOT_SPECIES_IS_PROVENANCE_ONLY',
        },
        'homeostasis_authority_unchanged': {
            'mutation_variance_supply_normalized_per_myr': 0.002,
            'nonlinear_stabilizing_variance_depletion_per_myr_per_q': 0.9876543209876544,
            'no_flow_equilibrium_q': 0.045,
        },
        'experiments': experiments,
        'calibration_decision': {
            'selected_candidate_ceiling': 0.08,
            'reason': '0.075 still contacts 99% of the ceiling in the 20 Myr frozen-admixture audit, while 0.08 and 0.10 yield the same natural maximum q and 0% >=99% ceiling. Raising the safety ceiling leaves mu, b, and q*=0.045 unchanged.',
            'b_recalibration_required': False,
        },
        'limitations': [
            'Frozen 150 Ma demographic/contact geometry is a diagnostic equilibrium probe, not a historical rerun.',
            'The 210->150 Ma production replay must be rerun with R3.4 before 150 Ma can be promoted.',
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    main()
