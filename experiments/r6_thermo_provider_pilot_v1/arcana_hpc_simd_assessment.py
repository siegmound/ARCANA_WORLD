#!/usr/bin/env python3
"""Isolated scalar/AVX2/AVX512 potential assessment; never an ASPECT speed claim."""
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import arcana_g44_hpc_campaign as c


def main():
    c.need((c.ROOT/'NATIVE_FOLLOWUP_COMPLETE.json').exists(),'PERFORMANCE_PHASE_MUST_FINISH_FIRST')
    out=c.ROOT/'SIMD_ASSESSMENT';out.mkdir();src=Path(__file__).with_name('hpc_simd_microkernel.cpp')
    # The C++ source is staged separately from the arcana_*.py transport.
    if not src.exists():src=Path(c.read(c.ROOT/'SIMD_SOURCE_LOCATION.json')['path'])
    compiler=Path('/usr/bin/g++').resolve()
    flags={'scalar':['-fno-tree-vectorize','-fno-tree-slp-vectorize','-mno-avx','-mno-avx2','-mno-avx512f'],
       'avx2':['-DENABLE_SIMD','-fopenmp-simd','-mavx2','-mno-avx512f','-mprefer-vector-width=256'],
       'avx512':['-DENABLE_SIMD','-fopenmp-simd','-mavx512f','-mprefer-vector-width=512']}
    build={};base=['-std=c++17','-O3','-march=x86-64','-fno-fast-math','-ffp-contract=off']
    for name,extra in flags.items():
        exe=out/name;cmd=[str(compiler),*base,*extra,str(src),'-o',str(exe)]
        with (out/(name+'_build.stdout')).open('x') as so,(out/(name+'_build.stderr')).open('x') as se:subprocess.run(cmd,stdout=so,stderr=se,check=True)
        dis=subprocess.check_output(['objdump','-d',str(exe)],text=True)
        (out/(name+'_disassembly.txt')).write_text(dis)
        build[name]={'argv':cmd,'binary_sha256':c.sha(exe),'ymm_instruction_lines':len(re.findall(r'^.*%ymm.*$',dis,re.M)),
            'zmm_instruction_lines':len(re.findall(r'^.*%zmm.*$',dis,re.M))}
    rows=[]
    # Rotate order across repetitions; every run is isolated and single-core.
    for rep,order in enumerate((('scalar','avx2','avx512'),('avx512','scalar','avx2'),('avx2','avx512','scalar')),1):
        for name in order:
            case=out/f'{name}_r{rep}';case.mkdir()
            config={'case':str(case),'tag':hashlib.sha256(str(case).encode()).hexdigest(),
               'argv':['/usr/bin/taskset','-c','0',str(out/name)],'environment':{'OMP_NUM_THREADS':'1'},
               'timeout_s':90,'aggregate_pss_abort_bytes':2*1024**3,'host_available_floor_bytes':64*1024**3,'sample_interval_s':.25}
            c.write(case/'config.json',config)
            with (case/'SUPERVISOR.stdout').open('x') as so,(case/'SUPERVISOR.stderr').open('x') as se:
                subprocess.run(['/usr/bin/python3',str(Path(__file__).with_name('arcana_hpc_supervisor.py')),'--run',str(case/'config.json')],stdout=so,stderr=se,check=True)
            execution=c.read(case/'RUN_EXIT.json');c.need(execution['exit_code']==0 and not execution['remaining'],'MICROKERNEL_EXIT')
            result=json.loads((case/'STDOUT.txt').read_text());rows.append({'variant':name,'repeat':rep,'execution':execution,**result})
    c.need(len({x['checksum'] for x in rows})==1,'SIMD_NUMERICAL_PARITY')
    summary={name:{'median_s':statistics.median(x['compute_s'] for x in rows if x['variant']==name),
        'range_s':[min(x['compute_s'] for x in rows if x['variant']==name),max(x['compute_s'] for x in rows if x['variant']==name)]} for name in flags}
    for name in flags:summary[name]['speedup_vs_scalar']=summary['scalar']['median_s']/summary[name]['median_s']
    c.need(build['avx2']['ymm_instruction_lines']>0 and build['avx512']['zmm_instruction_lines']>0,'ISA_NOT_EMITTED')
    c.write(out/'REPORT.json',{'screen_pass':True,'compiler':str(compiler),'compiler_sha256':c.sha(compiler),
       'compiler_version':subprocess.check_output([str(compiler),'--version'],text=True),'source_sha256':c.sha(src),
       'build':build,'runs':rows,'summary':summary,'bitwise_parity':True,'ASPECT_rebuilt':False,'dealII_SIMD_enabled':False,
       'scope':'manufactured independent arithmetic kernel only; no inferred ASPECT or full-mantle speedup',
       'limits':['single-core arithmetic kernel; different memory/operator structure from ASPECT',
          'frequency/thermal differences and kernel selection affect the result',
          'deal.II vectorization width remains zero; qualified rebuild needed for actual application SIMD'],**c.SCOPE})
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
