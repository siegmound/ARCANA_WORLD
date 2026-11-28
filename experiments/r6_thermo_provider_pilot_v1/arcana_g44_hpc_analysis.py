#!/usr/bin/env python3
"""Derive HPC comparisons from retained cases; never overwrite an experiment."""
import csv
import json
from pathlib import Path
import statistics as st
import arcana_g44_hpc_campaign as c


def sample_summary(case, expected):
    maxima = {}; times = []; peak = None
    for line in (case/'PROCESS_SAMPLES.jsonl').open():
        s = json.loads(line); times.append(s['elapsed_s'])
        if peak is None or s['pss_bytes'] > peak['pss_bytes']: peak = s
        for p in s['processes']:
            key = (p['pid'], p['starttime'])
            maxima[key] = max(maxima.get(key, 0.), p['cpu_s'])
    # Under PRoot /proc/exe is the interpreter. Select singleton-affinity tasks
    # at the aggregate PSS peak, preserving the identity ambiguity explicitly.
    ranks = [p for p in peak['processes'] if p['role'] == 'rank'] if peak else []
    inferred = False
    if not ranks and peak:
        ranks = [p for p in peak['processes'] if p['cpu_allowed'].isdigit()
                 and int(p['cpu_allowed']) in expected and p['Pss'] > 32*2**20]
        inferred = True
    pages = {str(i): sum(p['numa_resident_pages'].get(str(i), 0) for p in ranks) for i in range(4)}
    total = sum(pages.values())
    gaps = [b-a for a,b in zip(times,times[1:])]
    return {'cpu_seconds_observed_lower_bound':sum(maxima.values()),
        'sampling_gap_max_s':max(gaps,default=0.),'sampling_gap_median_s':st.median(gaps) if gaps else None,
        'rank_candidates_at_pss_peak':len(ranks),'rank_identity_inferred_from_affinity':inferred,
        'rank_peak_pss_at_aggregate_peak_bytes':max((p['Pss'] for p in ranks),default=None),
        'rank_min_pss_at_aggregate_peak_bytes':min((p['Pss'] for p in ranks),default=None),
        'numa_rank_resident_pages_at_pss_peak':pages,
        'numa_rank_resident_page_fraction':{k:v/total if total else None for k,v in pages.items()},
        'numa_metric_limit':'resident mapping pages, shared pages duplicated; not PSS or proof of NUMA locality'}


def summarize(rows):
    groups = {}
    for row in rows:
        key = (row['backend'],row['transport'],row['level'],row['ranks'],row['layout'])
        groups.setdefault(key,[]).append(row)
    result=[]
    for key, values in sorted(groups.items()):
        b,t,l,n,layout=key; wall=[v['wall_s'] for v in values]
        result.append({'backend':b,'transport':t,'level':l,'ranks':n,'layout':layout,
            'repeats':len(values),'cases':[v['name'] for v in values],
            'cells':values[0]['cells'],'total_dofs':values[0]['total_dofs'],
            'wall_median_s':st.median(wall),'wall_range_s':[min(wall),max(wall)],
            'aspect_median_s':st.median(v['aspect_wall_s'] for v in values),
            'solve_median_s':st.median(v['solve_s'] for v in values),
            'peak_pss_max_GiB':max(v['peak_pss_GiB'] for v in values),
            'peak_rss_max_GiB':max(v['peak_rss_GiB'] for v in values)})
    for row in result:
        same=[x for x in result if all(x[k]==row[k] for k in ('backend','transport','level','layout'))]
        ref=min(same,key=lambda x:x['ranks']);row['reference_ranks']=ref['ranks']
        row['strong_speedup_vs_reference']=ref['wall_median_s']/row['wall_median_s']
        row['parallel_efficiency_vs_reference']=row['strong_speedup_vs_reference']/(row['ranks']/ref['ranks'])
        row['rank_seconds']=row['ranks']*row['wall_median_s']
    return result


def main():
    c.need((c.ROOT/'NATIVE_FOLLOWUP_COMPLETE.json').exists(),'NATIVE_PHASE_INCOMPLETE')
    out=c.ROOT/'ANALYSIS';out.mkdir();rows=[];failures=[];nonperformance=[]
    for path in sorted(c.ROOT.glob('*/CASE_REPORT.json')):
        d=c.read(path)
        if not d.get('screen_pass',False):
            # Replay reports for old native G39/G42 have their own schemas.
            if 'name' in d and ('audit' in d or 'forced' in d):nonperformance.append(path.parent.name)
            else:failures.append({'case':path.parent.name,'error':d.get('error'),'report_sha256':c.sha(path)})
            continue
        if d.get('probe') or 'backend' not in d:continue
        e=d['execution'];row={k:d[k] for k in ('name','backend','transport','layout','level','ranks','cells','total_dofs','aspect_wall_s')}
        row.update({'wall_s':e['wall_s'],'solve_s':d['section_times_s']['Solve Stokes system'],
            'peak_pss_GiB':e['peak_aggregate_pss_observed_bytes']/2**30,
            'peak_rss_GiB':e['peak_aggregate_rss_observed_bytes']/2**30,
            'peak_swap_bytes':e['peak_aggregate_swap_observed_bytes'],
            'errors':d['errors'],'max_relative_error_parity':max((d.get('relative_to_baseline') or {}).values(),default=0.),
            'report_sha256':c.sha(path),
            'sampling':sample_summary(path.parent,c.cpus(d['ranks'],d['layout']))})
        c.need(e['exit_code']==0 and not e['remaining'] and d['time_s']==0 and d['step']==0,'CASE_SCOPE')
        rows.append(row)
    groups=summarize(rows);weak=[]
    for b,t in sorted({(r['backend'],r['transport']) for r in rows}):
        for l,n in ((3,4),(4,8),(5,8)):
            small=next((x for x in groups if (x['backend'],x['transport'],x['level'],x['ranks'],x['layout'])==(b,t,l,n,'spread')),None)
            big=next((x for x in groups if (x['backend'],x['transport'],x['level'],x['ranks'],x['layout'])==(b,t,l+1,n*8,'spread')),None)
            if small and big:
                weak.append({'backend':b,'transport':t,'small_level':l,'small_ranks':n,'large_level':l+1,'large_ranks':n*8,
                    'cells_per_rank_small':small['cells']/n,'cells_per_rank_large':big['cells']/(8*n),
                    'dofs_per_rank_small':small['total_dofs']/n,'dofs_per_rank_large':big['total_dofs']/(8*n),
                    'wall_small_s':small['wall_median_s'],'wall_large_s':big['wall_median_s'],
                    'weak_efficiency':small['wall_median_s']/big['wall_median_s'],
                    'limitation':'equal cells/rank, DOFs/rank differ slightly; only two-point screening, all setup and output included'})
    winners={}
    for level in sorted({r['level'] for r in groups}):
        eligible=[r for r in groups if r['level']==level and r['layout']=='spread']
        winners[str(level)]=min(eligible,key=lambda x:x['wall_median_s'])
    c.write(out/'REPORT.json',{'screen_pass':True,'cases':rows,'groups':groups,'weak_scaling':weak,
        'winners':winners,'preserved_failed_reports':failures,'nonperformance_regressions':nonperformance,
        'method':['end-to-end supervisor wall; ASPECT internal and solve-only clocks reported separately',
            'single measurements are screening; selected finalists have three sequential repetitions',
            'speedup references smallest tested rank for same backend, transport, mesh and placement; L5 reference is 8, not 1',
            'SMT128 is 2 logical CPUs per physical core; 128-rank normalized efficiency is not 128-core efficiency',
            'sampled PSS/RSS, CPU lower bounds and actual sampling gaps; no hardware counter or scheduler exclusivity claim',
            'no conclusion about ARCANA mantle physical validity or AMR based on uniform manufactured meshes'],**c.SCOPE})
    fields=['backend','transport','level','ranks','layout','repeats','wall_median_s','aspect_median_s','solve_median_s',
        'peak_pss_max_GiB','peak_rss_max_GiB','reference_ranks','strong_speedup_vs_reference','parallel_efficiency_vs_reference','rank_seconds']
    with (out/'SCALING.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(groups)
    lines=['| Runtime | MPI | L | Rank | n | Wall mediana s | Intervallo s | PSS max GiB | Speedup | Efficienza |',
        '|---|---|---:|---:|---:|---:|---|---:|---:|---:|']
    for r in groups:
        lines.append(f'| {r["backend"]}/{r["layout"]} | {r["transport"]} | {r["level"]} | {r["ranks"]} | {r["repeats"]} | {r["wall_median_s"]:.3f} | {r["wall_range_s"][0]:.3f}–{r["wall_range_s"][1]:.3f} | {r["peak_pss_max_GiB"]:.2f} | {r["strong_speedup_vs_reference"]:.2f} | {r["parallel_efficiency_vs_reference"]:.3f} |')
    (out/'TABLE.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'performance_cases':len(rows),'preserved_failures':failures,'winners':winners},indent=2))


if __name__=='__main__':main()
