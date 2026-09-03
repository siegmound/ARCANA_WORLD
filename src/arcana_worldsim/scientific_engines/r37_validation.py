from __future__ import annotations

import io
import json
from pathlib import Path
import zipfile
from typing import Any

import numpy as np

from .segregation_aware_admixture import (
    SegregationAwareAdmixtureConfig,
    qtl_segregation_potential,
    segregation_aware_gene_flow_mix,
)


def _read_json(zf: zipfile.ZipFile, name: str) -> dict[str, Any]:
    return json.loads(zf.read(name))


def _job_paths(zf: zipfile.ZipFile) -> list[str]:
    return sorted(n for n in zf.namelist() if n.endswith('/R3_6D_JOB.json'))


def _r36e_lookup(r36e: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    rows = {}
    for r in r36e['three_way_causal_comparison']:
        # ARCANA/analytic values are identical across N; keep one row per pair/axis.
        rows.setdefault((str(r['pair']), int(r['axis'])), r)
    return rows


def analyze_r37_reference_closure(
    raw_results_zip: str | Path,
    r36e_json: str | Path,
    *,
    recombination_fraction_per_generation: float = 0.5,
) -> dict[str, Any]:
    """Validate the R3.7 reduced-order operator against R3.6D/E evidence.

    The operator is evaluated only on the controlled QTL reference where the
    pairwise segregation potential is observable exactly.  This authorizes the
    operator decomposition, NOT its production initialization/evolution in the
    210->150 Ma replay.
    """
    raw_results_zip = Path(raw_results_zip)
    r36e = json.loads(Path(r36e_json).read_text(encoding='utf-8'))
    if r36e.get('verdict','').startswith('STRUCTURAL_ADMIXTURE_OPERATOR_MISMATCH_SUPPORTED') is False:
        raise ValueError('R3.7 requires the R3.6E structural mismatch verdict')
    lookup = _r36e_lookup(r36e)
    cfg = SegregationAwareAdmixtureConfig(
        recombination_fraction_per_generation=float(recombination_fraction_per_generation)
    )

    closure_rows = []
    with zipfile.ZipFile(raw_results_zip) as zf:
        # One deterministic QTL realization per scenario/axis is sufficient for
        # analytic closure; use N=2000, replicate 0 as the reference copy.
        selected=[]
        for jp in _job_paths(zf):
            job=_read_json(zf,jp)
            if (job.get('variant')=='FLOW' and int(job['population_size'])==2000
                    and int(job['replicate'])==0):
                selected.append((jp,job))
        if len(selected)!=4:
            raise ValueError(f'expected B1/C3 x 2 axes reference jobs, found {len(selected)}')

        for job_path,job in selected:
            pair=str(job['pair']); axis=int(job['axis'])
            job_dir=job_path.rsplit('/',1)[0]+'/'
            variant_dir=job_dir.rsplit('axis_',1)[0]
            with np.load(io.BytesIO(zf.read(variant_dir+'qtl/qtl_expected_state.npz'))) as data:
                effects=np.asarray(data['effect_sizes'],float)
                freqs=np.asarray(data['allele_frequencies'],float)
                expected_va=np.asarray(data['expected_variances'],float)
                expected_means=np.asarray(data['expected_means'],float)
            pergen=np.loadtxt(io.StringIO(zf.read(job_dir+'nemo_per_generation_dispersal.tsv').decode('utf-8')))
            manifest=_read_json(zf,job_dir+'R3_6D_NEMO_BINDING_MANIFEST.json')
            transitions=int(manifest['nemo_transitions'])
            interval=np.linalg.matrix_power(pergen,transitions)
            g=interval.copy(); np.fill_diagonal(g,0.0)

            z=expected_means[:,axis:axis+1]
            va=expected_va[:,axis:axis+1]
            s=qtl_segregation_potential(effects[axis:axis+1],freqs[:,axis:axis+1,:])
            n=np.full(z.shape[0],2000.0)
            z2,v2,c2,s2,diag=segregation_aware_gene_flow_mix(
                z,va,np.zeros_like(va),s,n,g,np.zeros_like(g),np.zeros(z.shape[0],dtype=int),
                np.full(z.shape[0],5.0),125000.0,cfg,
            )
            pm=interval@freqs[:,axis,:]
            direct_va=2.0*np.sum((effects[axis][None,:]**2)*pm*(1.0-pm),axis=1)
            analytic_delta=float(np.mean(direct_va-va[:,0]))
            r36=lookup[(pair,axis)]
            documented_analytic=float(r36['analytic_polygenic_delta_va'])
            legacy_delta=float(r36['arcana_admixture_only_1x125k_delta_va'])
            repaired_delta=float(np.mean(v2[:,0]-va[:,0]))
            pre_anc=np.asarray(diag['ancestry_abs_before_recombination_total'],float)
            post_anc=np.asarray(diag['ancestry_abs_after_recombination_total'],float)
            closure_rows.append({
                'pair':pair,'axis':axis,'loci':int(effects.shape[1]),
                'analytic_polygenic_delta_va_recomputed':analytic_delta,
                'analytic_polygenic_delta_va_r36e':documented_analytic,
                'r37_repaired_delta_va':repaired_delta,
                'r37_over_analytic':repaired_delta/documented_analytic,
                'legacy_arcana_delta_va':legacy_delta,
                'legacy_over_r37':legacy_delta/repaired_delta,
                'nemo_over_analytic_min':float(min(x['nemo_over_analytic'] for x in r36e['three_way_causal_comparison'] if x['pair']==pair and int(x['axis'])==axis)),
                'nemo_over_analytic_max':float(max(x['nemo_over_analytic'] for x in r36e['three_way_causal_comparison'] if x['pair']==pair and int(x['axis'])==axis)),
                'ancestry_abs_pre_recombination':float(pre_anc[0]),
                'ancestry_abs_post_recombination':float(post_anc[0]),
                'ancestry_post_over_pre':float(post_anc[0]/pre_anc[0]) if pre_anc[0]>0 else 0.0,
                'first_moment_conservation_max_abs':float(diag['first_moment_conservation_max_abs']),
                'pre_recombination_total_variance_closure_max_abs':float(diag['pre_recombination_total_variance_closure_max_abs']),
                'segregation_potential_initial_mean':float(np.mean(s)),
                'segregation_potential_final_mean':float(np.mean(s2)),
            })

    relerr=[abs(x['r37_over_analytic']-1.0) for x in closure_rows]
    legacy_factor=[x['legacy_over_r37'] for x in closure_rows]
    ancestry_ret=[x['ancestry_post_over_pre'] for x in closure_rows]
    closure=[x['pre_recombination_total_variance_closure_max_abs'] for x in closure_rows]
    first=[x['first_moment_conservation_max_abs'] for x in closure_rows]
    reference_closure=(
        max(relerr)<1e-8
        and min(legacy_factor)>100.0
        and max(ancestry_ret)<1e-3
        and max(closure)<1e-10
        and max(first)<1e-10
    )
    verdict=(
        'PASS_SEGREGATION_AWARE_OPERATOR_REFERENCE_CLOSURE__PRODUCTION_STATE_EVOLUTION_PENDING'
        if reference_closure else
        'FAIL_SEGREGATION_AWARE_OPERATOR_REFERENCE_CLOSURE'
    )
    return {
        'schema':'ARCANA_R37_SEGREGATION_AWARE_REFERENCE_CLOSURE_V1',
        'stage':'v0.6D1-R3.7',
        'source_r36e_verdict':r36e['verdict'],
        'operator_reference_rows':closure_rows,
        'max_relative_error_vs_analytic':float(max(relerr)),
        'minimum_legacy_over_repaired_factor':float(min(legacy_factor)),
        'maximum_ancestry_post_over_pre':float(max(ancestry_ret)),
        'verdict':verdict,
        'canonical_write_allowed':False,
        'production_runtime_binding_allowed':False,
        'mu_b_change_authorized':False,
        'ceiling_change_authorized':False,
        'state_initialization_authorized':False,
        'state_evolution_authorized':False,
        'next_required_stage':'R3.7A segregation-potential initialization/evolution and fission/coalescence/speciation lifecycle calibration before short World-1 replay binding',
    }
