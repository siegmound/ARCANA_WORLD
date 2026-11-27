#!/usr/bin/env python3
"""Read-only handoff, benchmark and provider inventory; no engine execution."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import zipfile


def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def write(p,obj):
    with p.open('x') as f: json.dump(obj,f,indent=2,sort_keys=True); f.write('\n')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',type=Path,required=True); ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args(); base=args.base.resolve(); ev=base/'ARCANA_WORLD_EVIDENCE/R6'; out=args.output.resolve()
    if out.exists(): raise RuntimeError('OUTPUT_EXISTS')
    out.mkdir(); checks=[]; availability={}
    for name in ('20261026T213828Z_case1a_ref3_fixed','20261026T224533Z_case1a_ref4'):
        root=ev/'GEODYN_1F_BLANKENBACH'/name
        # Discover actual manifests: level 3 has no OUTPUT_MANIFEST_SHA256.txt.
        lists=sorted(root.glob('*SHA256*.txt'))
        availability[name]=[p.name for p in lists]
        for p in lists:
            for line in p.read_text().splitlines():
                match=re.fullmatch(r'([0-9a-f]{64})\s+\*?(.+)',line)
                if not match: raise RuntimeError('HASH_LINE:'+str(p))
                pin,ref=match.groups(); target=Path(ref)
                if not target.is_absolute(): target=root/target
                actual=sha(target)
                checks.append({'manifest':str(p),'path':str(target),'expected':pin,
                               'actual':actual,'pass':actual==pin})
    write(out/'BLANKENBACH_HISTORICAL_REHASH.json',{'comparisons':checks,'available_hash_lists':availability,
        'screen_pass':bool(checks and all(c['pass'] for c in checks)),'new_benchmark_runs':0,
        'scope':'existing hash list membership only; no blanket hash inventory inferred for level 3'})
    package=base/'ARCANA_CODEX_HANDOFF_G36R2_PACKAGE.zip'
    with zipfile.ZipFile(package) as z:
        entries=[]
        for n in z.namelist():
            data=z.read(n)
            entries.append({'name':n,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    write(out/'HANDOFF_PACKAGE.json',{'zip_sha256':sha(package),'files':entries,'entries_read':len(entries)})
    src=base/'ARCANA_WORLD_R6_C11A_VERIFY.a7voPe'
    paths=['R6_GEODYNAMIC_LAW_AUTHORITY_MATRIX.json','R6_GEODYNAMIC_LAW_AUTHORITY_MATRIX.md',
        'experiments/first_physical_geodynamics_v1/audit.py',
        'src/arcana_worldsim/r6/adapters/aspect_snapshot_reader.py','src/arcana_worldsim/r6/geodyn3c_qualification.py',
        'src/arcana_worldsim/r6/state.py','src/arcana_worldsim/r6/store.py',
        'src/arcana_worldsim/r6/experimental_trajectory_archive.py',
        'experiments/r6_thermo_provider_pilot_v1/m01_mantle_experimental_design_candidate_v1.json',
        'R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json','R6_PRE_ORBDATA_TRANSIENT_THERMAL_COUPLING.json',
        'external/ShellSet-v1.1.0/src/MOD_ArcanaRuntime.f90']
    write(out/'FROZEN_AUTHORITIES.json',{n:sha(src/n) for n in paths})
    hs=base/'ARCANA_ASPECT_TOOLS/udocker-state/containers/arcana-aspect-v310/ROOT/home/dealii/aspect/benchmarks/hollow_sphere'
    write(out/'HOLLOW_SPHERE_SOURCE_INVENTORY.json',{
        'source_commit':'30eb77ee5da186137d436dbad35c6cb3cab64b69',
        'files':{str(p.relative_to(hs)):sha(p) for p in sorted(hs.rglob('*')) if p.is_file()},
        'proposed_not_executed':True,
        'boundary_conditions':'analytic prescribed velocity at both boundaries; NOT a free-slip/nullspace qualification',
        'solver_tolerance_upstream':1e-6,'end_time_s':0,'dimension':3,'radii':[.5,1.]})
    write(out/'MANIFEST.json',{'files':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()},
                             'runner_sha256':sha(Path(__file__))})
    ok=all(c['pass'] for c in checks)
    print('HANDOFF_FILES',len(entries),'HISTORICAL_BENCHMARK_CHECKS',len(checks),'PASS',ok)
    return 0 if ok else 2
if __name__=='__main__': raise SystemExit(main())
