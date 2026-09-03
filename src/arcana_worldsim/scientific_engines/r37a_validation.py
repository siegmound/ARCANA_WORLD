from __future__ import annotations

from pathlib import Path
import io
import json
import zipfile
from typing import Any

import numpy as np

from .segregation_aware_admixture import qtl_segregation_potential


def _read_qfreq_final_from_zip(zf: zipfile.ZipFile, prefix: str, effects: np.ndarray) -> np.ndarray:
    names = [n for n in zf.namelist() if n.startswith(prefix) and n.endswith('.qfreq')]
    if len(names) != 1:
        raise ValueError(f"expected one qfreq under {prefix}, got {len(names)}")
    lines = [x.strip() for x in zf.read(names[0]).decode('utf-8').splitlines() if x.strip()]
    header = lines[0].split()
    if header[:4] != ['pop','trait','locus','allele']:
        raise ValueError('unexpected qfreq header')
    pops = sorted({int(line.split()[0]) for line in lines[1:]})
    freq = np.full((len(pops), len(effects)), np.nan, dtype=float)
    pindex = {p:i for i,p in enumerate(pops)}
    for line in lines[1:]:
        tok=line.split(); pop=int(tok[0]); locus=int(tok[2])-1
        freq[pindex[pop], locus]=float(tok[-1])
    if np.any(~np.isfinite(freq)):
        raise ValueError('incomplete qfreq')
    return freq


def analyze_r37a_parent_reference(raw_results_zip: str | Path) -> dict[str, Any]:
    """Use the already-real R3.6D NEMO runs to validate drift and K_eff scale.

    B0 supplies an independent no-flow drift oracle. B1/C3 initial QTL states
    provide the reference effective participation number K_eff = dz^2/(2 S)
    for the same 64-locus architecture used to diagnose R3.6E.
    """
    raw = Path(raw_results_zip)
    drift_rows=[]; k_rows=[]
    with zipfile.ZipFile(raw) as zf:
        for name in zf.namelist():
            if not name.endswith('/R3_6D_JOB.json'):
                continue
            job=json.loads(zf.read(name))
            jobdir=name.rsplit('/',1)[0]+'/'
            axis=int(job['axis'])
            effects=np.asarray(job['effect_a'],float)
            if job.get('scenario')=='B0_EQUILIBRIUM_NO_FLOW':
                freq=_read_qfreq_final_from_zip(zf,jobdir,effects)
                s=qtl_segregation_potential(effects[None,:],freq[:,None,:])[:,:,0]
                if s.shape[0] != 2:
                    raise ValueError('B0 drift oracle expects two patches')
                N=float(job['population_size'])
                # R3.6D uses 125 kyr / 5 yr = 25,000 Wright-Fisher generations.
                generations=25000.0
                v0=float(np.mean(np.asarray(job['target_va'],float)))
                retain=float(np.exp(-generations/(2.0*N)))
                predicted=2.0*v0*(1.0-retain)
                observed=float(s[0,1])
                drift_rows.append({
                    'population_size':int(N),'replicate':int(job['replicate']),'axis':axis,
                    'observed_final_S':observed,'d3_3a_drift_transfer_prediction':predicted,
                    'observed_over_prediction':observed/max(predicted,1e-300),
                })
            elif job.get('variant')=='FLOW' and int(job['replicate'])==0 and int(job['population_size'])==2000:
                variant_dir=jobdir.rsplit('axis_',1)[0]
                with np.load(io.BytesIO(zf.read(variant_dir+'qtl/qtl_expected_state.npz'))) as data:
                    all_eff=np.asarray(data['effect_sizes'],float)
                    all_freq=np.asarray(data['allele_frequencies'],float)
                    means=np.asarray(data['expected_means'],float)
                s=qtl_segregation_potential(all_eff[axis:axis+1],all_freq[:,axis:axis+1,:])[:,:,0]
                for i in range(s.shape[0]):
                    for j in range(i+1,s.shape[0]):
                        dz=float(means[i,axis]-means[j,axis])
                        if s[i,j] <= 1e-14 or abs(dz) <= 1e-14:
                            continue
                        keff=dz*dz/(2.0*float(s[i,j]))
                        k_rows.append({
                            'scenario':job['pair'],'axis':axis,'i':i,'j':j,
                            'delta_trait_mean':dz,'S':float(s[i,j]),
                            'effective_polygenic_participation':keff,
                        })
    if not drift_rows or not k_rows:
        raise ValueError('required R3.6D references not found')
    ratios=np.asarray([x['observed_over_prediction'] for x in drift_rows],float)
    kvals=np.asarray([x['effective_polygenic_participation'] for x in k_rows],float)
    verdict=(
        'PASS_PARENT_NEMO_DRIFT_REFERENCE_AND_POLYGENIC_SCALE_FOUNDATION'
        if np.max(np.abs(ratios-1.0)) < 0.30 and np.min(kvals)>1.0
        else 'REVIEW_PARENT_REFERENCE_MISMATCH'
    )
    return {
        'schema':'ARCANA_R37A_PARENT_REFERENCE_VALIDATION_V1',
        'stage':'v0.6D1-R3.7A',
        'verdict':verdict,
        'drift_reference':{
            'row_count':len(drift_rows),
            'median_observed_over_prediction':float(np.median(ratios)),
            'mean_observed_over_prediction':float(np.mean(ratios)),
            'max_abs_fractional_deviation':float(np.max(np.abs(ratios-1.0))),
            'rows':drift_rows,
            'interpretation':'D3.3A drift-loss transfer predicts NEMO no-flow segregation divergence within finite-N stochastic scatter.',
        },
        'polygenic_participation_reference':{
            'row_count':len(k_rows),
            'minimum':float(np.min(kvals)),
            'median':float(np.median(kvals)),
            'maximum':float(np.max(kvals)),
            'literal_qtl_loci':64,
            'rows':k_rows,
            'interpretation':'K_eff is a participation number, not automatically identical to the literal locus count.',
        },
        'canonical_write_allowed':False,
        'production_selection_mapping_authorized':False,
    }
