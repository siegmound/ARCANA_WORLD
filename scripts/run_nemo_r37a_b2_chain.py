from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))

from arcana_worldsim.scientific_engines.nemo_benchmarks import canonical_r36b_scenarios
from arcana_worldsim.scientific_engines.nemo_qtl_ensemble import NemoQTLArchitectureSpec, build_qtl_realization, write_qtl_realization
from arcana_worldsim.scientific_engines.nemo242_r36d import parse_qfreq
from arcana_worldsim.scientific_engines.nemo242_r37a import (
    canonical_r37a_b2_phases, render_r37a_b2_phase_ini,
    b2_reduced_order_deterministic_trajectory,
)
from arcana_worldsim.scientific_engines.segregation_aware_admixture import qtl_segregation_potential


def windows_to_wsl(path: Path) -> str:
    s=str(path.resolve())
    if len(s)>=3 and s[1]==':' and s[2] in ('\\','/'):
        drive=s[0].lower(); rest=s[3:].replace('\\','/')
        return f'/mnt/{drive}/{rest}'
    # Allow execution from WSL/Linux too.
    return s.replace('\\','/')


def semhash(obj) -> str:
    return sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def _one_chain(*, N:int, rep:int, axis:int, base_seed:int, loci:int, outroot:Path, conda_env:str) -> dict:
    b2=canonical_r36b_scenarios(n_individuals=N)[2]
    qspec=NemoQTLArchitectureSpec(loci_per_trait=loci,individual_sample_size=N)
    gseed=base_seed + N*1000 + rep*100 + 37
    realization=build_qtl_realization(
        b2.normalized_trait_means,b2.normalized_additive_variance,
        trait_axes=(0,1),seed=gseed,spec=qspec,individuals_per_patch=b2.population_individuals,
    )
    chain_id=f'N{N}_r{rep:03d}_a{axis}'
    root=outroot/f'N_{N}'/f'rep_{rep:03d}'/f'axis_{axis}'
    root.mkdir(parents=True,exist_ok=True)
    write_qtl_realization(realization,root/'qtl',[f'P{i:03d}' for i in range(len(b2.population_individuals))])
    effects=np.asarray(realization.effect_sizes[axis],float)
    freq=np.asarray(realization.allele_frequencies[:,axis,:],float).copy()
    initial_s=qtl_segregation_potential(effects[None,:],freq[:,None,:])
    deterministic=b2_reduced_order_deterministic_trajectory(initial_s)
    phase_records=[]
    for pi,phase in enumerate(canonical_r37a_b2_phases()):
        proot=root/f'phase_{pi:02d}_{phase.name}'
        seed=base_seed + 50_000_000 + N*1000 + rep*100 + axis*10 + pi
        manifest=render_r37a_b2_phase_ini(
            phase=phase,effect_a=effects,allele_frequencies=freq,population_size=N,
            seed=seed,output_dir=proot,chain_id=chain_id,
        )
        wdir=windows_to_wsl(proot)
        ini='Nemo2_ARCANA_R37A_B2.ini'
        cmd=(
            'export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1; '
            f'cd {shlex.quote(wdir)} && conda run -n {shlex.quote(conda_env)} nemo2.4.2 {shlex.quote(ini)}'
        )
        cp=subprocess.run(['wsl','bash','-lc',cmd],text=True,capture_output=True,check=False)
        (proot/'engine.stdout.txt').write_text(cp.stdout,encoding='utf-8',errors='replace')
        (proot/'engine.stderr.txt').write_text(cp.stderr,encoding='utf-8',errors='replace')
        (proot/'engine.returncode.txt').write_text(str(cp.returncode)+'\n',encoding='ascii')
        qfreqs=sorted(proot.glob('*.qfreq'))
        if cp.returncode!=0 or len(qfreqs)!=1:
            return {
                'chain_id':chain_id,'population_size':N,'replicate':rep,'axis':axis,
                'status':'ENGINE_FAILED_OR_QFREQ_MISSING','failed_phase':phase.name,
                'returncode':cp.returncode,'qfreq_count':len(qfreqs),
            }
        parsed=parse_qfreq(qfreqs[0],arcana_effect_a=effects)
        freq=np.asarray(parsed['allele_frequencies'][-1],float)
        s=qtl_segregation_potential(effects[None,:],freq[:,None,:])[:,:,0]
        phase_records.append({
            'phase':phase.name,'transitions':phase.transitions,'returncode':cp.returncode,
            'final_mean_va':float(np.mean(parsed['additive_variance'][-1])),
            'final_max_va':float(np.max(parsed['additive_variance'][-1])),
            'final_trait_spread':float(np.ptp(parsed['trait_mean'][-1])),
            'final_mean_pair_S':float(np.mean(s[np.triu_indices(s.shape[0],1)])),
            'final_max_S':float(np.max(s)),
            'qfreq_file':qfreqs[0].name,
            'binding_manifest_sha256':semhash(manifest),
        })
    summary={
        'schema':'ARCANA_R37A_NEMO_B2_CHAIN_RESULT_V1','stage':'v0.6D1-R3.7A',
        'chain_id':chain_id,'population_size':N,'replicate':rep,'axis':axis,
        'status':'ENGINE_COMPLETED_B2_CHAIN','genetic_seed':gseed,
        'loci_per_trait':loci,'phases':phase_records,
        'reduced_order_migration_only_reference':deterministic,
        'phase_boundary_semantics':'QFREQ_FREQUENCY_STATE_CHAIN__LD_AND_GENOTYPE_PHASE_STATE_NOT_PRESERVED',
        'canonical_write_allowed':False,'automatic_calibration_allowed':False,
    }
    (root/'R3_7A_B2_CHAIN_SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return summary


def main() -> int:
    ap=argparse.ArgumentParser(description='Run R3.7A NEMO 2.4.2 B2 connected-fragmented-reconnected frequency-state chains through WSL.')
    ap.add_argument('outdir',type=Path)
    ap.add_argument('--replicates',type=int,default=2)
    ap.add_argument('--population-sizes',type=int,nargs='+',default=[500,2000])
    ap.add_argument('--loci-per-trait',type=int,default=64)
    ap.add_argument('--seed',type=int,default=37102026)
    ap.add_argument('--parallel-chains',type=int,default=4)
    ap.add_argument('--conda-env',default='arcana-nemo242')
    args=ap.parse_args()
    if args.replicates<1 or args.loci_per_trait<4 or args.parallel_chains<1 or any(n<20 for n in args.population_sizes):
        raise ValueError('invalid suite dimensions')
    root=args.outdir.resolve(); root.mkdir(parents=True,exist_ok=True)
    jobs=[(N,r,a) for N in args.population_sizes for r in range(args.replicates) for a in (0,1)]
    print(json.dumps({'stage':'v0.6D1-R3.7A','status':'STARTING_NEMO_B2_CHAIN_SUITE','chain_count':len(jobs),'population_sizes':args.population_sizes,'replicates':args.replicates},indent=2))
    records=[]
    with ThreadPoolExecutor(max_workers=args.parallel_chains) as ex:
        fut={ex.submit(_one_chain,N=N,rep=r,axis=a,base_seed=args.seed,loci=args.loci_per_trait,outroot=root,conda_env=args.conda_env):(N,r,a) for N,r,a in jobs}
        for f in as_completed(fut):
            rec=f.result(); records.append(rec); print(f"[R3.7A] {rec['chain_id']} {rec['status']}")
    records.sort(key=lambda x:(x['population_size'],x['replicate'],x['axis']))
    complete=sum(r.get('status')=='ENGINE_COMPLETED_B2_CHAIN' for r in records)
    summary={
        'schema':'ARCANA_R37A_NEMO_B2_SUITE_V1','stage':'v0.6D1-R3.7A',
        'status':'NEMO_B2_EVIDENCE_COMPLETE_REVIEW_REQUIRED' if complete==len(records) else 'PARTIAL_NEMO_B2_EVIDENCE',
        'chain_count':len(records),'complete_chain_count':complete,'records':records,
        'canonical_write_allowed':False,'production_binding_authorized':False,
    }
    (root/'R3_7A_NEMO_B2_SUITE_SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ('stage','status','chain_count','complete_chain_count')},indent=2))
    return 0 if complete==len(records) else 2

if __name__=='__main__':
    raise SystemExit(main())
