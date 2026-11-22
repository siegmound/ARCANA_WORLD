"""Run fast original Perple_X upstream MEEMUM test, pinning source and output.

Needs local v7.3.3 *source* checkout and separately installed v7.3.3
Linux executable. This does not compare its chemistry to MAGEMin.
"""
from __future__ import annotations
import argparse
import json
import math
import hashlib
import tarfile
import shutil
import subprocess
import time
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1.pilot import (
    PilotError, need, verify_perplex_source, parse_perplex_meemum, digest, pins
)

FILES=('bl691_MEEMUM.dat','bl691_MEEMUM_input.txt','hp62ver.dat','solution_model.dat')


def run(repo_root,source,executable,work,*,release_archive,timeout_s=150):
    root=Path(repo_root).resolve()
    work=Path(work).resolve()
    need(not work.is_relative_to(root) and not work.exists(),
         'PILOT_PERPLEX_OUTPUT_NOT_WRITE_ONCE_EXTERNAL')
    expected_release = pins()['providers']['Perple_X']['linux_release_sha256']
    need(Path(release_archive).is_file() and digest(release_archive)==expected_release,
         'PILOT_PERPLEX_RELEASE_ARCHIVE_SHA_MISMATCH')
    source=verify_perplex_source(source)
    exe=Path(executable).resolve()
    need(exe.exists() and exe.is_file(), 'PILOT_PERPLEX_MEEMUM_EXECUTABLE_MISSING')
    # Independently prove installed executable bytes are from the pinned
    # SHA256 release archive, not merely a similarly named local binary.
    try:
        with tarfile.open(release_archive,'r:gz') as archive:
            candidates=[item for item in archive.getmembers()
                        if item.isfile() and Path(item.name).name=='meemum']
            need(len(candidates)==1,'PILOT_PERPLEX_ARCHIVE_BINARY_AMBIGUOUS')
            stream=archive.extractfile(candidates[0])
            need(stream is not None,'PILOT_PERPLEX_ARCHIVE_BINARY_MISSING')
            embedded_sha=hashlib.sha256(stream.read()).hexdigest()
    except (tarfile.TarError,OSError) as exc:
        raise PilotError('PILOT_PERPLEX_RELEASE_ARCHIVE_INVALID') from exc
    need(digest(exe)==embedded_sha,'PILOT_PERPLEX_BINARY_NOT_FROM_PINNED_RELEASE')
    need(5<=timeout_s<=600,'PILOT_PERPLEX_TIMEOUT_INVALID')
    orig=source/'test/bl691_MEEMUM'
    expected=parse_perplex_meemum(orig/'output/bl691_MEEMUM.prn')
    work.mkdir(parents=True,exist_ok=False)
    for filename in FILES:
        shutil.copyfile(orig/filename,work/filename)
    start=time.monotonic()
    command=[str(exe)]
    try:
        with (work/'bl691_MEEMUM_input.txt').open('rb') as stdin:
            p=subprocess.run(command,stdin=stdin,stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,cwd=work,timeout=timeout_s,check=False)
    except subprocess.TimeoutExpired as e:
        raise PilotError('PILOT_PERPLEX_RUN_TIMEOUT') from e
    duration=time.monotonic()-start
    (work/'RUN_STDOUT.log').write_bytes(p.stdout)
    need(p.returncode==0,'PILOT_PERPLEX_NONZERO_EXIT')
    report=work/'bl691_MEEMUM.prn'
    need(report.exists(),'PILOT_PERPLEX_NO_PRN')
    computed=parse_perplex_meemum(report)
    need(math.isclose(expected['temperature_k'],computed['temperature_k'],abs_tol=.1)
         and math.isclose(expected['pressure_bar'],computed['pressure_bar'],abs_tol=.1),
         'PILOT_PERPLEX_P_T_REFERENCE_MISMATCH')
    # Numeric system: require same phase set and wt.% within 0.2 pp (after
    # upstream's own reference rounding), not numerical bit-for-bit equality.
    e,c=expected['phases_wt_percent'],computed['phases_wt_percent']
    need(set(e)==set(c),'PILOT_PERPLEX_REFERENCE_PHASE_ASSEMBLAGE_DIFFERENT')
    need(all(abs(e[k]-c[k])<=max(.2,.02*e[k]) for k in e),
         'PILOT_PERPLEX_REFERENCE_PHASE_FRACTIONS_DIFFERENT')
    result={'status':'PERPLEX_ORIGINAL_MEEMUM_REFERENCE_NUMERICAL_PASS',
        'provider':'Perple_X', 'version':'v7.3.3',
        'tag_commit_sha':pins()['providers']['Perple_X']['commit_sha'],
        'source_reference_report_sha256':digest(orig/'output/bl691_MEEMUM.prn'),
        'meemum_binary_sha256':digest(exe),
        'release_archive_sha256':expected_release,
        'input_sha256':{name:digest(work/name) for name in FILES},
        'output_prn_sha256':digest(report), 'stdout_sha256':digest(work/'RUN_STDOUT.log'),
        'elapsed_s':duration, 'official_T_K':computed['temperature_k'],
        'official_P_bar':computed['pressure_bar'],
        'phase_wt_percent':computed['phases_wt_percent'],
        'cross_provider_equivalence':False,
        'original_ARCANA_phases_assigned':0,
        'mechanical_solve_authorized':False,'physical_T1':None,'D_024':'ACTIVE',
        'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False}
    (work/'REPORT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'phase_count':len(c),
                      'cross_provider_equivalence':False,'physical_T1':None}))
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo-root',required=True,type=Path)
    ap.add_argument('--perplex-source',required=True,type=Path)
    ap.add_argument('--meemum',required=True,type=Path)
    ap.add_argument('--release-archive',required=True,type=Path)
    ap.add_argument('--output',required=True,type=Path)
    args=ap.parse_args()
    run(args.repo_root,args.perplex_source,args.meemum,args.output,release_archive=args.release_archive)

if __name__=='__main__':main()
