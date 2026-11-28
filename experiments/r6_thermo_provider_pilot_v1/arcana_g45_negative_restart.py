#!/usr/bin/env python3
"""Real production-gate negatives and honest native restart scope."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import numpy as np
import arcana_g45_distributed_amr_cbf as c
sys.path.insert(0,str(c.CODE));import audit


def source_restart_gate():
    out=c.ROOT/'restart_source_audit';out.mkdir();src=c.old.runtime()[3];rows=[]
    for name in ('source/time_stepping/interface.cc','source/simulator/core.cc','source/simulator/helper_functions.cc','source/simulator/checkpoint_restart.cc'):
        raw=(src/name).read_bytes();c.need(raw==subprocess.check_output(['git','-C',str(src),'show',c.old.ar.ASPECT_SHA+':'+name]),'RESTART_SOURCE_DRIFT')
        p=out/Path(name).name;p.write_bytes(raw);rows.append({'upstream_path':name,'sha256':c.sha(p)})
    code=(src/'source/time_stepping/interface.cc').read_text();core=(src/'source/simulator/core.cc').read_text()
    c.need('AssertThrow (new_time_step > 0' in code and core.index('advance_time(new_time_step_size);')<core.index('const bool checkpoint_written = maybe_write_checkpoint'),'RESTART_ORDER_UNPROVEN')
    c.write(c.ROOT/'RESTART_SOURCE_AUDIT.json',{'status':'BLOCKED_NATIVE_POSITIVE_STEP_REQUIRED_BEFORE_CHECKPOINT','same_rank_restart':'BLOCKED','rank_change_restart':'UNQUALIFIED',
        'source_bindings':rows,'positive_checkpoint_attempts':0,'reason':'standard run loop requires positive step, calls advance_time before maybe_write_checkpoint; no positive synthetic time authorized by frozen G45 contract; static exports never counted as restart',**c.SCOPE})


def overlay(base,dest):
    dest.mkdir();(dest/'output').mkdir();shutil.copy2(base/'CASE_SPEC.json',dest/'CASE_SPEC.json')
    for p in (base/'output').glob('G45_s0_r*'):
        q=dest/'output'/p.name;q.symlink_to(os.path.relpath(p,q.parent))
    c.write(dest/'BASE_REFERENCE.json',{'case':str(base),'audited_source':'G45R1_AUDIT_REPORT.json','audited_sha256':c.sha(base/'G45R1_AUDIT_REPORT.json'),
        'layout':'unmodified shards referenced inside same evidence bundle; each mutation atomically replaces local link, never writes through it'})


def replace(path,text):
    temp=path.with_name(path.name+'.replacement');temp.write_text(text);temp.replace(path)

def mutate_numeric(path,columns,operation):
    keys,values=audit.keyed(path,columns);keys,values=operation(keys,values)
    replace(path,''.join(k+' '+' '.join(format(float(v),'.17e') for v in row)+'\n' for k,row in zip(keys,values)))


def main():
    p=argparse.ArgumentParser();p.add_argument('--plugin',type=Path,required=True);a=p.parse_args();c.check();source_restart_gate()
    baseline=c.ROOT/'G45R1_forced_l2_a1_p4_unremoved_NEW01';c.need(c.read(baseline/'G45R1_AUDIT_REPORT.json')['screen_pass'] and c.native_convergence(baseline)['screen_pass'],'NEGATIVE_BASELINE_NOT_QUALIFIED')
    out=c.ROOT/'NEGATIVE_TESTS_NEW01';out.mkdir();results=[]
    for kind in ('inverted_orientation','duplicate_face','dropped_face','wrong_sign','omitted_constraint','stale_ghost'):
        case=out/kind;overlay(baseline,case);face=next((case/'output').glob('*_FACES.dat'))
        if kind=='inverted_orientation':
            def op(k,v):v[0,7:10]*=-1;return k,v
            mutate_numeric(face,37,op)
        elif kind=='duplicate_face':
            def op(k,v):return k+[k[0]],np.vstack((v,v[0]))
            mutate_numeric(face,37,op)
        elif kind=='dropped_face':
            def op(k,v):return k[9:],v[9:]
            mutate_numeric(face,37,op)
        elif kind=='wrong_sign':
            for q in (case/'output').glob('*_DOFS.dat'):
                d=audit.numeric(q,17);d[:,12:14]*=-1;replace(q,'\n'.join(' '.join(format(v,'.17e') for v in row) for row in d)+'\n')
            for q in (case/'output').glob('*_FACES.dat'):
                def op(k,v):v[:,22:25]*=-1;return k,v
                mutate_numeric(q,37,op)
        elif kind=='omitted_constraint':
            for q in (case/'output').glob('*_H.dat'):
                if q.stat().st_size:
                    d=audit.numeric(q,3);slave=d[0,0];d=d[d[:,0]!=slave];replace(q,'\n'.join(' '.join(format(v,'.17e') for v in row) for row in d)+'\n');break
        else:
            for q in (case/'output').glob('*_GHOSTS.dat'):
                if q.stat().st_size:
                    d=audit.numeric(q,4);d[0,2]+=1.;replace(q,'\n'.join(' '.join(format(v,'.17e') for v in row) for row in d)+'\n');break
        try:
            report,_=audit.evaluate(case);audit.enforce(report);rejected=False;error=None
        except audit.Rejected as e:rejected=True;error=str(e)
        row={'negative':kind,'expected_rejection':True,'production_gate_rejected':rejected,'error':error};c.write(case/'NEGATIVE_REPORT.json',row);results.append(row);c.need(rejected,'NEGATIVE_FALSE_ACCEPT:'+kind);print('NEGATIVE_REJECTED',kind,error,flush=True)
    # Gauge negative goes through the same projected-datum production gate.
    base=c.ROOT/'G45R1_forced_l2_a1_p4_unremoved_NEW01';shifted=c.ROOT/'G45R1_datum_l2_a1_p4_unremoved_NEW01';c.need(c.read(shifted/'G45R1_AUDIT_REPORT.json')['screen_pass'],'DATUM_BASELINE')
    positive=audit.datum(base,shifted);case=out/'wrong_datum';overlay(shifted,case)
    for q in (case/'output').glob('*_FACES.dat'):
        def op(k,v):v[:,22:25]+=20*v[:,7:10];return k,v
        mutate_numeric(q,37,op)
    try:audit.datum(base,case);rejected=False;error=None
    except audit.Rejected as e:rejected=True;error=str(e)
    row={'negative':'wrong_datum','expected_rejection':True,'production_gate_rejected':rejected,'error':error,'positive_control':positive};c.write(case/'NEGATIVE_REPORT.json',row);results.append(row);c.need(rejected,'NEGATIVE_DATUM_FALSE_ACCEPT')
    case=out/'tampered_parent';case.mkdir();parent=c.EV/'R6_G44_HPC_FULL_MANTLE_20261128_NEW01';m=c.read(parent/'MANIFEST.json');m['tampered_for_negative']=True;c.write(case/'MANIFEST.json',m)
    try:c.old.g38.verified_bundle(case,'8ef9676aa03875ea09452286e82edb20f755ab785f7a4f6d2b11d746a0322422');rejected=False;error=None
    except RuntimeError as e:rejected=True;error=str(e)
    row={'negative':'tampered_parent','production_gate_rejected':rejected,'error':error};c.write(case/'NEGATIVE_REPORT.json',row);results.append(row);c.need(rejected,'NEGATIVE_PARENT_FALSE_ACCEPT')
    spec=next(s for s in c.read(c.CODE/'contract.json')['cases'] if s['name']=='forced_l2_a0_p1');row=c.case(spec,'negative_invalid_restart_NEW01',a.plugin,extra_prm='\nset Resume computation = true\n')
    text=(c.ROOT/'negative_invalid_restart_NEW01/STDERR.txt').read_text();rejected=row['execution']['exit_code']!=0 and not row['execution']['remaining'] and 'no matching written checkpoint has been found' in text
    results.append({'negative':'invalid_native_restart','production_gate_rejected':rejected,'native_exit':row['execution']['exit_code'],'rejection':'ASPECT actual missing-checkpoint rejection'});c.need(rejected,'INVALID_NATIVE_RESTART_NOT_REJECTED')
    c.write(out/'REPORT.json',{'screen_pass':True,'tests':results,'scope':'mutated retained raw shards through same production auditor; parent uses original verifier, restart uses actual ASPECT',**c.SCOPE})
    gate=c.read(c.ROOT/'RESTART_SOURCE_AUDIT.json');gate.update(invalid_restart_negative_pass=True,same_rank_restart='BLOCKED_NO_AUTHORIZED_NATIVE_T0_CHECKPOINT',rank_change_restart='UNQUALIFIED');c.write(c.ROOT/'RESTART_GATE.json',gate)
    print('NEGATIVE_GATES_PASS',len(results),flush=True)
if __name__=='__main__':main()
