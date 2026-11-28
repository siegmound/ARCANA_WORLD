#!/usr/bin/env python3
"""Replay one retained synthetic case into a fresh root; parent stays immutable.
This is not full cross-rank, rotational-gauge or restart qualification.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys
import traceback
import arcana_g45_distributed_amr_cbf as c


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent',type=Path,required=True);p.add_argument('--manifest-sha256',required=True);p.add_argument('--case',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    parent=a.parent.resolve();out=a.output.resolve();c.need(re.fullmatch(r'[a-f0-9]{64}',a.manifest_sha256) and re.fullmatch(r'[A-Za-z0-9_]+',a.case),'REPLAY_ARGUMENTS')
    c.need(out.parent==c.EV.resolve() and out.name.startswith('R6_G45_REPLAY_') and not out.exists(),'FRESH_REPLAY_ROOT_REQUIRED')
    manifest=c.old.g38.verified_bundle(parent,a.manifest_sha256);c.need(all(manifest.get(k)==v for k,v in c.SCOPE.items()),'PARENT_NOT_G45_SYNTHETIC_SCOPE')
    source=parent/a.case;spec=c.read(source/'CASE_SPEC.json');c.need(spec in c.read(c.CODE/'contract.json')['cases'],'CASE_NOT_FROZEN')
    prm=(source/'input.prm').read_text();c.need(re.search(r'(?m)^set End time\s*=\s*0\s*$',prm) and 'no Advection, iterated Stokes' in prm,'REPLAY_MUST_REMAIN_SYNTHETIC_STATIC')
    c.old.source_check();out.mkdir();(out/'output').mkdir();copied={}
    for item in [source/'input.prm',source/'rank.sh',source/'CASE_SPEC.json',*source.glob('*.so')]:
        shutil.copy2(item,out/item.name);copied[item.name]=c.sha(item)
    if (source/'CASE_VARIANT.json').exists():shutil.copy2(source/'CASE_VARIANT.json',out/'CASE_VARIANT.json')
    cfg=c.read(source/'config.json');argv=[x.replace(str(source),str(out)) for x in cfg['argv']];env={k:v.replace(str(source),str(out)) for k,v in cfg['environment'].items()}
    c.ROOT=parent # supervised helper reads protected hardware; writes only out.
    c.write(out/'REPLAY_PROVENANCE.json',{'parent':str(parent),'manifest_sha256':a.manifest_sha256,'case':a.case,'input_files':copied,'replayer_sha256':c.sha(Path(__file__)),'scope':'single retained synthetic case only; no full provider/rotation/restart qualification'})
    report={'screen_pass':False,'status':'G45_REPLAY_BLOCKED',**c.SCOPE}
    try:
        execution=c.supervise(out,argv,env,cfg['timeout_s']);report['execution']=execution
        c.need(execution['exit_code']==0,'NATIVE_EXIT');convergence=c.native_convergence(out);report['native_convergence']=convergence;c.need(convergence['screen_pass'],'NATIVE_NONLINEAR_CONVERGENCE')
        sys.path.insert(0,str(c.CODE));import audit
        numerical,fields=audit.evaluate(out);report['numerical']=numerical;audit.enforce(numerical)
        c.write(out/'STABLE_FIELDS.json',fields);report.update(screen_pass=True,status='G45_SINGLE_CASE_REPLAY_PASS_ONLY')
    except Exception as error:report.update(error=repr(error),traceback=traceback.format_exc())
    c.old.source_check();c.old.g38.verified_bundle(parent,a.manifest_sha256)
    c.write(out/'REPORT.json',report);c.write(out/'MANIFEST.json',{'status':report['status'],'files':c.old.g25.inventory(out),'source_sha':c.old.g25.SOURCE,**c.SCOPE})
    print(json.dumps({'status':report['status'],'manifest_sha256':c.sha(out/'MANIFEST.json')}));return 0 if report['screen_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
