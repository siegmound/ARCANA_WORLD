from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
import json
from pathlib import Path
import shlex
import subprocess
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))

from arcana_worldsim.scientific_engines.nemo_qtl_ensemble import NemoQTLArchitectureSpec, build_qtl_realization, write_qtl_realization
from arcana_worldsim.scientific_engines.nemo242_r36d import parse_qfreq
from arcana_worldsim.scientific_engines.nemo242_r37c import (
    R37CSelectionProtocol, r37c_exchange_matrix, render_r37c_phase_ini,
)


def windows_to_wsl(path: Path) -> str:
    s=str(path.resolve())
    if len(s)>=3 and s[1]==':' and s[2] in ('\\','/'):
        return f'/mnt/{s[0].lower()}/{s[3:].replace(chr(92),"/")}'
    return s.replace('\\','/')


def semhash(obj) -> str:
    return sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def _run_phase(*, root:Path, phase:str, transitions:int, effects:np.ndarray, freq:np.ndarray,
               N:int, seed:int, chain_id:str, conda_env:str, selection_enabled:bool,
               selection_variance:float|None, optimum_amplitude:float, exchange:np.ndarray) -> tuple[dict,np.ndarray,str]:
    manifest=render_r37c_phase_ini(
        phase=phase,transitions=transitions,effect_a=effects,allele_frequencies=freq,
        population_size=N,seed=seed,output_dir=root,chain_id=chain_id,
        selection_enabled=selection_enabled,selection_variance=selection_variance,
        optimum_amplitude=optimum_amplitude,exchange_matrix=exchange,
    )
    wdir=windows_to_wsl(root)
    cmd=('export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1; '
         f'cd {shlex.quote(wdir)} && conda run -n {shlex.quote(conda_env)} nemo2.4.2 Nemo2_ARCANA_R37C.ini')
    cp=subprocess.run(['wsl','bash','-lc',cmd],text=True,capture_output=True,check=False)
    (root/'engine.stdout.txt').write_text(cp.stdout,encoding='utf-8',errors='replace')
    (root/'engine.stderr.txt').write_text(cp.stderr,encoding='utf-8',errors='replace')
    (root/'engine.returncode.txt').write_text(str(cp.returncode)+'\n',encoding='ascii')
    qfreqs=sorted(root.glob('*.qfreq'))
    if cp.returncode!=0 or len(qfreqs)!=1:
        raise RuntimeError(f'{chain_id} {phase}: NEMO rc={cp.returncode}, qfreq_count={len(qfreqs)}')
    parsed=parse_qfreq(qfreqs[0],arcana_effect_a=effects)
    ff=np.asarray(parsed['allele_frequencies'][-1],float)
    record={
        'phase':phase,'transitions':int(transitions),'returncode':cp.returncode,
        'final_trait_mean':np.asarray(parsed['trait_mean'][-1],float).tolist(),
        'final_additive_variance':np.asarray(parsed['additive_variance'][-1],float).tolist(),
        'qfreq_file':qfreqs[0].name,
        'qfreq_relpath':str(qfreqs[0].relative_to(root.parents[2])).replace('\\','/'),
        'binding_manifest_sha256':semhash(manifest),
    }
    return record,ff,qfreqs[0].name


def _one_chain(*, N:int,rep:int,axis:int,selection_variance:float,base_seed:int,loci:int,outroot:Path,conda_env:str,protocol:R37CSelectionProtocol) -> dict:
    means=np.zeros((4,2),float); va=np.full((4,2),0.045,float); pops=np.full(4,N,int)
    gseed=base_seed + N*1000 + rep*100 + axis*10
    qspec=NemoQTLArchitectureSpec(loci_per_trait=loci,individual_sample_size=N)
    realization=build_qtl_realization(means,va,trait_axes=(0,1),seed=gseed,spec=qspec,individuals_per_patch=pops)
    effects=np.asarray(realization.effect_sizes[axis],float)
    freq0=np.asarray(realization.allele_frequencies[:,axis,:],float).copy()
    chain_id=f'N{N}_r{rep:03d}_a{axis}_sv{selection_variance:g}'
    root=outroot/f'selection_variance_{selection_variance:g}'/f'N_{N}'/f'rep_{rep:03d}'/f'axis_{axis}'
    root.mkdir(parents=True,exist_ok=True)
    write_qtl_realization(realization,root/'qtl',[f'P{i:03d}' for i in range(4)])

    burn_root=root/'phase_00_COMMON_BURNIN'
    burn_seed=base_seed+10_000_000+N*1000+rep*100+axis*10
    burn,fork_freq,_=_run_phase(root=burn_root,phase='COMMON_BURNIN',transitions=protocol.burnin_transitions,
        effects=effects,freq=freq0,N=N,seed=burn_seed,chain_id=chain_id,conda_env=conda_env,
        selection_enabled=False,selection_variance=None,optimum_amplitude=protocol.optimum_amplitude,
        exchange=r37c_exchange_matrix('COMMON_BURNIN',protocol))

    branch_seed=base_seed+20_000_000+N*1000+rep*100+axis*10
    sel_root=root/'selected'/'phase_01_FRAGMENTED_DIVERGENT_SELECTION'
    ctl_root=root/'neutral'/'phase_01_FRAGMENTED_MATCHED_NEUTRAL'
    sel_frag,sel_freq,_=_run_phase(root=sel_root,phase='FRAGMENTED_DIVERGENT_SELECTION',transitions=protocol.selected_transitions,
        effects=effects,freq=fork_freq,N=N,seed=branch_seed,chain_id=chain_id+'_SEL',conda_env=conda_env,
        selection_enabled=True,selection_variance=selection_variance,optimum_amplitude=protocol.optimum_amplitude,
        exchange=r37c_exchange_matrix('FRAGMENTED_DIVERGENT_SELECTION',protocol))
    ctl_frag,ctl_freq,_=_run_phase(root=ctl_root,phase='FRAGMENTED_MATCHED_NEUTRAL',transitions=protocol.selected_transitions,
        effects=effects,freq=fork_freq,N=N,seed=branch_seed,chain_id=chain_id+'_CTL',conda_env=conda_env,
        selection_enabled=False,selection_variance=None,optimum_amplitude=protocol.optimum_amplitude,
        exchange=r37c_exchange_matrix('FRAGMENTED_MATCHED_NEUTRAL',protocol))

    reconn_seed=base_seed+30_000_000+N*1000+rep*100+axis*10
    sel_rec_root=root/'selected'/'phase_02_RECONNECTED_RELAXED'
    ctl_rec_root=root/'neutral'/'phase_02_RECONNECTED_RELAXED'
    sel_rec,_,_=_run_phase(root=sel_rec_root,phase='RECONNECTED_RELAXED',transitions=protocol.reconnect_transitions,
        effects=effects,freq=sel_freq,N=N,seed=reconn_seed,chain_id=chain_id+'_SEL',conda_env=conda_env,
        selection_enabled=False,selection_variance=None,optimum_amplitude=protocol.optimum_amplitude,
        exchange=r37c_exchange_matrix('RECONNECTED_RELAXED',protocol))
    ctl_rec,_,_=_run_phase(root=ctl_rec_root,phase='RECONNECTED_RELAXED',transitions=protocol.reconnect_transitions,
        effects=effects,freq=ctl_freq,N=N,seed=reconn_seed,chain_id=chain_id+'_CTL',conda_env=conda_env,
        selection_enabled=False,selection_variance=None,optimum_amplitude=protocol.optimum_amplitude,
        exchange=r37c_exchange_matrix('RECONNECTED_RELAXED',protocol))

    # Make qfreq paths relative to chain root for portable evidence parsing.
    def relfix(rec,branch,phase_dir):
        rec=dict(rec); rec['qfreq_relpath']=f'{branch}/{phase_dir}/{rec["qfreq_file"]}' if branch else f'{phase_dir}/{rec["qfreq_file"]}'; return rec
    burn=relfix(burn,'','phase_00_COMMON_BURNIN')
    sel_frag=relfix(sel_frag,'selected','phase_01_FRAGMENTED_DIVERGENT_SELECTION')
    ctl_frag=relfix(ctl_frag,'neutral','phase_01_FRAGMENTED_MATCHED_NEUTRAL')
    sel_rec=relfix(sel_rec,'selected','phase_02_RECONNECTED_RELAXED')
    ctl_rec=relfix(ctl_rec,'neutral','phase_02_RECONNECTED_RELAXED')

    summary={
        'schema':'ARCANA_R37C_NEMO_SELECTION_CHAIN_V1','stage':'v0.6D1-R3.7C','chain_id':chain_id,
        'status':'ENGINE_COMPLETED_SELECTION_CHAIN','population_size':N,'replicate':rep,'axis':axis,
        'selection_variance':float(selection_variance),'optimum_amplitude':protocol.optimum_amplitude,
        'genetic_seed':gseed,'loci_per_trait':loci,'common_burnin':burn,
        'selected_branch':{'fragmented':sel_frag,'reconnected':sel_rec},
        'neutral_branch':{'fragmented':ctl_frag,'reconnected':ctl_rec},
        'matched_branch_seed':branch_seed,'matched_reconnection_seed':reconn_seed,
        'phase_boundary_semantics':'QFREQ_FREQUENCY_STATE_CHAIN__LD_AND_GENOTYPE_PHASE_STATE_NOT_PRESERVED',
        'selection_semantics':'GAUSSIAN_PATCH_LOCAL_OPTIMA__RELATIVE_LOCAL_FITNESS',
        'canonical_write_allowed':False,'automatic_calibration_allowed':False,'scalar_K_eff_authorized':False,
    }
    (root/'R3_7C_SELECTION_CHAIN_SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return summary


def main() -> int:
    ap=argparse.ArgumentParser(description='Run R3.7C NEMO 2.4.2 matched directional-selection chains through WSL.')
    ap.add_argument('outdir',type=Path)
    ap.add_argument('--replicates',type=int,default=2)
    ap.add_argument('--population-sizes',type=int,nargs='+',default=[500,2000])
    ap.add_argument('--selection-variances',type=float,nargs='+',default=[1.0,4.0])
    ap.add_argument('--loci-per-trait',type=int,default=64)
    ap.add_argument('--optimum-amplitude',type=float,default=0.6)
    ap.add_argument('--seed',type=int,default=37202026)
    ap.add_argument('--parallel-chains',type=int,default=4)
    ap.add_argument('--conda-env',default='arcana-nemo242')
    args=ap.parse_args()
    if args.replicates<1 or args.loci_per_trait<4 or args.parallel_chains<1 or any(n<20 for n in args.population_sizes):
        raise ValueError('invalid R3.7C suite dimensions')
    protocol=R37CSelectionProtocol(optimum_amplitude=args.optimum_amplitude,selection_variances=tuple(args.selection_variances))
    root=args.outdir.resolve(); root.mkdir(parents=True,exist_ok=True)
    jobs=[(sv,N,r,a) for sv in args.selection_variances for N in args.population_sizes for r in range(args.replicates) for a in (0,1)]
    print(json.dumps({'stage':'v0.6D1-R3.7C','status':'STARTING_NEMO_SELECTION_SUITE','chain_count':len(jobs),'nemo_run_count':len(jobs)*5,'population_sizes':args.population_sizes,'selection_variances':args.selection_variances,'replicates':args.replicates},indent=2))
    records=[]
    with ThreadPoolExecutor(max_workers=args.parallel_chains) as ex:
        fut={ex.submit(_one_chain,N=N,rep=r,axis=a,selection_variance=sv,base_seed=args.seed,loci=args.loci_per_trait,outroot=root,conda_env=args.conda_env,protocol=protocol):(sv,N,r,a) for sv,N,r,a in jobs}
        for f in as_completed(fut):
            sv,N,r,a=fut[f]
            try:
                rec=f.result()
            except Exception as e:
                rec={'stage':'v0.6D1-R3.7C','chain_id':f'N{N}_r{r:03d}_a{a}_sv{sv:g}','population_size':N,'replicate':r,'axis':a,'selection_variance':sv,'status':'ENGINE_FAILED_SELECTION_CHAIN','error':repr(e)}
            records.append(rec); print(f"[R3.7C] {rec['chain_id']} {rec['status']}")
    records.sort(key=lambda x:(float(x['selection_variance']),int(x['population_size']),int(x['replicate']),int(x['axis'])))
    complete=sum(r.get('status')=='ENGINE_COMPLETED_SELECTION_CHAIN' for r in records)
    summary={'schema':'ARCANA_R37C_NEMO_SELECTION_SUITE_V1','stage':'v0.6D1-R3.7C','status':'NEMO_SELECTION_EVIDENCE_COMPLETE_REVIEW_REQUIRED' if complete==len(records) else 'PARTIAL_NEMO_SELECTION_EVIDENCE','chain_count':len(records),'complete_chain_count':complete,'nemo_run_count_expected':len(records)*5,'records':records,'canonical_write_allowed':False,'production_runtime_binding_authorized':False,'scalar_K_eff_authorized':False}
    (root/'R3_7C_NEMO_SELECTION_SUITE_SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ('stage','status','chain_count','complete_chain_count','nemo_run_count_expected')},indent=2))
    return 0 if complete==len(records) else 2

if __name__=='__main__':
    raise SystemExit(main())
