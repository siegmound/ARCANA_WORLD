#!/usr/bin/env python3
"""After TCP scaling, qualify shared-memory and private native deployment.
Independent failures stop only their dependent branch; no physical ARCANA solve.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import numpy as np
import arcana_g44_hpc_campaign as c
import arcana_g39_aspect_free_slip as g39
import arcana_g42_consistent_boundary_flux as g42
import arcana_native_runtime_candidate as native


def command_case(name,args,timeout=120,inputs=None):
    case=c.ROOT/name;case.mkdir();(case/'output').mkdir();(case/'tmp').mkdir()
    if inputs:
        for p in inputs:shutil.copy2(p,case/p.name)
    private=c.ROOT/'native_candidate2';root=c.runtime()[2]
    env={'OPAL_PREFIX':str(private),'OMPI_MCA_mca_base_component_path':str(root/'usr/lib/x86_64-linux-gnu/openmpi/lib/openmpi3'),
         'OMPI_MCA_pml':'ob1','OMPI_MCA_btl':'self,tcp','OMPI_MCA_btl_tcp_if_include':'lo','OMPI_MCA_oob_tcp_if_include':'lo',
         'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','HWLOC_HIDE_ERRORS':'2',
         'PATH':str(private/'bin')+':/usr/bin:/bin','TMPDIR':str(case/'tmp')}
    config={'case':str(case),'tag':hashlib.sha256(str(case).encode()).hexdigest(),
        'argv':['/usr/bin/taskset','-c','0','/usr/bin/env','LD_LIBRARY_PATH='+str(private/'lib'),*args],
        'environment':env,'timeout_s':timeout,'aggregate_pss_abort_bytes':80*1024**3,
        'host_available_floor_bytes':max(64*1024**3,int(c.read(c.ROOT/'HARDWARE_BEFORE.json')['memavailable_bytes']*.25)),
        'sample_interval_s':.25}
    c.write(case/'config.json',config)
    with (case/'SUPERVISOR.stdout').open('x') as so,(case/'SUPERVISOR.stderr').open('x') as se:
        done=subprocess.run(['/usr/bin/python3',str(Path(__file__).with_name('arcana_hpc_supervisor.py')),'--run',str(case/'config.json')],stdout=so,stderr=se)
    c.need(done.returncode==0 and c.read(case/'RUN_EXIT.json')['exit_code']==0,'NATIVE_COMMAND:'+name)
    return case


def native_regressions():
    private=c.ROOT/'native_candidate2';mpi=private/'bin/orterun';aspect=private/'bin/aspect-release'
    p39=c.EV/'R6_G39_ASPECT_FREE_SLIP_NEW01';p41=c.EV/'R6_G41_NATIVE_QUADRATURE_NEW01';p42=c.EV/'R6_G42_CONSISTENT_BOUNDARY_FLUX_NEW01'
    pins=['07ba543a44e841fb5d0397cef86154c3eed818a3473160cb8d529068d4d1399b',
          'a7c95cf40aebf36f037d92b8553058e1f4916eaee53929d2d4c6df71bd11b9e6',
          'f50077b527e8cabe8b4f294a07ec1221bbf6168a91809bb5607074d4bcf8494f']
    for p,pin in zip((p39,p41,p42),pins):c.g38.verified_bundle(p,pin)
    rows=[]
    for spec in g39.CASES:
        name,level,forced,gauge,datum=spec;old=p39/name
        case=command_case('native_g39_'+name,[str(mpi),'-np','1','--bind-to','none',str(aspect),'input.prm'],inputs=[old/'input.prm'])
        stats=g39.parse_stats(case/'output/statistics');text=(case/'STDOUT.txt').read_text()
        residuals=re.findall(r'Relative nonlinear residual \(Stokes system\) after nonlinear iteration \d+:\s*([0-9.eE+-]+)',text)
        row={'name':name,'level':level,'forced':forced,'gauge':gauge,'datum_Pa':datum,'native_exit':0,
             'last_nonlinear_residual':float(residuals[-1]) if residuals else None,'residual_markers':len(residuals),**stats}
        oldrow=c.read(old/'CASE_REPORT.json')
        c.need(all(np.isclose(stats[k],oldrow[k],rtol=1e-6,atol=1e-10) for k in g39.COLS),'NATIVE_G39_REPLAY:'+name)
        c.need(c.sha(case/'input.prm')==c.sha(old/'input.prm'),'REGRESSION_INPUT')
        c.write(case/'CASE_REPORT.json',row);rows.append(row)
    result=g39.evaluate(rows);c.need(result['screen_pass'],'NATIVE_G39_CHECKS');c.write(c.ROOT/'NATIVE_G39_REPLAY.json',result)
    rows42=[]
    for name in ('hydro_3','forced_volume_2','forced_volume_3','forced_datum_3'):
        old=p42/name;inputs=[old/'input.prm',*old.glob('*.so')]
        case=command_case('native_g42_'+name,[str(mpi),'-np','1','--bind-to','none',str(aspect),'input.prm'],inputs=inputs)
        stats=g39.parse_stats(case/'output/statistics');reference=c.read(p41/name/'CASE_REPORT.json')
        c.need(stats['cells']==reference['native']['cells'] and all(abs(stats[k]-reference['native'][k])/max(abs(reference['native'][k]),1e-10)<1e-6 for k in ('rms','pmean','dissipation')),'NATIVE_G41_REPLAY')
        audit=g42.audit(np.loadtxt(case/'output/G42_DOFS.dat',ndmin=2),np.loadtxt(case/'output/G42_FACES.dat',ndmin=2),reference)
        c.need(audit['screen_pass'],'NATIVE_G42_CBF')
        row={'name':name,'native':stats,'audit':audit,'plugin_recompiled':False,'same_binary_and_dependency_ABI':True}
        c.write(case/'CASE_REPORT.json',row);rows42.append(row)
    c.write(c.ROOT/'NATIVE_G42_REPLAY.json',{'screen_pass':True,'cases':rows42,'rank_scope':1,'AMR_and_MPI_CBF_qualified':False,**c.SCOPE})


def main():
    while not (c.ROOT/'TCP_SCALING_COMPLETE.json').exists():
        driver=c.ROOT/'DRIVER_R5.exitcode'
        if driver.exists() and int(driver.read_text())!=0:raise RuntimeError('TCP_SCALING_BLOCKED')
        time.sleep(2)
    print('TCP_SCALING_COMPLETE: starting sequential follow-up',flush=True)
    private=c.ROOT/'native_candidate2';root=c.runtime()[2]
    # Reconfirm application code identity for every relocated executable.
    checks={}
    for name in ('aspect-release','orterun','orted','ompi_info','bash','taskset','grep','cut'):
        source=root/('home/dealii/aspect/bin/aspect-release' if name=='aspect-release' else 'usr/bin/'+name)
        checks[name]={'historical_sha256':c.sha(source),'private_sha256':c.sha(private/'bin'/name),
              'text_exact':native.text_sha(source)==native.text_sha(private/'bin'/name)}
    c.need(all(v['text_exact'] for v in checks.values()),'PRIVATE_TEXT_IDENTITY')
    c.write(c.ROOT/'NATIVE_FINAL_BINARY_IDENTITY.json',checks)
    info=command_case('vader_mca_inventory',[str(private/'bin/ompi_info'),'--param','btl','vader','--level','9'])
    txt=(info/'STDOUT.txt').read_text()
    c.need('btl_vader_single_copy_mechanism' in txt and 'none' in txt,'VADER_OPTION_AUTHORITY')
    b2=c.read(c.EV/'R6_G38_ASPECT_HOLLOW_SPHERE_NEW01/level_2/CASE_REPORT.json')
    vader=False
    try:
        for n in (2,4):c.execute('vader_probe_p'+str(n),n,2,profile='vader',probe=True,timeout=45)
        for n in (2,4):c.execute('vader_aspect_l2_p'+str(n),n,2,profile='vader',baseline=b2,timeout=120)
        vader=True
    except Exception as error:
        c.write(c.ROOT/'VADER_PROFILE_BLOCKED.json',{'error':repr(error),'dependent_scaling_stopped':True,**c.SCOPE})
        failed=[p for p in c.ROOT.glob('vader_*/CASE_REPORT.json') if not c.read(p)['screen_pass']]
        for report in failed:
            run=report.parent/'RUN_EXIT.json'
            c.need(run.exists() and not c.read(run)['remaining'],'UNSAFE_CLEANUP_FAILURE')
            c.need('NUMERICAL_PARITY' not in c.read(report).get('error',''),'NUMERICAL_FAILURE_STOPS_SCALING')
    native_rows=[]
    try:
        for n in (1,2,4):native_rows.append(c.execute('native_tcp_l2_p'+str(n),n,2,baseline=b2,backend='native',timeout=120))
        b3=c.read(c.EV/'R6_G38_ASPECT_HOLLOW_SPHERE_NEW01/level_3/CASE_REPORT.json')
        for n in (1,4):c.execute('native_tcp_l3_p'+str(n),n,3,baseline=b3,backend='native')
        native_regressions()
        c.write(c.ROOT/'NATIVE_CORRECTNESS_GATE.json',{'screen_pass':True,'G38_levels':[2,3],'G39_rank1':True,'G41_G42_rank1':True,**c.SCOPE})
    except Exception as error:
        c.write(c.ROOT/'NATIVE_CORRECTNESS_BLOCKED.json',{'error':repr(error),'performance_stopped':True,**c.SCOPE});return
    # Same-mesh parity references; no old G38 timing is used as a speed baseline.
    baselines={l:c.read(c.ROOT/f'tcp_l{l}_p{1 if l==4 else 8}_spread_r1'/ 'CASE_REPORT.json') for l in (4,5)}
    # The level-4 singleton may have been retried after a monitor failure.
    if not baselines[4]['screen_pass']:baselines[4]=c.read(c.ROOT/'tcp_l4_p1_spread_r1_retry2/CASE_REPORT.json')
    candidates={}
    for profile in (('tcp','vader') if vader else ('tcp',)):
        for l,ranks in ((4,(1,2,4,8,16,32,64)),(5,(8,16,32,64,128))):
            rows=[]
            for n in ranks:rows.append(c.execute(f'native_{profile}_l{l}_p{n}_r1',n,l,profile=profile,baseline=baselines[l],backend='native',timeout=480))
            candidates[(profile,l)]=rows
    # NUMA placement at fixed rank and mesh, independent of SMT comparison.
    for profile in (('tcp','vader') if vader else ('tcp',)):
        c.execute(f'native_{profile}_l4_p16_compact_r1',16,4,profile=profile,layout='compact',baseline=baselines[4],backend='native')
    for l in (4,5):
        rows=[row for (profile,level),values in candidates.items() if level==l for row in values]
        for row in sorted(rows,key=lambda x:x['execution']['wall_s'])[:2]:
            for rep in (2,3):c.execute(f'native_{row["transport"]}_l{l}_p{row["ranks"]}_r{rep}',row['ranks'],l,profile=row['transport'],baseline=baselines[l],backend='native',timeout=480)
    # A measured level-5 projection, explicit full-HPC authorization and D-025
    # warning allow evaluating a larger *synthetic* mesh on the native candidate.
    p64=c.read(c.ROOT/'tcp_l5_p64_spread_r1/CASE_REPORT.json')
    projected=8*p64['execution']['peak_aggregate_pss_observed_bytes']
    host=c.g44.host();available=host['memavailable_bytes'];budget=170*1024**3
    allowed=projected<.85*budget and available>2*budget and (host['cgroup_finite_memory_headroom_bytes'] is None or host['cgroup_finite_memory_headroom_bytes']>2*budget)
    c.write(c.ROOT/'NATIVE_LEVEL6_RESOURCE_GATE.json',{'level5_observed_pss_bytes':p64['execution']['peak_aggregate_pss_observed_bytes'],
        'level6_screening_projection_bytes':projected,'sampled_pss_abort_budget_bytes':budget,'host_available_bytes':available,
        'host_reserve_fraction':.25,'start_allowed':allowed,'D025_over_100GB_notice_provided':True,
        'scope':'synthetic native level6 only; projection is not a guaranteed peak',**c.SCOPE})
    if allowed:
        first=c.execute('native_tcp_l6_p32_r1',32,6,backend='native',timeout=900,pss_budget_gib=170)
        c.need(all(first['errors'][k]<baselines[5]['errors'][k] for k in c.g38.LABELS),'L6_REFINEMENT')
        c.execute('native_tcp_l6_p64_r1',64,6,baseline=first,backend='native',timeout=900,pss_budget_gib=170)
    c.write(c.ROOT/'NATIVE_FOLLOWUP_COMPLETE.json',{'screen_pass':True,'vader_profile_qualified':vader,'application_rebuild':False,'SIMD_enabled':False,**c.SCOPE})
if __name__=='__main__':main()
