#!/usr/bin/env python3
"""Finalize the synthetic FAIR HPC evidence, preserving every earlier failure."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import arcana_g44_hpc_campaign as c
import arcana_native_runtime_candidate as native


def extra_metrics(case):
    maxima={}; cpu={}; io={}; user={}; system={}; threads={}
    samples=case/'PROCESS_SAMPLES.jsonl'
    if not samples.exists():return None
    for line in samples.open():
        for p in json.loads(line)['processes']:
            k=(p['pid'],p['starttime']);cpu[k]=max(cpu.get(k,0),p['cpu_s'])
            io[k]=max(io.get(k,0),p['write_bytes'])
            if p['Pss']>maxima.get(k,{}).get('Pss',-1):maxima[k]=p
            if 'cpu_user_s' in p:
                user[k]=max(user.get(k,0),p['cpu_user_s']);system[k]=max(system.get(k,0),p['cpu_system_s'])
                threads[k]=max(threads.get(k,0),p['threads'])
    return {'cpu_seconds_observed_lower_bound':sum(cpu.values()),'write_bytes_observed_lower_bound':sum(io.values()),
        'per_process':[{'pid':k[0],'starttime':k[1],'role':v['role'],'cpu_allowed_at_pss_peak':v['cpu_allowed'],
            'peak_pss_bytes':v['Pss'],'cpu_seconds_observed_lower_bound':cpu[k],
            'user_seconds_observed_lower_bound':user.get(k),'system_seconds_observed_lower_bound':system.get(k),
            'max_threads_observed':threads.get(k)} for k,v in maxima.items()],
        'limit':'sampled cumulative counters; short-lived processes and last CPU/I/O increments may be missed; not scheduler accounting'}


def final_guards():
    c.source_check();_,container,root,*_=c.runtime()
    metadata=c.ar.tree_metadata(container);before=c.read(c.ROOT/'CONTAINER_METADATA_BEFORE.json')
    changed=[k for k in set(before)|set(metadata) if before.get(k)!=metadata.get(k)]
    c.need(not changed,'HISTORICAL_RUNTIME_METADATA_CHANGED:'+str(changed[:10]))
    parents=[]
    extra=(('R6_G39_ASPECT_FREE_SLIP_NEW01','07ba543a44e841fb5d0397cef86154c3eed818a3473160cb8d529068d4d1399b'),
        ('R6_G41_NATIVE_QUADRATURE_NEW01','a7c95cf40aebf36f037d92b8553058e1f4916eaee53929d2d4c6df71bd11b9e6'),
        ('R6_G42_CONSISTENT_BOUNDARY_FLUX_NEW01','f50077b527e8cabe8b4f294a07ec1221bbf6168a91809bb5607074d4bcf8494f'))
    for folder,pin in (*c.PINNED,*extra):
        m=c.g38.verified_bundle(c.EV/folder,pin);parents.append({'path':folder,'manifest_sha256':pin,'members':len(m['files'])})
    identities=c.read(c.ROOT/'NATIVE_FINAL_BINARY_IDENTITY.json')
    for name,row in identities.items():
        source=root/('home/dealii/aspect/bin/aspect-release' if name=='aspect-release' else 'usr/bin/'+name)
        c.need(c.sha(source)==row['historical_sha256'] and c.sha(c.ROOT/'native_candidate2/bin'/name)==row['private_sha256'],'FINAL_BINARY_IDENTITY')
    live=[];cases=[];observed=set()
    for p in sorted(c.ROOT.rglob('RUN_EXIT.json')):
        d=c.read(p);c.need(not d['remaining'],'CASE_LEFTOVERS:'+str(p))
        cases.append({'case':str(p.parent.relative_to(c.ROOT)),'exit_code':d['exit_code'],'launcher_exit_code':d['launcher_exit_code']})
        for x in d.get('per_process_peak_pss_samples',{}).values():observed.add((x['pid'],x['starttime']))
    failed_cleanup=[]
    for p in sorted(c.ROOT.rglob('SUPERVISOR_FAILURE.json')):
        d=c.read(p);c.need('cleanup' in d and not d['cleanup']['remaining'],'FAILED_SUPERVISOR_LEFTOVERS')
        failed_cleanup.append(str(p.relative_to(c.ROOT)))
    for p in c.ROOT.rglob('PROCESS_SAMPLES.jsonl'):
        for line in p.open():
            for x in json.loads(line)['processes']:observed.add((x['pid'],x['starttime']))
    for pid,start in observed:
        try:
            raw=Path('/proc',str(pid),'stat').read_text();v=raw[raw.rfind(')')+2:].split()
            if int(v[19])==start and v[0] not in ('Z','X'):live.append({'pid':pid,'starttime':start})
        except (FileNotFoundError,ProcessLookupError):pass
    c.need(not live,'OBSERVED_JOB_STILL_LIVE')
    return {'screen_pass':True,'frozen_source_sha':c.g25.SOURCE,'frozen_source_clean':True,
        'historical_container_metadata_equal':True,'historical_metadata_entries':len(metadata),
        'parents':parents,'private_binary_identities_unchanged':True,
        'execution_cases':cases,'observed_process_identities_checked':len(observed),'observed_live_remaining':live,
        'failed_supervisor_cleanup_reports_checked':failed_cleanup,
        'process_scope':'per-job exact-token descendant scans and observed PID/starttime recheck, not a claim about unrelated node jobs',
        'R2_output_exists':(c.EV/'R6_G44R2_TCP_MPI_RECOVERY_NEW01').exists(),**c.SCOPE}


def reproduce_private_runtime():
    out=c.ROOT/'native_reproducibility_NEW01'
    identity=native.prepare(c.BASE,out)
    c.need(all(x['text_exact'] for x in identity['binary_identity'].values()),'REPRODUCED_ELF_TEXT')
    case=c.ROOT/'native_reproducibility_version';case.mkdir()
    conf={'case':str(case),'tag':hashlib.sha256(str(case).encode()).hexdigest(),
        'argv':['/usr/bin/env','LD_LIBRARY_PATH='+str(out/'lib'),str(out/'bin/aspect-release'),'--version'],
        'environment':{'OPAL_PREFIX':str(out),'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'},
        'timeout_s':60,'aggregate_pss_abort_bytes':4*2**30,'host_available_floor_bytes':64*2**30,'sample_interval_s':.25}
    c.write(case/'config.json',conf)
    with (case/'SUPERVISOR.stdout').open('x') as so,(case/'SUPERVISOR.stderr').open('x') as se:
        done=subprocess.run(['/usr/bin/python3',str(Path(__file__).with_name('arcana_hpc_supervisor.py')),'--run',str(case/'config.json')],stdout=so,stderr=se)
    d=c.read(case/'RUN_EXIT.json');text=(case/'STDOUT.txt').read_text()
    c.need(done.returncode==0 and d['exit_code']==0 and not d['remaining'] and '30eb77ee5' in text,'REPRODUCED_NATIVE_VERSION')
    c.write(c.ROOT/'NATIVE_REPRODUCIBILITY_REPORT.json',{'screen_pass':True,'builder_sha256':c.sha(Path(native.__file__)),
        'private_output':str(out),'all_8_text_sections_identical':True,'version_exit_code':0,
        'scope':'reproduction of private deployment and version probe; application benchmark uses native_candidate2',**c.SCOPE})


def prepare():
    for name in ('NATIVE_FOLLOWUP_COMPLETE.json','FINAL_FOLLOWUP_COMPLETE.json','THROUGHPUT_NEW01/REPORT.json','SIMD_ASSESSMENT/REPORT.json'):
        c.need(c.read(c.ROOT/name)['screen_pass'],'MISSING_FINAL_GATE:'+name)
    reproduce_private_runtime()
    metrics={};details={}
    for p in sorted(c.ROOT.rglob('RUN_EXIT.json')):
        name=str(p.parent.relative_to(c.ROOT));metrics[name]=extra_metrics(p.parent)
        report=p.parent/'CASE_REPORT.json'
        if report.exists():
            d=c.read(report)
            if 'errors' in d:
                details[name]={k:d.get(k) for k in ('ranks','level','cells','total_dofs','dof_components','errors','relative_to_baseline',
                    'stokes_iterations','nonlinear_residuals','section_times_s','rank_affinity','statistics')}
    c.write(c.ROOT/'CPU_IO_AND_RANK_METRICS.json',metrics);c.write(c.ROOT/'NUMERICAL_DETAILS.json',details)
    guards=final_guards();c.write(c.ROOT/'FINAL_GUARDS.json',guards);c.write(c.ROOT/'HARDWARE_AFTER.json',c.g44.host())
    analysis=c.read(c.ROOT/'ANALYSIS/REPORT.json');simd=c.read(c.ROOT/'SIMD_ASSESSMENT/REPORT.json');throughput=c.read(c.ROOT/'THROUGHPUT_NEW01/REPORT.json')
    code=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    report={'status':'PASS_SYNTHETIC_HPC_QUALIFICATION_ONLY','screen_pass':True,'source_sha':c.g25.SOURCE,
        'closure_code_commit':code,'scientific_scope':'upstream dimensionless HollowSphere at t=0, prescribed analytic boundary velocities, viscosity r^4; no ARCANA mantle state',
        'passed_performance_cases':len(analysis['cases']),'preserved_failed_case_reports':analysis['preserved_failed_reports'],
        'winners':analysis['winners'],'scaling':analysis['groups'],'weak_scaling':analysis['weak_scaling'],
        'SIMD_microkernel_summary':simd['summary'],'SIMD_bitwise_parity':simd['bitwise_parity'],
        'throughput':{k:v for k,v in throughput.items() if k not in c.SCOPE},
        'guard_report_sha256':c.sha(c.ROOT/'FINAL_GUARDS.json'),
        'capabilities':{'MPI_ranks_2_4_8_16_32_64':True,'SMT_128_tested':True,'mesh_levels':[2,3,4,5,6],
            'native_same_code_deployment':True,'G39_and_G41_G42_replayed_rank1':True,'dealII_SIMD_width_bits':0,
            'application_SIMD_build_qualified':False,'AMR_qualified':False,'MPI_CBF_qualified':False,'GPU_qualified':False},
        'limitations':['current shared-node load; no exclusive scheduler reservation or independent site-policy attestation',
            'sampled PSS/RSS and CPU/I/O lower bounds; configured interval .25s plus scan cost, actual intervals retained in analysis',
            'memory abort is a sampled threshold, not a kernel-enforced aggregate cap; no per-rank enforced cap',
            'level6 and SMT screening, selected L4/L5 finalists repeated; no extrapolation to 210Ma',
            'native means private ELF relocation with same application text and historical dependencies, not an optimized recompile',
            'AVX2/AVX512 arithmetic microkernel is not an ASPECT SIMD benchmark',
            'NUMA resident mapping pages include shared file pages; no controlled first-touch or memory-binding claim',
            'per-process user/system split available in final supervisor runs; older runs retain combined CPU observations'],**c.SCOPE}
    c.write(c.ROOT/'REPORT.json',report)
    print(json.dumps({'prepared':True,'closure_code_commit':code,'performance_cases':len(analysis['cases'])}))


def seal():
    report=c.read(c.ROOT/'REPORT.json');c.need(report['screen_pass'],'FINAL_REPORT')
    # Same complete regular-file inventory as g25.inventory, caching aliases to
    # avoid re-reading the historical libraries through each private symlink.
    files={};cache={};links={}
    for p in sorted(c.ROOT.rglob('*')):
        if p==c.ROOT/'MANIFEST.json':continue
        rel=str(p.relative_to(c.ROOT))
        if p.is_symlink():links[rel]=os.readlink(p)
        if not p.is_file():continue
        s=p.stat();key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
        if key not in cache:cache[key]=c.sha(p)
        files[rel]=cache[key]
    c.write(c.ROOT/'MANIFEST.json',{'status':report['status'],'source_sha':c.g25.SOURCE,
        'report_sha256':c.sha(c.ROOT/'REPORT.json'),'files':files,'symlink_targets':links,
        'inventory_contract':'g25.inventory complete regular-file SHA256 mapping; root manifest excluded; no symlink-directory traversal',**c.SCOPE})
    print(json.dumps({'manifest_sha256':c.sha(c.ROOT/'MANIFEST.json'),'members':len(files),'status':report['status']}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','seal']);args=p.parse_args()
    (prepare if args.action=='prepare' else seal)()
