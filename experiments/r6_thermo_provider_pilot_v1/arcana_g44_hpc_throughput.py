#!/usr/bin/env python3
"""Separate two-job throughput experiment; never part of strong scaling."""
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time
import arcana_g44_hpc_campaign as c


def main():
    c.need((c.ROOT/'FINAL_FOLLOWUP_COMPLETE.json').exists(),'SINGLE_JOB_CAMPAIGN_INCOMPLETE')
    out=c.ROOT/'THROUGHPUT_NEW01';out.mkdir();mapping=c.cpus(64,'spread');runs=[]
    c.need(not set(mapping[:32])&set(mapping[32:]),'OVERLAPPING_CORES')
    for repeat in range(1,4):
        jobs=[];start=time.monotonic()
        for label,ids in (('A',mapping[:32]),('B',mapping[32:])):
            name=f'THROUGHPUT_NEW01/batch_r{repeat}_{label}'
            script=('import arcana_g44_hpc_campaign as c; '
                "b=c.read(c.ROOT/'native_vader_l5_p8_r1/CASE_REPORT.json'); "
                f"c.execute({name!r},32,5,profile='vader',backend='native',baseline=b,timeout=480,cpu_ids={ids!r})")
            stdout=(out/f'launch_r{repeat}_{label}.stdout').open('x');stderr=(out/f'launch_r{repeat}_{label}.stderr').open('x')
            jobs.append((name,subprocess.Popen([sys.executable,'-u','-c',script],stdout=stdout,stderr=stderr),stdout,stderr))
        exits=[]
        for name,job,stdout,stderr in jobs:
            exits.append(job.wait());stdout.close();stderr.close()
        elapsed=time.monotonic()-start
        c.need(exits==[0,0],'THROUGHPUT_CHILD_FAILED')
        cases=[c.read(c.ROOT/name/'CASE_REPORT.json') for name,_,_,_ in jobs]
        c.need(all(x['screen_pass'] and not x['execution']['remaining'] for x in cases),'THROUGHPUT_CASE_FAILED')
        runs.append({'repeat':repeat,'batch_wall_s_including_two_preflights':elapsed,'jobs_per_s':2/elapsed,
            'cases':[x['name'] for x in cases],'case_wall_s':[x['execution']['wall_s'] for x in cases],
            'sum_of_individual_sampled_pss_peaks_GiB':sum(x['execution']['peak_aggregate_pss_observed_bytes'] for x in cases)/2**30})
    analysis=c.read(c.ROOT/'ANALYSIS/REPORT.json');references={}
    for n in (32,64):
        ref=next(x for x in analysis['groups'] if (x['backend'],x['transport'],x['level'],x['ranks'],x['layout'])==('native','vader',5,n,'spread'))
        references[str(n)]={'single_job_median_s':ref['wall_median_s'],'serial_jobs_per_s':1/ref['wall_median_s']}
    med=statistics.median(x['batch_wall_s_including_two_preflights'] for x in runs)
    c.write(out/'REPORT.json',{'screen_pass':True,'scope':'three separate pairs of independent identical synthetic jobs; 64 physical cores total',
        'cpu_mapping':{'A':mapping[:32],'B':mapping[32:]},'runs':runs,'median_batch_s':med,
        'range_batch_s':[min(x['batch_wall_s_including_two_preflights'] for x in runs),max(x['batch_wall_s_including_two_preflights'] for x in runs)],
        'median_jobs_per_s':2/med,'serial_references':references,
        'throughput_vs_serial_32':2*references['32']['single_job_median_s']/med,
        'throughput_vs_serial_64':2*references['64']['single_job_median_s']/med,
        'limitations':['includes subprocess/preflight cost absent from single-job clock; conservative comparison',
            'memory field sums individual sampled peaks, not simultaneous observed aggregate or hard limit',
            'one synthetic mesh/workload and current node load; no inferred throughput for ARCANA history'],**c.SCOPE})
    print(json.dumps(c.read(out/'REPORT.json'),indent=2))


if __name__=='__main__':main()
