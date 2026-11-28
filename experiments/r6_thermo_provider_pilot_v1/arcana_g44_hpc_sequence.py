#!/usr/bin/env python3
"""Sequential, gated synthetic scaling. No concurrent performance samples."""
import json
from pathlib import Path
import arcana_g44_hpc_campaign as c

def main():
    root=c.ROOT
    with (root/'SEQUENCE.log').open('a') as log:
        def case(name,n,l,**kw):
            original=root/name
            if original.exists():
                report=original/'CASE_REPORT.json'
                if report.exists() and c.read(report)['screen_pass']:
                    return c.read(report)
                name=name+'_retry2'
            log.write(json.dumps({'start':name,'ranks':n,'level':l})+'\n');log.flush()
            row=c.execute(name,n,l,**kw)
            log.write(json.dumps({'complete':name,'aspect_s':row.get('aspect_wall_s'),'wall_s':row['execution']['wall_s']})+'\n');log.flush()
            return row
        c.need(c.read(root/'TCP_P2_POSTPROCESS_RECOVERY.json')['screen_pass'],'TWO_RANK_REQUIRED')
        case('tcp_probe_p4',4,2,probe=True,timeout=45)
        b2=c.read(c.EV/'R6_G38_ASPECT_HOLLOW_SPHERE_NEW01/level_2/CASE_REPORT.json')
        case('tcp_aspect_l2_p4',4,2,baseline=b2,timeout=120)
        c.write(root/'G44R3_RECOVERY_GATE.json',{'screen_pass':True,'ranks':[2,4],'historical_failures_preserved':True,**c.SCOPE})
        b3=None
        for n in (1,2,4,8):
            row=case(f'tcp_l3_p{n}_spread_r1',n,3,baseline=b3)
            if b3 is None:
                c.need(all(row['errors'][k]<b2['errors'][k] for k in c.g38.LABELS),'L3_REFINEMENT')
                b3=row
        b4=None;rows4=[]
        for n in (1,2,4,8,16,32,64):
            row=case(f'tcp_l4_p{n}_spread_r1',n,4,baseline=b4,timeout=360)
            if b4 is None:
                c.need(all(row['errors'][k]<b3['errors'][k] for k in c.g38.LABELS),'L4_REFINEMENT')
                b4=row
            rows4.append(row)
        b5=None;rows5=[]
        for n in (8,16,32,64):
            row=case(f'tcp_l5_p{n}_spread_r1',n,5,baseline=b5,timeout=480)
            if b5 is None:
                c.need(all(row['errors'][k]<b4['errors'][k] for k in c.g38.LABELS),'L5_REFINEMENT')
                b5=row
            rows5.append(row)
        # SMT comparison on the same representative mesh, never oversubscription.
        case('tcp_l5_p128_spread_r1',128,5,baseline=b5,timeout=480)
        case('tcp_l4_p16_compact_r1',16,4,layout='compact',baseline=b4,timeout=360)
        # Select finalists separately by mesh from measured end-to-end time.
        for l,rows,baseline in ((4,rows4,b4),(5,rows5,b5)):
            finalists=sorted(rows,key=lambda x:x['execution']['wall_s'])[:2]
            for row in finalists:
                for rep in (2,3):case(f'tcp_l{l}_p{row["ranks"]}_spread_r{rep}',row['ranks'],l,baseline=baseline,timeout=480)
        p64=rows5[-1]
        projection={'level5_rank64_pss_peak':p64['execution']['peak_aggregate_pss_observed_bytes'],
             'level6_pss_projection_bytes':8*p64['execution']['peak_aggregate_pss_observed_bytes'],
             'level6_wall_projection_s':8*p64['execution']['wall_s'],
             'method':'conservative screening extrapolation x8, not a guaranteed peak or scaling prediction',
             'start_allowed':8*p64['execution']['peak_aggregate_pss_observed_bytes']<60*1024**3 and 8*p64['execution']['wall_s']<480}
        c.write(root/'LEVEL6_RESOURCE_GATE.json',projection)
        if projection['start_allowed']:
            first=case('tcp_l6_p32_spread_r1',32,6,timeout=600)
            c.need(all(first['errors'][k]<b5['errors'][k] for k in c.g38.LABELS),'L6_REFINEMENT')
            case('tcp_l6_p64_spread_r1',64,6,baseline=first,timeout=600)
        c.write(root/'TCP_SCALING_COMPLETE.json',{'screen_pass':True,'level6_executed':projection['start_allowed'],**c.SCOPE})
if __name__=='__main__':main()
